"""HyperFrames 렌더 요청 payload 빌더.

설계 문서: HYPERFRAMES_DESIGN.md §4.1
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .scripture import detect_scripture_refs

# Tailscale 안에서 HP가 sermon-app에 audio fetch할 때 쓸 base url
SERMON_APP_BASE = os.getenv(
    "SERMON_APP_BASE_URL", "http://mac-tailscale:5001"
)
DEFAULT_HOUSE_STYLE = "a_church_london_v1"


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _filter_words_in_clip(
    transcript: dict, clip: dict, emphasis_ids: set[str]
) -> list[dict]:
    """clip 범위 안의 word를 clip-local 시각으로 변환 + emphasis flag 부여."""
    in_s = float(clip["start_sec"])
    out_s = float(clip["end_sec"])
    out: list[dict] = []
    for sIdx, seg in enumerate(transcript.get("segments", []) or []):
        s_start = float(seg.get("start", 0))
        s_end = float(seg.get("end", 0))
        if s_end < in_s or s_start > out_s:
            continue
        for wIdx, w in enumerate(seg.get("words", []) or []):
            try:
                ws = float(w.get("start", 0))
                we = float(w.get("end", 0))
            except (TypeError, ValueError):
                continue
            if ws >= in_s and we <= out_s:
                wid = f"s{sIdx}w{wIdx}"
                out.append({
                    "wid": wid,
                    "seg_idx": sIdx,
                    "word_idx": wIdx,
                    "word": (w.get("word") or "").strip(),
                    # clip-local 시각으로 rebase
                    "start": round(ws - in_s, 3),
                    "end": round(we - in_s, 3),
                    "is_emphasis": wid in emphasis_ids,
                })
    return out


def _segments_in_clip(transcript: dict, clip: dict) -> list[dict]:
    """편집 단위로 사용할 segment 텍스트도 함께 보냄 (자막 줄바꿈 가이드)."""
    in_s = float(clip["start_sec"])
    out_s = float(clip["end_sec"])
    rows = []
    for sIdx, seg in enumerate(transcript.get("segments", []) or []):
        s_start = float(seg.get("start", 0))
        s_end = float(seg.get("end", 0))
        if s_end < in_s or s_start > out_s:
            continue
        rows.append({
            "seg_idx": sIdx,
            "start": round(max(s_start, in_s) - in_s, 3),
            "end": round(min(s_end, out_s) - in_s, 3),
            "text": (seg.get("text") or "").strip(),
        })
    return rows


def build_short_payload(
    job_id: str,
    clip: dict,
    *,
    jobs_dir: Path | str,
    composition: str = "sermon_short_v1",
    fmt: str = "9:16",
    quality: str = "1080p",
    house_style: str = DEFAULT_HOUSE_STYLE,
    sermon_app_base: str | None = None,
    callback_url: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict:
    """sermon-app 캐시(transcript + emphasis)를 읽어 HyperFrames 요청 body를 구성.

    Args:
        job_id: sermon-app job id
        clip: {"start_sec": float, "end_sec": float, "hook_archetype"?: str, ...}
        jobs_dir: sermon-app `JOBS_DIR` 경로
        composition: HyperFrames 컴포지션 ID (sermon_short_v1 / sermon_reel_v1 등)
        fmt: "9:16" / "16:9"
        quality: "720p" / "1080p"
        house_style: CSS variable preset
        sermon_app_base: HP가 audio fetch할 base URL (default env SERMON_APP_BASE_URL)
        callback_url: 렌더 완료 콜백 (없으면 polling)
        extra: 컴포지션별 추가 필드 병합

    Returns:
        HP `/render` POST 본문.
    """
    jobs_dir = Path(jobs_dir)
    job_dir = jobs_dir / job_id
    transcript_path = job_dir / "transcript.json"
    if not transcript_path.exists():
        raise FileNotFoundError(f"transcript 없음: {transcript_path}")
    transcript = _read_json(transcript_path)

    emphasis_path = job_dir / "llm_emphasis.json"
    emphasis_ids: set[str] = set()
    if emphasis_path.exists():
        try:
            emphasis_ids = set(_read_json(emphasis_path).get("emphasis_ids", []))
        except Exception:
            emphasis_ids = set()

    in_s = float(clip["start_sec"])
    out_s = float(clip["end_sec"])
    duration = max(0.5, out_s - in_s)

    words = _filter_words_in_clip(transcript, clip, emphasis_ids)
    segs = _segments_in_clip(transcript, clip)
    refs = detect_scripture_refs(transcript, clip)

    base = (sermon_app_base or SERMON_APP_BASE).rstrip("/")

    body: dict[str, Any] = {
        "composition": composition,
        "format": fmt,
        "quality": quality,
        "house_style": house_style,
        "audio_url": f"{base}/api/job/{job_id}/audio",
        "audio_clip": {
            "start_sec": round(in_s, 3),
            "duration": round(duration, 3),
        },
        "clip_range": {"in_sec": round(in_s, 3), "out_sec": round(out_s, 3)},
        "words": words,
        "transcript_segments": segs,
        "scripture_refs": refs,
        "meta": {
            "job_id": job_id,
            "hook_archetype": clip.get("hook_archetype"),
            "language": transcript.get("language"),
            "source_duration": transcript.get("duration"),
        },
    }
    if callback_url:
        body["callback_url"] = callback_url
    if extra:
        body.update(extra)
    return body
