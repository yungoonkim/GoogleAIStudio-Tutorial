# To run this code you need to install the following dependencies:
# pip install google-genai

import io
import os
import sys
import warnings

# Windows 콘솔 한글 깨짐 방지
if isinstance(sys.stdout, io.TextIOWrapper) and sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 경고 메시지 억제
warnings.filterwarnings("ignore")

from google import genai
from google.genai import types


def generate(audio_file_path: str = "gemini_4_news_briefing.wav"):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY 환경 변수가 설정되어 있지 않습니다.")
        return

    if not os.path.exists(audio_file_path):
        print(f"❌ 오디오 파일을 찾을 수 없습니다: {audio_file_path}")
        return

    client = genai.Client(api_key=api_key)

    # 1. 오디오 파일 읽기
    with open(audio_file_path, "rb") as f:
        audio_bytes = f.read()

    model = "gemini-3.5-transcribe"

    # 2. 오디오 바이트 데이터를 입력 parts에 추가
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_bytes(
                    data=audio_bytes,
                    mime_type="audio/wav",
                ),
            ],
        ),
    ]

    generate_content_config = types.GenerateContentConfig(
        audio_transcription_config=types.AudioTranscriptionConfig(
            word_timestamp=True,
            diarization=True,
        ),
    )

    print(f"🎤 '{audio_file_path}' 전사(STT) 진행 중 ({model})...\n")
    print("-" * 50)

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if text := chunk.text:
            print(text, end="", flush=True)

    print("\n" + "-" * 50)
    print("✅ 전사 완료!")


if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else "gemini_4_news_briefing.wav"
    generate(target_file)


