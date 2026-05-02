"""sermon-app — Local Gemma 4 wrapper.

Reasons we don't use local_llm_client.LLM.chat directly:
- It prepends "<no_think>" to the message but does NOT pass the native
  `think: false` flag, so Gemma 4 still consumes tokens on hidden reasoning
  and content can come back empty.

This module talks to Ollama's native /api/chat with the proper flags,
plus provides sermon-specific helpers.
"""
from __future__ import annotations
import json
import os
import re
import requests
from typing import Optional

LLM_HOST = os.getenv("HP_Z2_LLM", "http://100.104.121.7:11434")
DEFAULT_MODEL = os.getenv("SERMON_LLM_MODEL", "gemma4:26b")
REASON_MODEL = os.getenv("SERMON_LLM_REASON_MODEL", "gemma4:31b")
EMBED_MODEL = "bge-m3"


def chat(system: str, user: str, *,
         model: Optional[str] = None,
         think: bool = False,
         temperature: float = 0.3,
         max_tokens: int = 2000,
         timeout: int = 300) -> str:
    """Call Gemma 4 with proper think flag honoring.

    think=False : skip internal CoT, fast & deterministic. Best for
                  classification, extraction, JSON tasks.
    think=True  : full reasoning. Best for clip selection, judgement.
                  Output `content` may be empty until reasoning finishes,
                  so allocate at least 1500 tokens for max_tokens.
    """
    payload = {
        "model": model or DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "think": think,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
    }
    r = requests.post(f"{LLM_HOST}/api/chat", json=payload, timeout=timeout)
    r.raise_for_status()
    return r.json()["message"]["content"]


def chat_json(system: str, user: str, **kw) -> dict:
    """Same as chat() but parses JSON from the response.
    
    Forces think=False (deterministic) and low temperature unless overridden.
    """
    kw.setdefault("think", False)
    kw.setdefault("temperature", 0.0)
    sys_with_schema = system + "\n\nReply with VALID JSON only. No markdown fences, no prose."
    out = chat(sys_with_schema, user, **kw)
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", out)
        if m:
            return json.loads(m.group(0))
        raise ValueError(f"Not JSON. Got: {out[:300]}")


def embed(text: str) -> list:
    r = requests.post(f"{LLM_HOST}/api/embeddings",
                      json={"model": EMBED_MODEL, "prompt": text},
                      timeout=30)
    r.raise_for_status()
    return r.json()["embedding"]


def health() -> bool:
    try:
        return requests.get(f"{LLM_HOST}/api/tags", timeout=3).status_code == 200
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────────
# Sermon-app specific helpers
# ─────────────────────────────────────────────────────────────────

def emphasis_words(transcript_chunk: str, *, max_words: int = 6) -> list:
    """S2 — pick emphasis words for caption rendering.
    
    Returns list of words to bold/color. For Korean Christian sermon:
    nouns, scripture refs, names of God/Jesus/Christ, contrast words.
    """
    sys_p = (
        "You are a Korean sermon caption stylist. "
        "Pick the 1-3 MOST emphasis-worthy words from the input transcript chunk. "
        "Prefer: subject of action verbs, scripture refs, names of God (하나님/예수/그리스도/주님), "
        "emotionally loaded nouns, contrast words (그러나/하지만/그러므로). "
        "Avoid: articles, conjunctions, fillers (음/어/그/저)."
    )
    schema = '{"emphasis": ["word1", "word2"]}'
    out = chat_json(sys_p + f"\n\nFormat: {schema}",
                    transcript_chunk, max_tokens=200)
    words = out.get("emphasis", [])
    return words[:max_words]


def clip_candidates(transcript_segments: list, *, n_clips: int = 5,
                    use_reasoning: bool = True) -> list:
    """S1 — pick top N short clip candidates from a sermon transcript.
    
    transcript_segments: list of {start, end, text}
    Returns list of {start_sec, end_sec, hook_archetype, hook_text,
                     why_it_works, virality_score (1-10)}.
    """
    # Compress transcript: timestamp + text only, no word arrays
    compressed = "\n".join(
        f"[{s['start']:.0f}-{s['end']:.0f}] {s['text']}"
        for s in transcript_segments
    )
    sys_p = (
        "You are a faceless Christian-content YouTube Shorts producer. "
        "Find the TOP %d clips (45-75 sec each) from the sermon transcript below. "
        "Each clip MUST: open with a hook (contradiction / authority quote / "
        "rhetorical question / direct challenge / numbered listicle / "
        "in-medias-res testimony), contain a self-contained narrative arc, "
        "end on a landing line, stand alone without context. "
        "Avoid denominationally divisive cuts."
    ) % n_clips
    schema = (
        '{"clips":['
        '{"start_sec":int,"end_sec":int,'
        '"hook_archetype":"contradiction|authority|question|challenge|listicle|testimony",'
        '"hook_text":str,"why_it_works":str,"virality_score":1-10}]}'
    )
    out = chat_json(
        sys_p + f"\n\nReturn JSON: {schema}",
        compressed,
        model=REASON_MODEL if use_reasoning else DEFAULT_MODEL,
        think=use_reasoning,
        max_tokens=4000,
        timeout=600,
    )
    return out.get("clips", [])


def clean_transcript_text(text: str) -> str:
    """S4 — light Korean speech cleanup. Removes 'um', 'eh', stutters,
    fixes obvious typos. Preserves meaning. Word count ~unchanged.
    """
    out = chat(
        system=("Korean speech transcript cleanup. Remove fillers like "
                "'음', '어', '그', '저', stutters, repetitions. Fix obvious "
                "typos. PRESERVE original word count and meaning. "
                "Output only the cleaned text, no commentary."),
        user=text,
        think=False,
        temperature=0.1,
        max_tokens=len(text) * 2 + 100,
    )
    return out.strip()



def rearrange_for_arc(clips: list) -> list:
    """Level 1 — Reorder clips for narrative arc.
    
    Does NOT modify clip content (start/end times preserved). Only changes order.
    Strongest hook → first; theological climax → middle; application/landing → last.
    
    Returns list of clips in new order. If LLM fails, returns input unchanged.
    """
    if not clips or len(clips) < 2:
        return list(clips)
    
    # Compress for LLM context
    compact = [
        {"i": i, "archetype": c.get("hook_archetype", "?"),
         "score": c.get("virality_score", 0),
         "hook": (c.get("hook_text") or "")[:120],
         "duration": int(c.get("end_sec", 0) - c.get("start_sec", 0))}
        for i, c in enumerate(clips)
    ]
    sys_p = (
        "You are a Christian sermon highlight-reel narrative arc designer. "
        "You will rearrange a list of sermon clips into the most compelling viewing order. "
        "RULES:\n"
        "1. The clip with the strongest hook (curiosity, contradiction, direct challenge) goes FIRST — to capture attention.\n"
        "2. The clip with the deepest theological revelation or emotional climax goes in the MIDDLE.\n"
        "3. The clip with the clearest application/landing line goes LAST.\n"
        "4. The remaining clips fill the build-up between hook and climax.\n"
        "5. NEVER drop or duplicate clips. NEVER modify clip content.\n"
        "Return only the reordered list of clip indices (i values), as JSON."
    )
    schema = '{"order": [int]}'
    try:
        out = chat_json(
            sys_p + f"\n\nReturn JSON: {schema}",
            json.dumps(compact, ensure_ascii=False),
            think=False,
            temperature=0.0,
            max_tokens=300,
            timeout=120,
        )
        order = out.get("order", [])
        if not order or len(order) != len(clips) or set(order) != set(range(len(clips))):
            return list(clips)
        return [clips[i] for i in order]
    except Exception:
        return list(clips)
