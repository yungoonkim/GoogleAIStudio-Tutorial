import os
import io
import sys
import warnings

# Windows 콘솔 한글 깨짐 방지
if isinstance(sys.stdout, io.TextIOWrapper) and sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

warnings.filterwarnings("ignore")

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from downloader import download_audio, get_video_info
from transcriber import transcribe_audio_file

app = FastAPI(title="YouTube Audio Transcriber", version="1.0.0")

# CORS 활성화
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


class URLRequest(BaseModel):
    url: str


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """메인 웹 대시보드 페이지를 반환합니다."""
    index_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_file):
        with open(index_file, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>웹 인터페이스 파일을 찾을 수 없습니다. (static/index.html)</h1>")


@app.post("/api/info")
async def fetch_video_info(req: URLRequest):
    """유튜브 링크로부터 제목, 썸네일, 재생시간을 빠르게 조회합니다."""
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="유튜브 URL을 입력해주세요.")

    try:
        info = get_video_info(url)
        return {"success": True, "data": info}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"영상 정보를 불러올 수 없습니다: {str(e)}")


@app.post("/api/transcribe")
async def process_transcribe(req: URLRequest):
    """
    1. 유튜브 영상에서 오디오 다운로드
    2. Gemini STT 모델로 텍스트 전사
    3. 결과 반환
    """
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="유튜브 URL을 입력해주세요.")

    # 1. 오디오 다운로드
    try:
        print(f"\n[1/2] 유튜브 오디오 다운로드 시작: {url}")
        audio_info = download_audio(url, output_dir=DOWNLOADS_DIR)
        print(f"다운로드 완료: {audio_info['file_name']} ({audio_info['mime_type']})")
    except Exception as e:
        print(f"다운로드 실패: {e}")
        raise HTTPException(status_code=500, detail=f"오디오 다운로드 실패: {str(e)}")

    # 2. Gemini STT 전사
    try:
        print(f"[2/2] Gemini 모델로 STT 전사 분석 시작...")
        stt_result = transcribe_audio_file(
            audio_path=audio_info["file_path"],
            mime_type=audio_info["mime_type"],
            model="gemini-3.5-transcribe",
        )
        print("전사 분석 완료!")
    except Exception as e:
        print(f"STT 전사 실패: {e}")
        raise HTTPException(status_code=500, detail=f"STT 전사 실패: {str(e)}")

    # 3. 전사 결과를 txt 파일로도 저장
    base_name = os.path.splitext(audio_info["file_name"])[0]
    txt_filename = f"{base_name}.txt"
    txt_path = os.path.join(DOWNLOADS_DIR, txt_filename)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(stt_result["text"])

    return {
        "success": True,
        "video": {
            "title": audio_info["title"],
            "uploader": audio_info["uploader"],
            "thumbnail": audio_info["thumbnail"],
            "duration_str": audio_info["duration_str"],
        },
        "audio": {
            "file_name": audio_info["file_name"],
            "audio_url": f"/api/audio/{audio_info['file_name']}",
            "file_size_mb": round(audio_info["file_size_bytes"] / (1024 * 1024), 2),
        },
        "transcript": {
            "text": stt_result["text"],
            "char_count": stt_result["char_count"],
            "word_count": stt_result["word_count"],
            "txt_download_url": f"/api/download-txt/{txt_filename}",
        },
    }


@app.get("/api/audio/{filename}")
async def get_audio(filename: str):
    """다운로드된 오디오 파일을 브라우저에서 스트리밍 재생합니다."""
    file_path = os.path.join(DOWNLOADS_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="오디오 파일을 찾을 수 없습니다.")

    ext = filename.split(".")[-1].lower()
    mime_type = "audio/mp4" if ext == "m4a" else f"audio/{ext}"
    return FileResponse(file_path, media_type=mime_type, filename=filename)


@app.get("/api/download-txt/{filename}")
async def download_txt(filename: str):
    """전사된 텍스트 파일을 다운로드합니다."""
    file_path = os.path.join(DOWNLOADS_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="텍스트 파일을 찾을 수 없습니다.")
    return FileResponse(file_path, media_type="text/plain; charset=utf-8", filename=filename)


if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("🚀 YouTube Audio Transcriber 웹 서비스 시작")
    print("🌐 브라우저 접속 주소: http://127.0.0.1:8000")
    print("=" * 60)
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
