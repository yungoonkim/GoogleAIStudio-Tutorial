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
from storage import get_cached_transcript, save_transcript_to_csv

app = FastAPI(title="AI YouTube Searcher", version="1.1.0")

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
    1. CSV 캐시 조회: 이미 저장된 트랜스크립트가 있다면 다운로드/API 호출 없이 즉시 반환 (초고속 & 비용 절감)
    2. 캐시가 없을 경우:
       - 유튜브 오디오 다운로드 (yt-dlp)
       - Gemini 3.6 Flash 타임스탬프 STT 전사
       - CSV 파일(data/transcripts.csv)에 영구 저장
    """
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="유튜브 링크를 입력해주세요.")

    video_id = extract_video_id(url)
    if not video_id:
        raise HTTPException(status_code=400, detail="유효한 유튜브 영상 링크가 아닙니다.")

    # 1. CSV 캐시 조회
    cached = get_cached_transcript(url)
    if cached and cached.get("segments"):
        print(f"\n[⚡ CSV 캐시 히트] 이미 저장된 트랜스크립트를 즉시 불러옵니다: {cached['video']['title']} ({len(cached['segments'])}개 세그먼트)")
        return {
            "success": True,
            "from_cache": True,
            "video": cached["video"],
            "segments": cached["segments"],
        }

    print(f"\n[신규 영상 분석] 캐시 데이터가 없습니다. 오디오 다운로드 및 STT를 시작합니다: {url}")

    # 2. 오디오 다운로드
    try:
        print(f"[1/2] 오디오 다운로드 시작: {url}")
        audio_info = download_audio(url, output_dir=DOWNLOADS_DIR)
        print(f"다운로드 완료: {audio_info['file_name']}")
    except Exception as e:
        print(f"오디오 다운로드 실패: {e}")
        raise HTTPException(status_code=500, detail=f"오디오 다운로드 실패: {str(e)}")

    # 3. 타임스탬프 STT 전사
    try:
        print("[2/2] Gemini 3.6 Flash 타임스탬프 STT 분석 시작...")
        segments = transcribe_audio_with_timestamps(
            audio_path=audio_info["file_path"],
            mime_type=audio_info["mime_type"],
            model="gemini-3.6-flash",
        )
        print(f"STT 분석 완료! (총 {len(segments)}개 타임스탬프 세그먼트)")
    except Exception as e:
        print(f"STT 전사 실패: {e}")
        raise HTTPException(status_code=500, detail=f"STT 전사 실패: {str(e)}")

    # 4. CSV 파일에 저장
    video_dict = {
        "id": audio_info["video_id"],
        "title": audio_info["title"],
        "uploader": audio_info["uploader"],
        "thumbnail": audio_info["thumbnail"],
        "duration": audio_info["duration"],
        "duration_str": audio_info["duration_str"],
    }
    save_transcript_to_csv(url=url, video_info=video_dict, segments=segments)

    return {
        "success": True,
        "from_cache": False,
        "video": video_dict,
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
    print("🚀 AI YouTube Searcher 웹 서비스 시작 (CSV 캐싱 활성화)")
    print(f"🌐 브라우저 접속 주소: http://127.0.0.1:{port}")
    print("=" * 60)
    uvicorn.run("app:app", host="127.0.0.1", port=port, reload=True)
