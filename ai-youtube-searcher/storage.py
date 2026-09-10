import csv
import json
import os
from datetime import datetime
from downloader import extract_video_id

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
CSV_PATH = os.path.join(DATA_DIR, "transcripts.csv")

os.makedirs(DATA_DIR, exist_ok=True)

CSV_FIELDNAMES = [
    "video_id",
    "url",
    "title",
    "uploader",
    "duration",
    "duration_str",
    "thumbnail",
    "transcript_text",
    "segments_json",
    "created_at",
]


def init_csv_if_not_exists():
    """CSV 파일이 없으면 헤더를 포함하여 새로 생성합니다."""
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, mode="w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
            writer.writeheader()


def get_cached_transcript(url: str) -> dict | None:
    """
    유튜브 URL 또는 Video ID를 기반으로 이미 저장된 트랜스크립트가 있는지 CSV에서 검색합니다.
    존재할 경우 video 메타데이터와 segments 리스트를 복원하여 반환합니다.
    """
    init_csv_if_not_exists()
    target_id = extract_video_id(url)
    if not target_id:
        return None

    try:
        with open(CSV_PATH, mode="r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("video_id") == target_id or row.get("url") == url:
                    # segments_json 파싱
                    segments = []
                    raw_segments = row.get("segments_json", "")
                    if raw_segments:
                        try:
                            segments = json.loads(raw_segments)
                        except Exception:
                            segments = []

                    return {
                        "from_cache": True,
                        "video": {
                            "id": row.get("video_id"),
                            "title": row.get("title", ""),
                            "uploader": row.get("uploader", ""),
                            "thumbnail": row.get("thumbnail", ""),
                            "duration": int(row.get("duration", 0) or 0),
                            "duration_str": row.get("duration_str", "00:00"),
                        },
                        "segments": segments,
                        "transcript_text": row.get("transcript_text", ""),
                        "created_at": row.get("created_at", ""),
                    }
    except Exception as e:
        print(f"CSV 캐시 조회 중 오류 발생: {e}")

    return None


def save_transcript_to_csv(
    url: str,
    video_info: dict,
    segments: list[dict],
) -> None:
    """
    추출된 유튜브 정보와 트랜스크립트 세그먼트를 CSV 파일에 저장합니다.
    """
    init_csv_if_not_exists()
    video_id = video_info.get("id") or extract_video_id(url)

    # 이미 동일한 video_id가 존재하는지 확인
    existing = get_cached_transcript(url)
    if existing:
        print(f"[CSV Storage] 이미 저장된 영상입니다: {video_id}")
        return

    # 순수 텍스트 생성
    transcript_text = "\n".join([f"[{s.get('time', '00:00')}] {s.get('text', '')}" for s in segments])

    row = {
        "video_id": video_id,
        "url": url,
        "title": video_info.get("title", ""),
        "uploader": video_info.get("uploader", ""),
        "duration": video_info.get("duration", 0),
        "duration_str": video_info.get("duration_str", "00:00"),
        "thumbnail": video_info.get("thumbnail", ""),
        "transcript_text": transcript_text,
        "segments_json": json.dumps(segments, ensure_ascii=False),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    try:
        with open(CSV_PATH, mode="a", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
            writer.writerow(row)
        print(f"[CSV Storage] 트랜스크립트 저장 완료 -> {CSV_PATH}")
    except Exception as e:
        print(f"[CSV Storage] 트랜스크립트 저장 실패: {e}")
