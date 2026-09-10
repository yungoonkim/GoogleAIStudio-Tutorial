import os
import warnings

# AFC 권고 경고 숨김
warnings.filterwarnings("ignore")

from google import genai
from google.genai import types


def transcribe_audio_file(
    audio_path: str,
    mime_type: str = "audio/mp4",
    model: str = "gemini-3.6-flash",
) -> dict:
    """
    오디오 파일을 Gemini API를 통해 한국어 트랜스크립트와 영어 발화 전용 트랜스크립트로 각각 추출합니다.
    동일한 업로드 파일에 대해 2가지 관점의 전사를 병렬/연속 수행합니다.
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
        # 2-1. 한국어 및 원본 전체 트랜스크립트 추출
        korean_prompt = (
            "이 오디오 파일의 모든 발화 내용을 한국어(또는 영상의 원본 언어)로 정확하게 받아적어주세요(전사/STT). "
            "추가 코멘트나 부가 설명 없이 대화/발화 텍스트만 시간의 흐름대로 출력해주세요."
        )
        res_korean = client.models.generate_content(
            model=model,
            contents=[uploaded_file, korean_prompt],
        )
        korean_text = res_korean.text.strip() if res_korean.text else ""

        # 2-2. 영어로 된 음성만 선별 추출하는 트랜스크립트
        english_prompt = (
            "이 오디오 파일을 정밀하게 분석하여, 음성 중에서 [영어로 발화된 부분]만 모두 찾아내어 시간 순서대로 모아서 정리해주세요.\n"
            "- 한국어 발화는 제외하고, 실제로 영어로 말한 문장, 표현, 단어 발화만 그대로 받아적어주세요.\n"
            "- 만약 영상 전체가 영어라면 영어 전체를 정확하게 전사해주세요.\n"
            "- 만약 영상 내에 영어 발화가 전혀 없다면 '(영상 내에 영어 발화가 감지되지 않았습니다.)'라고만 출력하세요.\n"
            "- 부가적인 인사말이나 추가 코멘트는 제외하고 발화 내용만 출력하세요."
        )
        res_english = client.models.generate_content(
            model=model,
            contents=[uploaded_file, english_prompt],
        )
        english_text = res_english.text.strip() if res_english.text else ""

        return {
            "success": True,
            # 기본 텍스트 (하위 호환)
            "text": korean_text,
            "char_count": len(korean_text),
            "word_count": len(korean_text.split()),
            # 한국어 트랜스크립트
            "korean": {
                "text": korean_text,
                "char_count": len(korean_text),
                "word_count": len(korean_text.split()),
            },
            # 영어 발화 전용 트랜스크립트
            "english": {
                "text": english_text,
                "char_count": len(english_text),
                "word_count": len(english_text.split()),
            },
        }

    finally:
        # 3. 업로드된 임시 파일 정리 (자원 누수 방지)
        try:
            client.files.delete(name=uploaded_file.name)
        except Exception:
            pass
