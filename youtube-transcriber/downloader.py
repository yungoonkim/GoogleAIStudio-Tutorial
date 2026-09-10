import os
import re
import yt_dlp


def sanitize_filename(name: str) -> str:
    """파일명에서 윈도우/리눅스 특수문자를 안전하게 제거합니다."""
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()


def get_video_info(url: str) -> dict:
    """유튜브 URL로부터 영상 기본 정보(제목, 썸네일, 채널명, 재생길이 등)를 추출합니다."""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "id": info.get("id"),
            "title": info.get("title", "알 수 없는 제목"),
            "uploader": info.get("uploader", "알 수 없는 채널"),
            "thumbnail": info.get("thumbnail"),
            "duration": info.get("duration", 0),
            "duration_str": format_duration(info.get("duration", 0)),
            "webpage_url": info.get("webpage_url", url),
        }


def format_duration(seconds: int) -> str:
    """초 단위 시간을 MM:SS 또는 HH:MM:SS 형식 문자열로 변환합니다."""
    if not seconds:
        return "00:00"
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def download_audio(url: str, output_dir: str = "downloads") -> dict:
    """
    유튜브 URL에서 최적의 오디오 스트림을 다운로드합니다.
    ffmpeg 없이도 m4a 또는 webm 포맷의 원시 오디오 스트림을 안전하게 다운로드합니다.
    """
    os.makedirs(output_dir, exist_ok=True)

    # 1. 영상 정보 먼저 조회
    info = get_video_info(url)
    video_id = info["id"]
    safe_title = sanitize_filename(info["title"])[:50]
    out_tmpl = os.path.join(output_dir, f"{video_id}_%(ext)s")

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": out_tmpl,
        "quiet": True,
        "no_warnings": True,
        "overwrites": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        download_info = ydl.extract_info(url, download=True)
        ext = download_info.get("ext", "m4a")
        downloaded_file = os.path.join(output_dir, f"{video_id}.{ext}")

        # 만약 확장자 차이 등으로 파일명을 못 찾았을 경우 폴더 검색
        if not os.path.exists(downloaded_file):
            for candidate in os.listdir(output_dir):
                if candidate.startswith(video_id):
                    downloaded_file = os.path.join(output_dir, candidate)
                    ext = candidate.split(".")[-1]
                    break

    # MIME 타입 매핑
    mime_map = {
        "m4a": "audio/mp4",
        "webm": "audio/webm",
        "mp3": "audio/mp3",
        "wav": "audio/wav",
        "aac": "audio/aac",
        "ogg": "audio/ogg",
    }
    mime_type = mime_map.get(ext.lower(), "audio/mp4")

    return {
        "title": info["title"],
        "uploader": info["uploader"],
        "thumbnail": info["thumbnail"],
        "duration_str": info["duration_str"],
        "duration": info["duration"],
        "file_path": downloaded_file,
        "file_name": os.path.basename(downloaded_file),
        "mime_type": mime_type,
        "file_size_bytes": os.path.getsize(downloaded_file) if os.path.exists(downloaded_file) else 0,
    }
