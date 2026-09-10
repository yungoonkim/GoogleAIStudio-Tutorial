# To run this code you need to install the following dependencies:
# pip install google-genai

import mimetypes
import os
import struct
from google import genai
from google.genai import types


def save_binary_file(file_name, data):
    f = open(file_name, "wb")
    f.write(data)
    f.close()
    print(f"File saved to to: {file_name}")


def generate():
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemini-3.1-flash-tts-preview"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""## Scene:
                    A professional newsroom studio with high-tech breaking news alert ambiance

                    ## Sample Context:
                    The tech news anchor is urgently breaking major unexpected news about Google's new AI model launch and its shockingly low price.

                    ## Transcript:
                    [breaking news tone] 긴급 속보입니다! 구글이 차세대 플래그십 AI 모델인 '제미나이 4.0 프로(Gemini 4.0 Pro)'를 전격 출시했습니다. [excited] 그런데 성능보다 더 전 세계를 충격에 빠뜨린 건 바로 가격인데요! 기존 모델 대비 90% 이상 폭락한 파격적인 단가로 공개되면서, 개발자 커뮤니티는 그야말로 축제 분위기입니다. [amazed] AI 업계의 치킨 게임이 본격적으로 시작된 것 같습니다."""),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        temperature=1,
        response_modalities=[
            "audio",
        ],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name="Kore"
                )
            )
        ),
    )

    audio_bytes_chunks = bytearray()
    mime_type = "audio/L16;rate=24000"

    print("음성 생성 스트리밍 시작...")
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if not chunk.parts:
            continue
        first_part = chunk.parts[0]
        inline_data = first_part.inline_data
        if inline_data is not None and inline_data.data is not None:
            if inline_data.mime_type:
                mime_type = inline_data.mime_type
            audio_bytes_chunks.extend(inline_data.data)
        else:
            if text := chunk.text:
                print(text)

    if audio_bytes_chunks:
        output_filename = "gemini_4_news_briefing.wav"
        wav_data = convert_to_wav(bytes(audio_bytes_chunks), mime_type)
        save_binary_file(output_filename, wav_data)
        print(f"✅ 오디오 파일이 하나로 성공적으로 저장되었습니다: {output_filename}")
        
        # 생성된 오디오 파일에 대한 STT 수행
        output_txt = "gemini_4_news_briefing.txt"
        transcribe_audio(client=client, audio_path=output_filename, output_txt_path=output_txt)
    else:
        print("생성된 오디오 데이터가 없습니다.")

def convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
    """Generates a WAV file header for the given audio data and parameters.

    Args:
        audio_data: The raw audio data as a bytes object.
        mime_type: Mime type of the audio data.

    Returns:
        A bytes object representing the WAV file header.
    """
    parameters = parse_audio_mime_type(mime_type)
    bits_per_sample = parameters["bits_per_sample"]
    sample_rate = parameters["rate"]
    num_channels = 1
    data_size = len(audio_data)
    bytes_per_sample = bits_per_sample // 8
    block_align = num_channels * bytes_per_sample
    byte_rate = sample_rate * block_align
    chunk_size = 36 + data_size  # 36 bytes for header fields before data chunk size

    # http://soundfile.sapp.org/doc/WaveFormat/

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",          # ChunkID
        chunk_size,       # ChunkSize (total file size - 8 bytes)
        b"WAVE",          # Format
        b"fmt ",          # Subchunk1ID
        16,               # Subchunk1Size (16 for PCM)
        1,                # AudioFormat (1 for PCM)
        num_channels,     # NumChannels
        sample_rate,      # SampleRate
        byte_rate,        # ByteRate
        block_align,      # BlockAlign
        bits_per_sample,  # BitsPerSample
        b"data",          # Subchunk2ID
        data_size         # Subchunk2Size (size of audio data)
    )
    return header + audio_data

def parse_audio_mime_type(mime_type: str) -> dict[str, int]:
    """Parses bits per sample and rate from an audio MIME type string.

    Assumes bits per sample is encoded like "L16" and rate as "rate=xxxxx".

    Args:
        mime_type: The audio MIME type string (e.g., "audio/L16;rate=24000").

    Returns:
        A dictionary with "bits_per_sample" and "rate" keys. Values will be integers.
    """
    bits_per_sample = 16
    rate = 24000

    # Extract rate from parameters
    parts = mime_type.split(";")
    for param in parts: # Skip the main type part
        param = param.strip()
        if param.lower().startswith("rate="):
            try:
                rate_str = param.split("=", 1)[1]
                rate = int(rate_str)
            except (ValueError, IndexError):
                # Handle cases like "rate=" with no value or non-integer value
                pass # Keep rate as default
        elif param.startswith("audio/L"):
            try:
                bits_per_sample = int(param.split("L", 1)[1])
            except (ValueError, IndexError):
                pass # Keep bits_per_sample as default if conversion fails

    return {"bits_per_sample": bits_per_sample, "rate": rate}


def transcribe_audio(
    client: genai.Client,
    audio_path: str = "gemini_4_news_briefing.wav",
    output_txt_path: str = "gemini_4_news_briefing.txt",
    model: str = "gemini-3.6-flash",
) -> str:
    """오디오 파일을 읽어서 Gemini 모델로 텍스트 전사(STT)를 수행하고 파일로 저장합니다."""
    if not os.path.exists(audio_path):
        print(f"❌ 전사할 오디오 파일이 없습니다: {audio_path}")
        return ""

    print(f"\n🎤 오디오 음성 인식(STT) 진행 중... ({audio_path})")
    with open(audio_path, "rb") as f:
        audio_data = f.read()

    prompt = (
        "이 오디오 파일의 음성을 듣고 한국어로 정확하게 그대로 받아적어주세요(전사/STT). "
        "감정 태그나 부가 설명 없이 오디오에 발화된 한국어 텍스트 내용만 출력하세요."
    )

    response = client.models.generate_content(
        model=model,
        contents=[
            types.Part.from_bytes(data=audio_data, mime_type="audio/wav"),
            prompt,
        ],
    )

    transcribed_text = response.text.strip() if response.text else ""

    # UTF-8 텍스트 파일로 저장
    with open(output_txt_path, "w", encoding="utf-8") as f:
        f.write(transcribed_text)

    print("=" * 60)
    print("📝 [STT 전사 결과]")
    print("=" * 60)
    print(transcribed_text)
    print("=" * 60)
    print(f"✅ STT 텍스트 파일이 저장되었습니다: {output_txt_path}\n")

    return transcribed_text


if __name__ == "__main__":
    generate()


