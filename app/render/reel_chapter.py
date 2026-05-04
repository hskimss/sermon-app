"""Sermon transcript → 3-4 chapter 자동 분할 (Gemma 4 narrative arc)."""
import requests, json
from pathlib import Path

GEMMA_URL = "http://192.168.1.111:11434/api/chat"
GEMMA_MODEL = "gemma4:26b"

CHAPTER_SCHEMA = {
    "type": "object",
    "properties": {
        "chapters": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "start_sec": {"type": "number"},
                    "end_sec": {"type": "number"},
                    "summary_short": {"type": "string"},  # 50자 이내
                    "key_quote": {"type": "string"}  # 30자 이내
                },
                "required": ["title", "start_sec", "end_sec", "summary_short", "key_quote"]
            }
        }
    },
    "required": ["chapters"]
}


def split_chapters(transcript: dict, target_count: int = 3) -> list:
    segs = transcript.get("segments", [])
    text = "\n".join(f"[{s['start']:.1f}s] {s['text']}" for s in segs)

    prompt = f"""
설교 transcript를 {target_count}개의 chapter로 분할.
각 chapter:
- title: 5-10자 (예: "구원의 약속", "심판의 날")
- start_sec, end_sec: 시작/끝 timestamp
- summary_short: 한 줄 요약 (50자)
- key_quote: 인용 가능한 핵심 1줄 (30자)

TRANSCRIPT:
{text}
"""
    r = requests.post(GEMMA_URL, json={
        "model": GEMMA_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "think": False,
        "format": CHAPTER_SCHEMA,
        "stream": False,
        "options": {"temperature": 0.0, "repeat_penalty": 1.3, "num_predict": 2000}
    }, timeout=120)
    return json.loads(r.json()["message"]["content"])["chapters"]


def split_chapters_fallback(transcript: dict, target_count: int = 3) -> list:
    """Gemma 실패 시 — segments duration 균등 분할."""
    segs = transcript.get("segments", [])
    if not segs:
        total = float(transcript.get("duration", 180))
        step = total / target_count
        return [
            {
                "title": f"Chapter {i+1}",
                "start_sec": round(i * step, 1),
                "end_sec": round((i + 1) * step, 1),
                "summary_short": f"Chapter {i+1}",
                "key_quote": "",
            }
            for i in range(target_count)
        ]

    total_start = float(segs[0].get("start", 0))
    total_end = float(segs[-1].get("end", segs[-1].get("start", 0) + 5))
    total_dur = total_end - total_start
    step = total_dur / target_count
    chapters = []
    for i in range(target_count):
        s = total_start + i * step
        e = total_start + (i + 1) * step
        # find representative text from segments in range
        texts = [sg.get("text", "") for sg in segs
                 if float(sg.get("start", 0)) >= s and float(sg.get("start", 0)) < e]
        snippet = " ".join(texts)[:30].strip() or f"Chapter {i+1}"
        chapters.append({
            "title": f"Chapter {i+1}",
            "start_sec": round(s, 1),
            "end_sec": round(e, 1),
            "summary_short": snippet,
            "key_quote": snippet[:30],
        })
    return chapters


def get_chapters(transcript: dict, target_count: int = 3) -> list:
    """Gemma 4 호출 → 실패 시 fallback 균등분할."""
    try:
        return split_chapters(transcript, target_count)
    except Exception as e:
        print(f"[reel_chapter] Gemma 실패: {e} — fallback 균등분할")
        return split_chapters_fallback(transcript, target_count)
