import os
import re
import yt_dlp


def extract_video_id(url: str) -> str:
    """다양한 형식의 유튜브 URL에서 11자리 Video ID를 정규식으로 추출합니다."""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'youtu\.be\/([0-9A-Za-z_-]{11})',
        r'embed\/([0-9A-Za-z_-]{11})',
        r'shorts\/([0-9A-Za-z_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return ""


def sanitize_filename(name: str) -> str:
    """윈도우 및 리눅스에서 안전한 파일명으로 변환합니다."""
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()


def format_duration(seconds: int) -> str:
    """초 단위 시간을 MM:SS 또는 HH:MM:SS 형식으로 변환합니다."""
    if not seconds:
        return "00:00"
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def get_video_info(url: str) -> dict:
    """유튜브 URL로부터 메타데이터(ID, 제목, 채널명, 썸네일, 재생시간)를 추출합니다."""
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        video_id = info.get("id") or extract_video_id(url)
        return {
            "id": video_id,
            "title": info.get("title", "알 수 없는 제목"),
            "uploader": info.get("uploader", "알 수 없는 채널"),
            "thumbnail": info.get("thumbnail"),
            "duration": info.get("duration", 0),
            "duration_str": format_duration(info.get("duration", 0)),
            "webpage_url": info.get("webpage_url", url),
        }


def download_audio(url: str, output_dir: str = "downloads") -> dict:
    """
    유튜브 영상에서 최고 음질의 오디오 스트림(m4a/webm)을 다운로드합니다.
    외부 ffmpeg 설치가 없어도 안전하게 원본 오디오 스트림을 추출합니다.
    """
    os.makedirs(output_dir, exist_ok=True)

    info = get_video_info(url)
    video_id = info["id"]
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

        if not os.path.exists(downloaded_file):
            for candidate in os.listdir(output_dir):
                if candidate.startswith(video_id):
                    downloaded_file = os.path.join(output_dir, candidate)
                    ext = candidate.split(".")[-1]
                    break

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
        "video_id": video_id,
        "title": info["title"],
        "uploader": info["uploader"],
        "thumbnail": info["thumbnail"],
        "duration": info["duration"],
        "duration_str": info["duration_str"],
        "file_path": downloaded_file,
        "file_name": os.path.basename(downloaded_file),
        "mime_type": mime_type,
        "file_size_bytes": os.path.getsize(downloaded_file) if os.path.exists(downloaded_file) else 0,
    }
