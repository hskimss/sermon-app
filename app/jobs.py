from __future__ import annotations
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs, urlparse

JOBS_DIR = Path(__file__).resolve().parent.parent / "jobs"


def extract_youtube_id(url: str) -> str | None:
    parsed = urlparse(url)
    host = parsed.hostname or ""
    if host == "youtu.be":
        vid = parsed.path.lstrip("/")
        return vid if vid else None
    if host in ("www.youtube.com", "youtube.com", "m.youtube.com"):
        qs = parse_qs(parsed.query)
        if qs.get("v"):
            return qs["v"][0]
        parts = parsed.path.strip("/").split("/")
        if len(parts) >= 2 and parts[0] in ("live", "shorts", "embed", "v"):
            return parts[1]
    return None


def cache_key(url: str, start_sec: int, end_sec: int, media_type: str = "video") -> str:
    yt_id = extract_youtube_id(url) or url
    raw = f"{yt_id}:{start_sec}:{end_sec}:{media_type}"
    return hashlib.sha1(raw.encode()).hexdigest()


def find_or_create_job(
    youtube_url: str,
    start_sec: int,
    end_sec: int,
    mode: str,
    target_sec: int | None,
    media_type: str = "video",
) -> tuple[str, bool]:
    ck = cache_key(youtube_url, start_sec, end_sec, media_type)
    JOBS_DIR.mkdir(parents=True, exist_ok=True)

    for meta_path in JOBS_DIR.glob("*/meta.json"):
        try:
            meta = json.loads(meta_path.read_text())
            if meta.get("cache_key") == ck:
                return meta["job_id"], True
        except (json.JSONDecodeError, KeyError):
            continue

    yt_id = extract_youtube_id(youtube_url) or "unknown"
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = "_audio" if media_type == "audio" else ""
    job_id = f"{ts}_{yt_id}{suffix}"
    job_dir = JOBS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    meta = {
        "cache_key": ck,
        "job_id": job_id,
        "youtube_url": youtube_url,
        "youtube_id": yt_id,
        "start_sec": start_sec,
        "end_sec": end_sec,
        "mode": mode,
        "target_sec": target_sec,
        "media_type": media_type,
        "phase": "queued",
        "created_at": datetime.now().isoformat(),
    }
    (job_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    return job_id, False


def get_job_status(job_id: str) -> dict | None:
    meta_path = JOBS_DIR / job_id / "meta.json"
    if not meta_path.exists():
        return None
    try:
        return json.loads(meta_path.read_text())
    except (json.JSONDecodeError, KeyError):
        return None
