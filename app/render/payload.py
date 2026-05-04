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
    "SERMON_APP_BASE_URL", "http://100.89.99.106:5001"
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
    # P3: 본문 lookup 포함 (BibleStore)
    refs = detect_scripture_refs(transcript, clip, lookup=True)

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


def _chunk_body_lines(
    transcript_segments: list[dict],
    body_window_start: float = 14.0,
    body_window_end: float = 48.0,
    emphasis_ids: set[str] | None = None,
    max_lines: int = 6,
) -> list[dict]:
    """transcript segments → 4-6 body lines (each ~5-9s).

    Returns: [{html, start (body-local), duration}]
    """
    emphasis_ids = emphasis_ids or set()

    body_segs = [
        s for s in (transcript_segments or [])
        if float(s.get("end", 0)) > body_window_start
        and float(s.get("start", 0)) < body_window_end
    ]
    if not body_segs:
        return []

    rows: list[dict] = []
    for si, seg in enumerate(body_segs):
        s_start = max(float(seg.get("start", 0)), body_window_start)
        s_end = min(float(seg.get("end", 0)), body_window_end)
        local_start = round(s_start - body_window_start, 3)
        local_dur = round(max(0.4, s_end - s_start), 3)

        # word-level emphasis -> inline span
        words_html: list[str] = []
        for wi, w in enumerate(seg.get("words", []) or []):
            wid_full = f"s{seg.get('seg_idx', si)}w{wi}"
            wid_alt = w.get("wid")
            word_text = (w.get("word") or "").strip()
            if not word_text:
                continue
            is_em = (wid_full in emphasis_ids) or (wid_alt in emphasis_ids)
            from html import escape as _esc
            esc = _esc(word_text)
            if is_em:
                words_html.append(f'<span class="emphasis">{esc}</span>')
            else:
                words_html.append(esc)

        if not words_html:
            from html import escape as _esc
            words_html.append(_esc((seg.get("text") or "").strip()))

        rows.append({
            "html": " ".join(words_html),
            "start": local_start,
            "duration": local_dur,
        })

    # Cap to max_lines — merge adjacent short segments if needed
    while len(rows) > max_lines:
        # find the shortest pair of adjacents and merge
        pairs = [(rows[i]["duration"] + rows[i+1]["duration"], i)
                 for i in range(len(rows) - 1)]
        pairs.sort()
        i = pairs[0][1]
        merged = {
            "html": rows[i]["html"] + " " + rows[i+1]["html"],
            "start": rows[i]["start"],
            "duration": round(rows[i]["duration"] + rows[i+1]["duration"], 3),
        }
        rows = rows[:i] + [merged] + rows[i+2:]

    return rows


def build_short_payload_v2(
    job_id: str,
    clip: dict,
    *,
    jobs_dir: Path | str,
    fmt: str = "9:16",
    quality: str = "1080p",
    house_style: str = DEFAULT_HOUSE_STYLE,
    sermon_app_base: str | None = None,
    callback_url: str | None = None,
    austerity_phrase: str | None = None,
    music_bed_url: str = "",
    extra: dict[str, Any] | None = None,
) -> dict:
    """sermon_short_v2 composition payload (5 scenes).

    DESIGN_BRIEF inject contract:
      hook_text, hook_archetype, austerity_phrase, music_bed_url
      + (재사용) audio_url, audio_clip, words, scripture_refs
    """
    # base는 v1과 동일 데이터 (transcript / emphasis / scripture)
    body = build_short_payload(
        job_id=job_id, clip=clip, jobs_dir=jobs_dir,
        composition="sermon_short_v2",
        fmt=fmt, quality=quality, house_style=house_style,
        sermon_app_base=sermon_app_base, callback_url=callback_url,
    )

    # v2 specific keys
    words = body.get("words") or []
    # 첫 8 단어 = hook
    hook_words = [w["word"] for w in words[:8] if w.get("word")]
    body["hook_text"] = " ".join(hook_words).strip()
    body["hook_archetype"] = (clip.get("hook_archetype") or "질문")[:8]
    body["austerity_phrase"] = (
        austerity_phrase
        or clip.get("austerity_phrase")
        or "주님 앞에 잠잠하라"
    )[:24]
    body["music_bed_url"] = music_bed_url or ""

    if extra:
        body.update(extra)
    return body


def build_short_payload_v4(
    job_id: str,
    clip: dict,
    *,
    jobs_dir: Path | str,
    fmt: str = "9:16",
    quality: str = "1080p",
    house_style: str = DEFAULT_HOUSE_STYLE,
    sermon_app_base: str | None = None,
    callback_url: str | None = None,
    austerity_phrase: str | None = None,
    music_bed_url: str = "",
    body_window: tuple[float, float] = (14.0, 48.0),
    extra: dict[str, Any] | None = None,
) -> dict:
    """sermon_short_v4 — JARVIS_HF_V4_TEMPLATE_FIX 정석 (sub-comp <template> wrapped)."""
    body = build_short_payload_v3(
        job_id=job_id, clip=clip, jobs_dir=jobs_dir,
        fmt=fmt, quality=quality, house_style=house_style,
        sermon_app_base=sermon_app_base, callback_url=callback_url,
        austerity_phrase=austerity_phrase, music_bed_url=music_bed_url,
        body_window=body_window,
    )
    body["composition"] = "sermon_short_v4"
    if extra:
        body.update(extra)
    return body


def build_short_payload_v3(
    job_id: str,
    clip: dict,
    *,
    jobs_dir: Path | str,
    fmt: str = "9:16",
    quality: str = "1080p",
    house_style: str = DEFAULT_HOUSE_STYLE,
    sermon_app_base: str | None = None,
    callback_url: str | None = None,
    austerity_phrase: str | None = None,
    music_bed_url: str = "",
    body_window: tuple[float, float] = (14.0, 48.0),
    extra: dict[str, Any] | None = None,
) -> dict:
    """sermon_short_v3 payload — SKILL.md 정석 5 sub-comp.

    v2와 동일 데이터 + body_lines (segment 단위 4-6 line chunk) +
    scripture_ref/text/translation 정적 추가.
    """
    body = build_short_payload_v2(
        job_id=job_id, clip=clip, jobs_dir=jobs_dir,
        fmt=fmt, quality=quality, house_style=house_style,
        sermon_app_base=sermon_app_base, callback_url=callback_url,
        austerity_phrase=austerity_phrase, music_bed_url=music_bed_url,
    )
    body["composition"] = "sermon_short_v3"

    # emphasis_ids (v3 chunk-time emphasis 적용)
    job_dir = Path(jobs_dir) / job_id
    emphasis_ids: set[str] = set()
    emp_path = job_dir / "llm_emphasis.json"
    if emp_path.exists():
        try:
            emphasis_ids = set(_read_json(emp_path).get("emphasis_ids", []))
        except Exception:
            emphasis_ids = set()

    body["body_lines"] = _chunk_body_lines(
        body.get("transcript_segments", []),
        body_window_start=body_window[0],
        body_window_end=body_window[1],
        emphasis_ids=emphasis_ids,
        max_lines=6,
    )

    refs = body.get("scripture_refs") or []
    if refs:
        r0 = refs[0]
        ve = r0.get("verse_end") or r0.get("verse_start")
        vs = r0.get("verse_start")
        chap = r0.get("chapter")
        book = r0.get("book") or ""
        if book and chap and vs:
            verse_range = f"{vs}" if (not ve or ve == vs) else f"{vs}-{ve}"
            body["scripture_ref"] = f"{book} {chap}:{verse_range}"
        else:
            body["scripture_ref"] = ""
        body["scripture_text"] = r0.get("text", "") or ""
        body["scripture_translation"] = r0.get("translation", "") or ""
    else:
        body["scripture_ref"] = ""
        body["scripture_text"] = ""
        body["scripture_translation"] = ""

    if extra:
        body.update(extra)
    return body


def build_reel_payload_v1(
    job_id: str,
    clip: dict,
    *,
    jobs_dir: Path | str,
    fmt: str = "9:16",
    quality: str = "1080p",
    house_style: str = DEFAULT_HOUSE_STYLE,
    sermon_app_base: str | None = None,
    callback_url: str | None = None,
    chapter_count: int = 3,
    church_name: str = "교회",
    sermon_cta: str = "예배에 오세요",
    music_bed_url: str = "",
    extra: dict[str, Any] | None = None,
) -> dict:
    """sermon_reel_v1 — 2-3분 멀티씬 reel payload.

    chapter 자동 분할 (Gemma 4 via reel_chapter.get_chapters).
    실패 시 균등 분할 fallback.
    """
    from .reel_chapter import get_chapters

    jobs_dir = Path(jobs_dir)
    job_dir = jobs_dir / job_id
    transcript_path = job_dir / "transcript.json"

    in_s = float(clip.get("start_sec", 0))
    out_s = float(clip.get("end_sec", 180))
    duration = max(1.0, out_s - in_s)

    base = (sermon_app_base or SERMON_APP_BASE).rstrip("/")
    audio_url = f"{base}/api/job/{job_id}/audio"

    # --- transcript + chapters ---
    transcript: dict = {}
    if transcript_path.exists():
        transcript = _read_json(transcript_path)

    chapters = get_chapters(transcript, target_count=chapter_count)

    # --- scripture from first detected ref ---
    refs = detect_scripture_refs(transcript, clip, lookup=True) if transcript else []
    scripture_ref = ""
    scripture_text = ""
    if refs:
        r0 = refs[0]
        ve = r0.get("verse_end") or r0.get("verse_start")
        vs = r0.get("verse_start")
        chap_num = r0.get("chapter")
        book = r0.get("book") or ""
        if book and chap_num and vs:
            vr = f"{vs}" if (not ve or ve == vs) else f"{vs}-{ve}"
            scripture_ref = f"{book} {chap_num}:{vr}"
        scripture_text = r0.get("text", "") or ""

    # --- hook text from first 8 words ---
    words_in_clip: list[dict] = []
    if transcript:
        emphasis_path = job_dir / "llm_emphasis.json"
        emphasis_ids: set[str] = set()
        if emphasis_path.exists():
            try:
                emphasis_ids = set(_read_json(emphasis_path).get("emphasis_ids", []))
            except Exception:
                emphasis_ids = set()
        words_in_clip = _filter_words_in_clip(transcript, clip, emphasis_ids)

    hook_words = [w["word"] for w in words_in_clip[:8] if w.get("word")]
    hook_text = " ".join(hook_words).strip() or "말씀이 시작됩니다"

    # --- chapter → template vars ---
    def _ch(i: int, key: str, fallback: str) -> str:
        if i < len(chapters):
            return str(chapters[i].get(key, fallback))
        return fallback

    template_vars: dict[str, str] = {
        "INTRO_LINE1": hook_text[:10],
        "INTRO_LINE2": _ch(0, "title", "오늘의"),
        "INTRO_HERO": _ch(0, "key_quote", "말씀")[:10],
        "CHAPTER_1_LABEL": _ch(0, "title", "Chapter 1"),
        "CH2_POINT_1": _ch(0, "title", "믿음"),
        "CH2_POINT_2": _ch(1, "title", "소망"),
        "CH2_POINT_3": _ch(2, "title", "사랑"),
        "CH3_SCENE_1": _ch(0, "summary_short", "은혜")[:12],
        "CH3_SCENE_2": _ch(1, "summary_short", "구원")[:12],
        "CH3_SCENE_3": _ch(2, "summary_short", "회복")[:12],
        "CH3_CAPTION": _ch(1, "key_quote", "하나님의 은혜")[:20],
        "KEY_QUOTE": _ch(1, "key_quote", "두려워하지 말라")[:20],
        "SCRIPTURE_REF": scripture_ref or "요한복음 3:16",
        "SCRIPTURE_TEXT": scripture_text[:40] or "하나님이 세상을 이처럼 사랑하사",
        "SCRIPTURE_SUMMARY": _ch(2, "summary_short", "말씀의 핵심")[:20],
        "CHURCH_NAME": church_name,
        "SERMON_TAGLINE": _ch(2, "key_quote", "말씀 안에서 새롭게")[:24],
        "SERMON_CTA": sermon_cta,
    }

    body: dict[str, Any] = {
        "composition": "sermon_reel_v1",
        "format": fmt,
        "quality": quality,
        "house_style": house_style,
        "audio_url": audio_url,
        "audio_clip": {
            "start_sec": round(in_s, 3),
            "duration": round(duration, 3),
        },
        "clip_range": {"in_sec": round(in_s, 3), "out_sec": round(out_s, 3)},
        "chapters": chapters,
        "template_vars": template_vars,
        "scripture_refs": refs,
        "music_bed_url": music_bed_url,
        "meta": {
            "job_id": job_id,
            "language": transcript.get("language") if transcript else None,
            "source_duration": transcript.get("duration") if transcript else None,
            "chapter_count": len(chapters),
        },
    }
    if callback_url:
        body["callback_url"] = callback_url
    if extra:
        body.update(extra)
    return body
