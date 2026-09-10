# Gemini 3.5 Transcribe STT (Speech-to-Text) 코드 라인별(Line-by-Line) 상세 해설

이 문서는 `gemini-35-stt-example.py` 파일의 전체 코드를 한 줄 한 줄 분석하여 각 라인의 역할과 작동 원리를 상세히 설명합니다.

---

## 📌 목차
1. [라이브러리 임포트 및 환경 설정 (1~21행)](#1-라이브러리-임포트-및-환경-설정-121행)
2. [전사(STT) 메인 함수 - 파일 로드 및 모델 구성 (23~52행)](#2-전사stt-메인-함수---파일-로드-및-모델-구성-2352행)
3. [전사 고급 옵션 설정 (54~59행)](#3-전사-고급-옵션-설정-5459행)
4. [실시간 스트리밍 출력 루프 (61~73행)](#4-실시간-스트리밍-출력-루프-6173행)
5. [프로그램 진입점 및 CLI 인자 지원 (76~78행)](#5-프로그램-진입점-및-cli-인자-지원-7678행)

---

### 1. 라이브러리 임포트 및 환경 설정 (1~21행)

```python
1: # To run this code you need to install the following dependencies:
2: # pip install google-genai
3: 
4: import io
5: import os
6: import sys
7: import warnings
8: 
9: # Windows 콘솔 한글 깨짐 방지
10: if isinstance(sys.stdout, io.TextIOWrapper) and sys.stdout.encoding != "utf-8":
11:     try:
12:         sys.stdout.reconfigure(encoding="utf-8")
13:     except Exception:
14:         pass
15: 
16: # 경고 메시지 억제
17: warnings.filterwarnings("ignore")
18: 
19: from google import genai
20: from google.genai import types
21: 
```

* **1~2행**: 실행 전 필요한 의존성 안내 주석입니다.
* **4행 (`import io`)**: 입출력 스트림 타입 검사(`TextIOWrapper`)를 위해 사용합니다.
* **5행 (`import os`)**: 환경 변수 확인 및 파일 경로 검사를 위한 모듈입니다.
* **6행 (`import sys`)**: 표준 입출력 스트림(`sys.stdout`)과 커맨드라인 인자(`sys.argv`)를 다루기 위한 모듈입니다.
* **7행 (`import warnings`)**: 라이브러리 내부 권고성 경고 메시지를 필터링하기 위한 모듈입니다.
* **9~14행**: Windows 파워쉘/명령 프롬프트 환경에서 한글 출력이 깨지는 문제를 해결합니다. 특히 `isinstance(sys.stdout, io.TextIOWrapper)`를 먼저 체크하여 IDE의 정적 타입 분석기(Pylance/Pyright)에서 `reconfigure` 메서드에 빨간 밑줄이 그어지는 것을 방지합니다.
* **16~17행**: GenAI SDK에서 출력하는 AFC(자동 함수 호출) 권고 경고 등을 숨겨 터미널 출력을 깔끔하게 유지합니다.
* **19~20행**: Google Gemini의 최신 SDK 클라이언트(`genai`)와 설정 타입 모음(`types`)을 임포트합니다.

---

### 2. 전사(STT) 메인 함수 - 파일 로드 및 모델 구성 (23~52행)

```python
23: def generate(audio_file_path: str = "gemini_4_news_briefing.wav"):
24:     api_key = os.environ.get("GEMINI_API_KEY")
25:     if not api_key:
26:         print("❌ GEMINI_API_KEY 환경 변수가 설정되어 있지 않습니다.")
27:         return
28: 
29:     if not os.path.exists(audio_file_path):
30:         print(f"❌ 오디오 파일을 찾을 수 없습니다: {audio_file_path}")
31:         return
32: 
33:     client = genai.Client(api_key=api_key)
34: 
35:     # 1. 오디오 파일 읽기
36:     with open(audio_file_path, "rb") as f:
37:         audio_bytes = f.read()
38: 
39:     model = "gemini-3.5-transcribe"
40: 
41:     # 2. 오디오 바이트 데이터를 입력 parts에 추가
42:     contents = [
43:         types.Content(
44:             role="user",
45:             parts=[
46:                 types.Part.from_bytes(
47:                     data=audio_bytes,
48:                     mime_type="audio/wav",
49:                 ),
50:             ],
51:         ),
52:     ]
53: 
```

* **23행**: 전사를 실행할 오디오 파일 경로를 기본값(`gemini_4_news_briefing.wav`)과 함께 인자로 받는 `generate` 함수를 정의합니다.
* **24~27행**: 환경 변수 `GEMINI_API_KEY`가 설정되어 있는지 확인하고, 없을 경우 오류 메시지와 함께 조기 종료합니다.
* **29~31행**: 지정한 오디오 파일이 실제로 디스크에 존재하는지 검증합니다.
* **33행**: API 키를 전달하여 Gemini 통신용 `Client` 인스턴스를 생성합니다.
* **35~37행**: 오디오 파일을 바이너리 읽기(`"rb"`) 모드로 열어 전체 바이트 데이터를 `audio_bytes`에 로드합니다.
* **39행**: Google의 음성 전사 전문 모델인 `"gemini-3.5-transcribe"`를 모델명으로 지정합니다.
* **42~52행**: 모델 입력 구조를 정의합니다.
  * `types.Content(role="user")`: 사용자의 입력 메시지 객체
  * `types.Part.from_bytes(...)`: 파일 업로드 API를 별도로 거치지 않고, 로컬의 오디오 바이트 데이터(`audio_bytes`)와 MIME 타입(`audio/wav`)을 모델에 직접 인라인으로 주입합니다.

---

### 3. 전사 고급 옵션 설정 (54~59행)

```python
54:     generate_content_config = types.GenerateContentConfig(
55:         audio_transcription_config=types.AudioTranscriptionConfig(
56:             word_timestamp=True,
57:             diarization=True,
58:         ),
59:     )
60: 
```

* **54~59행**: `gemini-3.5-transcribe` 모델의 전사 기능을 극대화하는 옵션 객체(`AudioTranscriptionConfig`)를 설정합니다.
  * **`word_timestamp=True`**: 단순히 문장만 전사하는 것이 아니라, 각 단어가 발화된 시작/끝 시간(타임스탬프) 메타데이터를 함께 계산하도록 활성화합니다.
  * **`diarization=True`**: 음성 속에 등장하는 여러 화자를 구분(화자 분리 / 화자 식별)하도록 활성화합니다.

---

### 4. 실시간 스트리밍 출력 루프 (61~73행)

```python
61:     print(f"🎤 '{audio_file_path}' 전사(STT) 진행 중 ({model})...\n")
62:     print("-" * 50)
63: 
64:     for chunk in client.models.generate_content_stream(
65:         model=model,
66:         contents=contents,
67:         config=generate_content_config,
68:     ):
69:         if text := chunk.text:
70:             print(text, end="", flush=True)
71: 
72:     print("\n" + "-" * 50)
73:     print("✅ 전사 완료!")
74: 
```

* **61~62행**: 전사가 시작되었음을 알리는 안내선을 콘솔에 출력합니다.
* **64~68행**: `client.models.generate_content_stream`을 호출하여 오디오 분석 및 전사 결과를 스트리밍 형태로 청크 단위 수신합니다.
* **69~70행**: 수신된 청크에 텍스트가 있을 경우, 줄바꿈 없이 즉시 화면에 밀어내어(`flush=True`) 실시간 자막처럼 자연스럽게 텍스트가 타이핑되듯 표시됩니다.
* **72~73행**: 전사 작업이 성공적으로 끝났음을 알리는 완료 메시지를 출력합니다.

---

### 5. 프로그램 진입점 및 CLI 인자 지원 (76~78행)

```python
76: if __name__ == "__main__":
77:     target_file = sys.argv[1] if len(sys.argv) > 1 else "gemini_4_news_briefing.wav"
78:     generate(target_file)
```

* **76행**: 파이썬 인터프리터에서 스크립트가 직접 실행되었는지 확인하는 관용구입니다.
* **77행**: CLI 인자 지원 로직입니다.
  * `python gemini-35-stt-example.py` 로 실행하면 기본값인 `"gemini_4_news_briefing.wav"`를 대상으로 동작합니다.
  * `python gemini-35-stt-example.py other_audio.wav` 처럼 인자를 주면 첫 번째 인자(`sys.argv[1]`)를 대상 파일로 자동 인식합니다.
* **78행**: 결정된 대상 파일을 넘겨 `generate()` 함수를 실행합니다.
