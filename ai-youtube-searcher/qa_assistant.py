import json
import os
import re
import warnings

warnings.filterwarnings("ignore")

from google import genai
from google.genai import types


def ask_video_qa(
    query: str,
    segments: list[dict],
    video_title: str = "",
    model: str = "gemini-3.8-flash",
) -> dict:
    """
    영상 트랜스크립트와 타임스탬프 정보를 바탕으로 gemini-3.8-flash 모델을 사용하여 질문에 답변합니다.
    답변 내에서 관련 시간대를 감지하여 자동 영상 점프를 지원합니다.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY 환경 변수가 설정되어 있지 않습니다.")

    client = genai.Client(api_key=api_key)

    # 1. 트랜스크립트 포맷팅
    context_lines = []
    for s in segments:
        context_lines.append(f"[{s.get('time', '00:00')}] {s.get('text', '')}")
    transcript_context = "\n".join(context_lines)

    system_instruction = (
        "당신은 유튜브 영상의 내용을 정확하게 파악하여 사용자의 질문에 답해주는 친절한 AI 어시스턴트입니다.\n"
        "제공된 영상의 타임스탬프별 트랜스크립트를 바탕으로 질문에 정확하고 구체적으로 답변하세요.\n"
        "규칙:\n"
        "1. 관련된 내용이 영상의 몇 분 몇 초에 나오는지 반드시 [MM:SS] 형식의 타임스탬프를 언급하세요.\n"
        "2. 사용자가 특정 장면이나 대사의 위치를 물어보면 해당 시간대를 명확히 알려주세요.\n"
        "3. 한국어로 자연스럽고 정중하게 답변하세요.\n"
    )

    user_prompt = f"""[영상 제목]: {video_title}

[영상 타임스탬프 트랜스크립트]:
{transcript_context}

[사용자 질문]:
{query}
"""

    try:
        response = client.models.generate_content(
            model=model,
            contents=[user_prompt],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
            ),
        )
        answer_text = response.text.strip() if response.text else "답변을 생성할 수 없습니다."
    except Exception as e:
        print(f"[{model}] 호출 실패, gemini-3.6-flash 로 대체 질의응답 진행: {e}")
        fallback_model = "gemini-3.6-flash"
        response = client.models.generate_content(
            model=fallback_model,
            contents=[user_prompt],
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.7,
            ),
        )
        answer_text = response.text.strip() if response.text else "답변을 생성할 수 없습니다."

    # 답변에서 가장 먼저 등장하는 [MM:SS] 타임스탬프 추출 (자동 점프용)
    jump_sec = None
    jump_time = None
    match = re.search(r'\[?(\d{1,2}):(\d{2})\]?', answer_text)
    if match:
        mins, secs = int(match.group(1)), int(match.group(2))
        jump_sec = mins * 60 + secs
        jump_time = f"{mins:02d}:{secs:02d}"

    return {
        "answer": answer_text,
        "jump_sec": jump_sec,
        "jump_time": jump_time,
    }


def search_transcript(query: str, segments: list[dict]) -> list[dict]:
    """
    단순 키워드 검색을 통해 일치하는 타임스탬프 목록을 빠르게 필터링합니다.
    """
    query_lower = query.lower().strip()
    if not query_lower:
        return []

    matched = []
    for s in segments:
        text = s.get("text", "")
        if query_lower in text.lower():
            matched.append(s)
    return matched
