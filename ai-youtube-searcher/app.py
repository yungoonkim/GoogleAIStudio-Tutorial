import os
import io
import sys
import warnings

if isinstance(sys.stdout, io.TextIOWrapper) and sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

warnings.filterwarnings("ignore")

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from downloader import download_audio, extract_video_id, get_video_info
from transcriber import transcribe_audio_with_timestamps
from qa_assistant import ask_video_qa, search_transcript

app = FastAPI(title="AI YouTube Searcher", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_DIR = os.path.join(BASE_DIR, "downloads")
STATIC_DIR = os.path.join(BASE_DIR, "static")

os.makedirs(DOWNLOADS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)


class ProcessRequest(BaseModel):
    url: str


class QARequest(BaseModel):
    query: str
    video_title: str = ""
    segments: list[dict]


class SearchRequest(BaseModel):
    query: str
    segments: list[dict]


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>웹 인터페이스 파일(static/index.html)을 찾을 수 없습니다.</h1>")


@app.post("/api/process")
async def process_video(req: ProcessRequest):
    """
    1. 유튜브 영상 메타데이터 추출
    2. 고음질 오디오 다운로드 (yt-dlp)
    3. gemini-3.5-transcribe 모델로 타임스탬프 기반 STT 세그먼트 추출
    """
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="유튜브 링크를 입력해주세요.")

    video_id = extract_video_id(url)
    if not video_id:
        raise HTTPException(status_code=400, detail="유효한 유튜브 영상 링크가 아닙니다.")

    # 1. 오디오 다운로드
    try:
        print(f"\n[1/2] 오디오 다운로드 시작: {url}")
        audio_info = download_audio(url, output_dir=DOWNLOADS_DIR)
        print(f"다운로드 완료: {audio_info['file_name']}")
    except Exception as e:
        print(f"오디오 다운로드 실패: {e}")
        raise HTTPException(status_code=500, detail=f"오디오 다운로드 실패: {str(e)}")

    # 2. 타임스탬프 STT 전사
    try:
        print("[2/2] Gemini 3.5 Transcribe 타임스탬프 STT 분석 시작...")
        segments = transcribe_audio_with_timestamps(
            audio_path=audio_info["file_path"],
            mime_type=audio_info["mime_type"],
            model="gemini-3.6-flash",
        )
        print(f"STT 분석 완료! (총 {len(segments)}개 타임스탬프 세그먼트)")
    except Exception as e:
        print(f"STT 전사 실패: {e}")
        raise HTTPException(status_code=500, detail=f"STT 전사 실패: {str(e)}")

    return {
        "success": True,
        "video": {
            "id": audio_info["video_id"],
            "title": audio_info["title"],
            "uploader": audio_info["uploader"],
            "thumbnail": audio_info["thumbnail"],
            "duration": audio_info["duration"],
            "duration_str": audio_info["duration_str"],
        },
        "segments": segments,
    }


@app.post("/api/qa")
async def process_qa(req: QARequest):
    """gemini-3.8-flash 모델을 통해 영상 내용에 대해 질문하고 답변을 받습니다."""
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="질문 내용을 입력해주세요.")

    try:
        result = ask_video_qa(
            query=req.query,
            segments=req.segments,
            video_title=req.video_title,
            model="gemini-3.8-flash",
        )
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"질의응답 처리 실패: {str(e)}")


@app.post("/api/search")
async def process_search(req: SearchRequest):
    """트랜스크립트 내에서 특정 단어나 내용을 키워드로 검색합니다."""
    matched = search_transcript(req.query, req.segments)
    return {"success": True, "data": matched}


if __name__ == "__main__":
    import uvicorn
    port = 8080
    print("=" * 60)
    print("🚀 AI YouTube Searcher 웹 서비스 시작")
    print(f"🌐 브라우저 접속 주소: http://127.0.0.1:{port}")
    print("=" * 60)
    uvicorn.run("app:app", host="127.0.0.1", port=port, reload=True)
