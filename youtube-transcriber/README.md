# YouTube Audio Transcriber (웹 서비스)

유튜브 영상 URL을 입력하면 해당 영상의 고음질 오디오를 다운로드하고, Google Gemini STT 모델(`gemini-3.5-transcribe`)을 통해 음성을 정밀 텍스트(트랜스크립트)로 추출해주는 풀스택 웹 애플리케이션입니다.

---

## 🌟 주요 기능
* **간편한 유튜브 링크 입력**: 영상 URL(일반 영상, Shorts 등) 입력만으로 즉시 작동
* **고음질 오디오 추출**: `yt-dlp` 기반으로 ffmpeg 없이도 원본 오디오 스트림(m4a/webm) 무손실 다운로드
* **Google Gemini AI 트랜스크립션**: 최신 STT 모델을 활용해 빠르고 정확한 음성 텍스트 변환
* **내장 웹 오디오 플레이어**: 다운로드된 오디오를 브라우저에서 바로 청취
* **결과 관리 기능**: 트랜스크립트 1초 만에 클립보드 복사 & UTF-8 `.txt` 파일 다운로드 지원
* **반응형 모던 UI**: Tailwind CSS 기반의 직관적인 디자인

---

## 📂 파일 구성
```text
youtube-transcriber/
├── app.py              # FastAPI 메인 웹 서버 & REST API
├── downloader.py       # yt-dlp 기반 유튜브 오디오 다운로드 모듈
├── transcriber.py      # Gemini API 오디오 업로드 및 STT 전사 모듈
├── static/
│   └── index.html      # 반응형 웹 대시보드 UI
├── downloads/          # 다운로드된 오디오 및 텍스트 파일 저장소
└── README.md           # 실행 가이드
```

---

## 🚀 실행 방법

### 1. 가상환경 및 API 키 확인
`GEMINI_API_KEY` 환경 변수가 설정되어 있어야 합니다:
```powershell
$env:GEMINI_API_KEY="YOUR_API_KEY"
```

### 2. 웹 서버 시작
`youtube-transcriber` 폴더로 이동하거나 해당 폴더 경로를 지정하여 실행합니다:

```powershell
cd youtube-transcriber
python app.py
```

또는 루트 폴더에서:
```powershell
python youtube-transcriber/app.py
```

### 3. 브라우저 접속
서버가 시작되면 웹 브라우저를 열고 아래 주소로 접속합니다:
👉 **http://127.0.0.1:8000**
