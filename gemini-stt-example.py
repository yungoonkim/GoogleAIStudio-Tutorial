import glob
import io
import os
import sys
import warnings

# Windows 콘솔 한글 깨짐 방지 (타입 체커 호환)
if isinstance(sys.stdout, io.TextIOWrapper) and sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 경고 메시지 억제
warnings.filterwarnings("ignore")

from google import genai
from google.genai import types


def get_available_wav_files(directory: str = ".") -> list[str]:
    """현재 디렉터리에서 .wav 파일 목록을 최근 수정된 순서대로 정렬하여 반환합니다."""
    wav_files = glob.glob(os.path.join(directory, "*.wav"))
    # 최근 수정된 순으로 정렬
    wav_files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
    return [os.path.basename(f) for f in wav_files]


def transcribe_audio_file(
    audio_path: str,
    output_txt_path: str | None = None,
    model: str = "gemini-3.6-flash",
) -> str:
    """단일 오디오 파일을 Gemini 모델로 전사(STT)하여 .txt 파일로 저장합니다."""
    if not os.path.exists(audio_path):
        print(f"❌ 파일을 찾을 수 없습니다: {audio_path}")
        return ""

    if output_txt_path is None:
        output_txt_path = os.path.splitext(audio_path)[0] + ".txt"

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ GEMINI_API_KEY 환경 변수가 설정되어 있지 않습니다.")
        return ""

    print(f"\n🎤 오디오 분석 중 (STT): {audio_path}")
    client = genai.Client(api_key=api_key)

    with open(audio_path, "rb") as f:
        audio_data = f.read()

    prompt = (
        "이 오디오 파일의 음성을 듣고 한국어로 정확하게 그대로 받아적어주세요(전사/STT). "
        "감정 태그나 부가 설명 없이, 발화된 텍스트 내용만 출력해주세요."
    )

    response = client.models.generate_content(
        model=model,
        contents=[
            types.Part.from_bytes(data=audio_data, mime_type="audio/wav"),
            prompt,
        ],
    )

    transcribed_text = response.text.strip() if response.text else ""

    with open(output_txt_path, "w", encoding="utf-8") as f:
        f.write(transcribed_text)

    print("-" * 50)
    print("📝 [전사 결과]")
    print("-" * 50)
    print(transcribed_text)
    print("-" * 50)
    print(f"✅ 텍스트 파일 저장 완료: {output_txt_path}\n")

    return transcribed_text


def select_and_transcribe():
    """WAV 파일을 자동 탐색하고 대상 파일을 결정하여 전사를 실행합니다."""
    # 1. 사용자가 CLI 인자로 직접 파일명을 준 경우 (예: python gemini-stt-example.py my_voice.wav)
    if len(sys.argv) > 1:
        target_file = sys.argv[1]
        transcribe_audio_file(target_file)
        return

    # 2. 현재 폴더 내의 .wav 파일 자동 탐색
    wav_files = get_available_wav_files()

    if not wav_files:
        print("❌ 현재 디렉터리에 .wav 오디오 파일이 없습니다.")
        print("먼저 TTS를 실행하여 오디오 파일을 생성해주세요.")
        return

    # 파일이 1개만 있는 경우 -> 즉시 자동 실행
    if len(wav_files) == 1:
        target_file = wav_files[0]
        print(f"🔍 발견된 오디오 파일: '{target_file}' (자동 선택됨)")
        transcribe_audio_file(target_file)
        return

    # 파일이 여러 개 있는 경우 -> 목록 출력 후 사용자 선택 or 전체 변환
    print(f"📁 총 {len(wav_files)}개의 .wav 파일이 발견되었습니다:\n")
    for idx, f in enumerate(wav_files, start=1):
        size_kb = os.path.getsize(f) / 1024
        print(f"  [{idx}] {f} ({size_kb:.1f} KB)")
    print(f"  [A] 발견된 모든 파일 전체 일괄 변환")

    choice = input("\n변환할 파일 번호를 입력하세요 (기본값: 1번 최신 파일): ").strip().lower()

    if choice == "a":
        print(f"\n🚀 {len(wav_files)}개 파일 일괄 STT 변환을 시작합니다...")
        for f in wav_files:
            transcribe_audio_file(f)
    elif choice.isdigit() and 1 <= int(choice) <= len(wav_files):
        selected_file = wav_files[int(choice) - 1]
        transcribe_audio_file(selected_file)
    elif choice == "":
        # 엔터만 누르면 가장 최신 파일(1번) 자동 선택
        print(f"기본값(가장 최근 파일: '{wav_files[0]}')을 선택합니다.")
        transcribe_audio_file(wav_files[0])
    else:
        print("❌ 올바른 번호를 입력하지 않아 취소되었습니다.")


if __name__ == "__main__":
    select_and_transcribe()
