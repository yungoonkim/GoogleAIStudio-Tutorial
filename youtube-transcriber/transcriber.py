import os
import warnings

# AFC 권고 경고 숨김
warnings.filterwarnings("ignore")

from google import genai
from google.genai import types


def transcribe_audio_file(
    audio_path: str,
    mime_type: str = "audio/mp4",
    model: str = "gemini-3.5-transcribe",
) -> dict:
    """
    오디오 파일을 Gemini API를 통해 전사(STT)합니다.
    대용량 오디오도 안정적으로 처리할 수 있도록 client.files.upload 방식을 사용합니다.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY 환경 변수가 설정되어 있지 않습니다.")

    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"오디오 파일을 찾을 수 없습니다: {audio_path}")

    client = genai.Client(api_key=api_key)

    # 1. Gemini Files API를 통해 오디오 파일 업로드 (대용량 안전)
    uploaded_file = client.files.upload(
        file=audio_path,
        config=types.UploadFileConfig(mime_type=mime_type),
    )

    try:
        # 2. 전사 모델 설정
        # gemini-3.5-transcribe 모델용 전사 설정
        config = types.GenerateContentConfig(
            audio_transcription_config=types.AudioTranscriptionConfig(
                word_timestamp=True,
                diarization=True,
            ),
        )

        try:
            response = client.models.generate_content(
                model=model,
                contents=[uploaded_file],
                config=config,
            )
            raw_text = response.text.strip() if response.text else ""
        except Exception as e:
            # gemini-3.5-transcribe 실패 시 gemini-3.6-flash 로 자동 Fallback
            print(f"[{model}] 전사 오류 발생, gemini-3.6-flash로 대체 시도: {e}")
            fallback_model = "gemini-3.6-flash"
            fallback_prompt = (
                "이 오디오 파일의 모든 발화 내용을 한국어(또는 원본 언어)로 정확하게 받아적어주세요(전사/STT). "
                "추가 코멘트나 부가 설명 없이 대화/발화 텍스트만 시간의 흐름대로 출력해주세요."
            )
            response = client.models.generate_content(
                model=fallback_model,
                contents=[uploaded_file, fallback_prompt],
            )
            raw_text = response.text.strip() if response.text else ""

        return {
            "success": True,
            "text": raw_text,
            "char_count": len(raw_text),
            "word_count": len(raw_text.split()),
        }

    finally:
        # 3. 업로드된 임시 파일 정리 (자원 누수 방지)
        try:
            client.files.delete(name=uploaded_file.name)
        except Exception:
            pass
