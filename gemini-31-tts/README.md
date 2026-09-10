# Gemini 3.1 Flash TTS (Text-to-Speech) 코드 라인별(Line-by-Line) 상세 해설

이 문서는 `gemini-31-tts-example.py` 파일의 전체 코드를 한 줄 한 줄 분석하여 각 라인의 역할과 작동 원리를 상세히 설명합니다.

---

## 📌 목차
1. [라이브러리 임포트 (1~9행)](#1-라이브러리-임포트-19행)
2. [바이너리 파일 저장 유틸리티 (11~16행)](#2-바이너리-파일-저장-유틸리티-1116행)
3. [TTS 음성 생성 메인 함수 - 설정 및 프롬프트 (18~52행)](#3-tts-음성-생성-메인-함수---설정-및-프롬프트-1852행)
4. [스트리밍 오디오 수신 및 버퍼 결합 (53~73행)](#4-스트리밍-오디오-수신-및-버퍼-결합-5373행)
5. [WAV 파일 저장 및 STT 자동 연동 (74~84행)](#5-wav-파일-저장-및-stt-자동-연동-7484행)
6. [PCM 데이터를 WAV 포맷으로 변환 (86~124행)](#6-pcm-데이터를-wav-포맷으로-변환-86124행)
7. [오디오 MIME 타입 파싱 (126~158행)](#7-오디오-mime-타입-파싱-126158행)
8. [생성된 음성 텍스트 전사(STT) 함수 (160~202행)](#8-생성된-음성-텍스트-전사stt-함수-160202행)
9. [프로그램 진입점 (204~207행)](#9-프로그램-진입점-204207행)

---

### 1. 라이브러리 임포트 (1~9행)

```python
1: # To run this code you need to install the following dependencies:
2: # pip install google-genai
3: 
4: import mimetypes
5: import os
6: import struct
7: from google import genai
8: from google.genai import types
9: 
```

* **1~2행**: 실행 전 필요한 의존성 라이브러리 안내 주석입니다. (`google-genai` 최신 공식 SDK)
* **4행 (`import mimetypes`)**: MIME 타입(예: `audio/wav`)을 기반으로 파일 확장자를 추론하기 위한 파이썬 표준 모듈입니다.
* **5행 (`import os`)**: 환경 변수(`GEMINI_API_KEY`)를 읽거나 파일 경로의 존재 여부를 확인할 때 사용합니다.
* **6행 (`import struct`)**: 원시 오디오 데이터(PCM)에 WAV 규격의 바이너리 헤더(RIFF/WAVE)를 바이트 단위로 패킹(조립)하기 위한 모듈입니다.
* **7행 (`from google import genai`)**: Google Gemini 2.x/3.x 모델들과 통신하는 최신 GenAI 클라이언트 라이브러리입니다.
* **8행 (`from google.genai import types`)**: API 호출 시 전달하는 설정 객체(`GenerateContentConfig`, `SpeechConfig`, `Part` 등)의 타입 정의 모음입니다.

---

### 2. 바이너리 파일 저장 유틸리티 (11~16행)

```python
11: def save_binary_file(file_name, data):
12:     f = open(file_name, "wb")
13:     f.write(data)
14:     f.close()
15:     print(f"File saved to to: {file_name}")
16: 
```

* **11행**: 파일 이름과 바이너리 데이터(`bytes`)를 인자로 받는 함수 정의입니다.
* **12행**: 전달받은 파일 이름을 바이너리 쓰기(`"wb"`) 모드로 엽니다.
* **13행**: 완성된 WAV 바이트 데이터를 디스크에 기록합니다.
* **14행**: 파일 스트림을 닫아 버퍼를 완전히 비우고 자원을 해제합니다.
* **15행**: 파일 저장이 완료되었음을 알리는 로그를 출력합니다.

---

### 3. TTS 음성 생성 메인 함수 - 설정 및 프롬프트 (18~52행)

```python
18: def generate():
19:     client = genai.Client(
20:         api_key=os.environ.get("GEMINI_API_KEY"),
21:     )
22: 
23:     model = "gemini-3.1-flash-tts-preview"
24:     contents = [
25:         types.Content(
26:             role="user",
27:             parts=[
28:                 types.Part.from_text(text="""## Scene:
29: A professional newsroom studio with high-tech breaking news alert ambiance
30: 
31: ## Sample Context:
32: The tech news anchor is urgently breaking major unexpected news about Google's new AI model launch and its shockingly low price.
33: 
34: ## Transcript:
35: [breaking news tone] 긴급 속보입니다! 구글이 차세대 플래그십 AI 모델인 '제미나이 4.0 프로(Gemini 4.0 Pro)'를 전격 출시했습니다. [excited] 그런데 성능보다 더 전 세계를 충격에 빠뜨린 건 바로 가격인데요! 기존 모델 대비 90% 이상 폭락한 파격적인 단가로 공개되면서, 개발자 커뮤니티는 그야말로 축제 분위기입니다. [amazed] AI 업계의 치킨 게임이 본격적으로 시작된 것 같습니다."""),
36:             ],
37:         ),
38:     ]
39:     generate_content_config = types.GenerateContentConfig(
40:         temperature=1,
41:         response_modalities=[
42:             "audio",
43:         ],
44:         speech_config=types.SpeechConfig(
45:             voice_config=types.VoiceConfig(
46:                 prebuilt_voice_config=types.PrebuiltVoiceConfig(
47:                     voice_name="Kore"
48:                 )
49:             )
50:         ),
51:     )
52: 
```

* **18행**: 음성 생성을 총괄하는 `generate()` 함수 정의입니다.
* **19~21행**: OS 환경 변수에서 `GEMINI_API_KEY`를 읽어와 Gemini API 클라이언트 객체를 생성합니다.
* **23행**: 음성 합성(TTS) 전용 모델인 `"gemini-3.1-flash-tts-preview"`를 지정합니다.
* **24~38행**: 모델에 전달할 대본 프롬프트입니다.
  * `## Scene:` 음향 배경 설정 (뉴스룸 스튜디오 분위기)
  * `## Sample Context:` 발화 상황 (충격적인 가격 인하 소식을 전하는 긴박한 뉴스 앵커)
  * `## Transcript:` 실제 읽을 대사와 감정 연기 태그(`[breaking news tone]`, `[excited]`, `[amazed]`)
* **39~40행**: 생성 설정 객체를 정의하며, 음성의 다양성과 자연스러움을 위해 `temperature=1`을 부여합니다.
* **41~43행**: 모델의 응답 모달리티를 텍스트가 아닌 `"audio"`로 지정합니다.
* **44~50행**: 음성 설정(`SpeechConfig`)으로, Google AI Studio에서 제공하는 사전 정의 보이스 중 여성 한국어 톤에 적합한 `"Kore"`를 선택합니다.

---

### 4. 스트리밍 오디오 수신 및 버퍼 결합 (53~73행)

```python
53:     audio_bytes_chunks = bytearray()
54:     mime_type = "audio/L16;rate=24000"
55: 
56:     print("음성 생성 스트리밍 시작...")
57:     for chunk in client.models.generate_content_stream(
58:         model=model,
59:         contents=contents,
60:         config=generate_content_config,
61:     ):
62:         if not chunk.parts:
63:             continue
64:         first_part = chunk.parts[0]
65:         inline_data = first_part.inline_data
66:         if inline_data is not None and inline_data.data is not None:
67:             if inline_data.mime_type:
68:                 mime_type = inline_data.mime_type
69:             audio_bytes_chunks.extend(inline_data.data)
70:         else:
71:             if text := chunk.text:
72:                 print(text)
73: 
```

* **53행 (`audio_bytes_chunks = bytearray()`)**: 스트리밍으로 수신되는 작은 오디오 조각들을 메모리 상에서 하나의 연속된 데이터로 합치기 위한 가변 바이트 배열입니다.
* **54행**: Gemini TTS 모델의 기본 오디오 규격인 16비트 리니어 PCM, 24kHz 샘플레이트(`audio/L16;rate=24000`)를 기본 MIME 타입으로 지정합니다.
* **56행**: 사용자에게 스트리밍 시작을 알립니다.
* **57~61행**: `generate_content_stream` 메서드를 호출하여 오디오 조각(청크)을 실시간으로 스트리밍 수신합니다.
* **62~63행**: 응답 청크에 `parts`가 비어있을 경우 발생할 수 있는 인덱스 오류를 방지하기 위한 안전 가드입니다.
* **64~65행**: 첫 번째 파트에서 인라인 오디오 데이터(`inline_data`) 객체를 추출합니다.
* **66~69행**: `inline_data`와 `inline_data.data`가 모두 `None`이 아님을 확인한 후, 응답에 포함된 MIME 타입을 갱신하고, 오디오 조각 바이트를 `audio_bytes_chunks` 버퍼에 차례대로 이어 붙입니다(`extend`).
* **70~72행**: 만약 오디오 데이터가 아닌 텍스트가 전달된 경우 콘솔에 출력합니다.

---

### 5. WAV 파일 저장 및 STT 자동 연동 (74~84행)

```python
74:     if audio_bytes_chunks:
75:         output_filename = "gemini_4_news_briefing.wav"
76:         wav_data = convert_to_wav(bytes(audio_bytes_chunks), mime_type)
77:         save_binary_file(output_filename, wav_data)
78:         print(f"✅ 오디오 파일이 하나로 성공적으로 저장되었습니다: {output_filename}")
79:         
80:         # 생성된 오디오 파일에 대한 STT 수행
81:         output_txt = "gemini_4_news_briefing.txt"
82:         transcribe_audio(client=client, audio_path=output_filename, output_txt_path=output_txt)
83:     else:
84:         print("생성된 오디오 데이터가 없습니다.")
85: 
```

* **74행**: 수집된 오디오 데이터가 존재하는지 확인합니다.
* **75행**: 저장할 WAV 파일명을 `"gemini_4_news_briefing.wav"`로 설정합니다.
* **76행**: 모아둔 원시 PCM 데이터에 표준 WAV 헤더를 붙이기 위해 `convert_to_wav` 함수를 호출합니다.
* **77행**: 완성된 WAV 데이터를 파일로 저장합니다.
* **78행**: 성공 완료 메시지를 출력합니다.
* **80~82행**: 방금 생성된 WAV 파일을 다시 읽어 텍스트로 잘 발화되었는지 검증하기 위해 하단의 `transcribe_audio`(STT) 함수를 자동 호출하여 `.txt` 파일까지 저장합니다.
* **83~84행**: 오디오 수신에 실패한 경우의 예외 처리입니다.

---

### 6. PCM 데이터를 WAV 포맷으로 변환 (86~124행)

```python
86: def convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
87:     """Generates a WAV file header for the given audio data and parameters."""
88:     parameters = parse_audio_mime_type(mime_type)
89:     bits_per_sample = parameters["bits_per_sample"]
90:     sample_rate = parameters["rate"]
91:     num_channels = 1
92:     data_size = len(audio_data)
93:     bytes_per_sample = bits_per_sample // 8
94:     block_align = num_channels * bytes_per_sample
95:     byte_rate = sample_rate * block_align
96:     chunk_size = 36 + data_size  # 36 bytes for header fields before data chunk size
97: 
98:     # http://soundfile.sapp.org/doc/WaveFormat/
99: 
100:     header = struct.pack(
101:         "<4sI4s4sIHHIIHH4sI",
102:         b"RIFF",          # ChunkID
103:         chunk_size,       # ChunkSize (total file size - 8 bytes)
104:         b"WAVE",          # Format
105:         b"fmt ",          # Subchunk1ID
106:         16,               # Subchunk1Size (16 for PCM)
107:         1,                # AudioFormat (1 for PCM)
108:         num_channels,     # NumChannels
109:         sample_rate,      # SampleRate
110:         byte_rate,        # ByteRate
111:         block_align,      # BlockAlign
112:         bits_per_sample,  # BitsPerSample
113:         b"data",          # Subchunk2ID
114:         data_size         # Subchunk2Size (size of audio data)
115:     )
116:     return header + audio_data
117: 
```

* **86~87행**: 원시 PCM 오디오 바이트에 표준 WAV(RIFF) 44바이트 헤더를 덧붙여 반환하는 함수입니다.
* **88~90행**: MIME 타입에서 샘플레이트(24,000Hz)와 샘플당 비트수(16bit)를 추출합니다.
* **91~96행**: 모노 채널(1), 전체 데이터 크기, 바이트 레이트, 블록 정렬, 전체 청크 크기 등 WAV 헤더 계산에 필요한 필드들을 연산합니다.
* **100~115행 (`struct.pack`)**: C 구조체 형태의 리틀 엔디안(`"<"`) 바이너리 규격에 맞춰 44바이트 헤더를 패킹합니다.
  * `RIFF`, `WAVE`: 파일 포맷 식별자
  * `fmt `: 오디오 형식 서브청크 (PCM=1, 채널수, 샘플레이트, 데이터전송률)
  * `data`: 실제 소리 데이터 청크 식별자 및 데이터 길이
* **116행**: 생성된 44바이트 헤더 뒤에 실제 PCM 소리 데이터를 합쳐서 완성된 WAV 바이트를 반환합니다.

---

### 7. 오디오 MIME 타입 파싱 (126~158행)

```python
126: def parse_audio_mime_type(mime_type: str) -> dict[str, int]:
127:     """Parses bits per sample and rate from an audio MIME type string."""
128:     bits_per_sample = 16
129:     rate = 24000
130: 
131:     # Extract rate from parameters
132:     parts = mime_type.split(";")
133:     for param in parts:
134:         param = param.strip()
135:         if param.lower().startswith("rate="):
136:             try:
137:                 rate_str = param.split("=", 1)[1]
138:                 rate = int(rate_str)
139:             except (ValueError, IndexError):
140:                 pass
141:         elif param.startswith("audio/L"):
142:             try:
143:                 bits_per_sample = int(param.split("L", 1)[1])
144:             except (ValueError, IndexError):
145:                 pass
146: 
147:     return {"bits_per_sample": bits_per_sample, "rate": rate}
148: 
```

* **126~129행**: 기본값으로 16비트(`bits_per_sample = 16`) 및 24000Hz(`rate = 24000`)를 설정합니다.
* **132~145행**: MIME 문자열(예: `audio/L16;rate=24000`)을 세미콜론(`;`)으로 분리하여 `rate=` 및 `audio/L` 뒤의 숫자를 안전하게 정수로 파싱합니다.
* **147행**: 파싱된 값(또는 기본값)을 딕셔너리로 반환합니다.

---

### 8. 생성된 음성 텍스트 전사(STT) 함수 (160~202행)

```python
160: def transcribe_audio(
161:     client: genai.Client,
162:     audio_path: str = "gemini_4_news_briefing.wav",
163:     output_txt_path: str = "gemini_4_news_briefing.txt",
164:     model: str = "gemini-3.6-flash",
165: ) -> str:
166:     """오디오 파일을 읽어서 Gemini 모델로 텍스트 전사(STT)를 수행하고 파일로 저장합니다."""
167:     if not os.path.exists(audio_path):
168:         print(f"❌ 전사할 오디오 파일이 없습니다: {audio_path}")
169:         return ""
170: 
171:     print(f"\n🎤 오디오 음성 인식(STT) 진행 중... ({audio_path})")
172:     with open(audio_path, "rb") as f:
173:         audio_data = f.read()
174: 
175:     prompt = (
176:         "이 오디오 파일의 음성을 듣고 한국어로 정확하게 그대로 받아적어주세요(전사/STT). "
177:         "감정 태그나 부가 설명 없이 오디오에 발화된 한국어 텍스트 내용만 출력하세요."
178:     )
179: 
180:     response = client.models.generate_content(
181:         model=model,
182:         contents=[
183:             types.Part.from_bytes(data=audio_data, mime_type="audio/wav"),
184:             prompt,
185:         ],
186:     )
187: 
188:     transcribed_text = response.text.strip() if response.text else ""
189: 
190:     # UTF-8 텍스트 파일로 저장
191:     with open(output_txt_path, "w", encoding="utf-8") as f:
192:         f.write(transcribed_text)
193: 
194:     print("=" * 60)
195:     print("📝 [STT 전사 결과]")
196:     print("=" * 60)
197:     print(transcribed_text)
198:     print("=" * 60)
199:     print(f"✅ STT 텍스트 파일이 저장되었습니다: {output_txt_path}\n")
200: 
201:     return transcribed_text
202: 
```

* **160~165행**: 생성된 오디오를 Gemini 멀티모달 모델(`gemini-3.6-flash`)에 전달하여 STT를 수행하는 함수 정의입니다.
* **167~169행**: 대상 오디오 파일이 존재하는지 검증합니다.
* **172~173행**: 생성된 WAV 바이너리 데이터를 메모리로 읽어옵니다.
* **175~178행**: 발화 내용만 군더더기 없이 받아적도록 유도하는 STT 프롬프트입니다.
* **180~186행**: 오디오 바이트 데이터(`types.Part.from_bytes`)와 프롬프트를 함께 Gemini 모델로 전송합니다.
* **188~192행**: 모델의 텍스트 답변을 UTF-8 인코딩 텍스트 파일(`gemini_4_news_briefing.txt`)로 저장합니다.
* **194~201행**: 결과를 터미널 콘솔에 출력하고 문자열을 반환합니다.

---

### 9. 프로그램 진입점 (204~207행)

```python
204: if __name__ == "__main__":
205:     generate()
```

* **204~205행**: 스크립트가 직접 실행되었을 때 메인 진입점으로서 `generate()` 함수를 호출하여 전체 TTS 및 STT 파이프라인을 실행합니다.
