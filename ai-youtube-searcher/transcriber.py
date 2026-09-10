import json
import os
import re
import time
import warnings

warnings.filterwarnings("ignore")

from google import genai
from google.genai import types


def seconds_to_timestamp(seconds: int) -> str:
    """초를 MM:SS 형식으로 변환합니다."""
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def parse_timestamp_response(raw_text: str) -> list[dict]:
    """Gemini 응답에서 타임스탬프 세그먼트 리스트를 안전하게 추출합니다."""
    cleaned_segments = []

    # 1. 마크다운 코드블록 제거
    text_clean = re.sub(r'```(?:json)?', '', raw_text).strip()

    # 2. JSON 배열 매칭 시도
    match = re.search(r'\[\s*\{.*\}\s*\]', text_clean, re.DOTALL)
    if match:
        try:
            items = json.loads(match.group(0))
            if isinstance(items, list):
                for item in items:
                    raw_start = item.get("start", item.get("start_sec", item.get("timestamp_sec", 0)))
                    try:
                        start_sec = int(raw_start)
                        # 밀리초(ms) 단위로 넘어왔을 경우(예: 3000) 초(3)로 변환
                        if start_sec > 1000:
                            start_sec = start_sec // 1000
                    except (ValueError, TypeError):
                        start_sec = 0

                    time_str = item.get("time", item.get("timestamp", ""))
                    if not time_str or ":" not in str(time_str):
                        time_str = seconds_to_timestamp(start_sec)

                    text_val = item.get("text", item.get("content", "")).strip()
                    if text_val:
                        cleaned_segments.append({
                            "start": start_sec,
                            "time": time_str,
                            "text": text_val,
                        })
                if cleaned_segments:
                    return cleaned_segments
        except Exception as e:
            print(f"JSON 파싱 실패, 텍스트 파싱 진행: {e}")

    # 3. 줄단위 정규식 파싱 시도 (예: [00:15] 대사...)
    lines = raw_text.splitlines()
    line_pattern = re.compile(r'\[?(\d{1,2}):(\d{2})\]?\s*(.*)')
    for line in lines:
        line = line.strip()
        m = line_pattern.match(line)
        if m:
            mins, secs, line_text = m.groups()
            total_sec = int(mins) * 60 + int(secs)
            time_str = f"{int(mins):02d}:{int(secs):02d}"
            line_text = line_text.strip()
            if line_text:
                cleaned_segments.append({
                    "start": total_sec,
                    "time": time_str,
                    "text": line_text,
                })

    # 4. 세그먼트가 여전히 비어있을 경우 문장 단위 분리 및 타임스탬프 부여
    if not cleaned_segments and raw_text.strip():
        # 마침표, 물음표, 느낌표 또는 줄바꿈으로 분리
        sentences = [s.strip() for s in re.split(r'[\n.!?]+', raw_text) if len(s.strip()) > 1]
        for idx, s in enumerate(sentences):
            cleaned_segments.append({
                "start": idx * 3,
                "time": seconds_to_timestamp(idx * 3),
                "text": s,
            })

    return cleaned_segments


def transcribe_audio_with_timestamps(
    audio_path: str,
    mime_type: str = "audio/webm",
    model: str = "gemini-3.6-flash",
) -> list[dict]:
    """
    Gemini 멀티모달 모델을 사용하여 오디오의 시작 시간대(초 단위)와 발화 대사를 정밀하게 전사합니다.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY 환경 변수가 설정되어 있지 않습니다.")

    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"오디오 파일을 찾을 수 없습니다: {audio_path}")

    client = genai.Client(api_key=api_key)

    # 1. Gemini Files API에 업로드
    uploaded_file = client.files.upload(
        file=audio_path,
        config=types.UploadFileConfig(mime_type=mime_type),
    )

    prompt = (
        "이 오디오 파일의 모든 발화 내용을 듣고, 발화가 시작되는 정확한 시작 시간(초 단위)과 함께 문장 단위로 전사(STT)해주세요.\n"
        "반드시 다른 설명 없이 아래 JSON 배열 형식으로만 응답하세요:\n"
        "[\n"
        '  {"start": 0, "time": "00:00", "text": "한국어 또는 영어 발화 문장"},\n'
        '  {"start": 5, "time": "00:05", "text": "다음 발화 문장"}\n'
        "]\n"
        "- start: 발화 시작 시간 (초 단위 정수, 예: 0, 5, 12, 65)\n"
        "- time: MM:SS 형식 문자열 (예: 00:00, 00:05, 01:05)\n"
        "- text: 해당 시점에 발화된 대사\n"
    )

    try:
        response = None
        # 지수 백오프 재시도 (최대 3회)
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=[uploaded_file, prompt],
                )
                break
            except Exception as e:
                if attempt < 2 and "429" in str(e):
                    print(f"Gemini API 429 감지, {attempt + 1}회차 재시도 대기 중...")
                    time.sleep(2 * (attempt + 1))
                else:
                    raise e

        # 응답 텍스트 추출
        raw_text = ""
        if response:
            if response.text:
                raw_text = response.text.strip()
            # 만약 non-text part (audio_transcription)가 있을 경우 텍스트 복구
            elif response.candidates and response.candidates[0].content:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, "audio_transcription") and part.audio_transcription:
                        raw_text = getattr(part.audio_transcription, "text", "")
                    elif hasattr(part, "text") and part.text:
                        raw_text = part.text

        segments = parse_timestamp_response(raw_text)
        return segments

    finally:
        try:
            client.files.delete(name=uploaded_file.name)
        except Exception:
            pass
