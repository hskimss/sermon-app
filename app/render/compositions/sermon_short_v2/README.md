# sermon_short_v2 — Inject Contract

> 60s vertical (1080×1920) sermon short for **A Church London**.
> 5-scene composition with graceful degradation. v1 → v2 upgrade per `CLAUDE_DESIGN_BRIEF.md`.

---

## Files

- `index.html` — single-file composition (CSS + GSAP timeline)
- `preview.html` — local preview wrapper (50% scale iframe + JSON injector)
- `DESIGN.md` — design choices + Persona #3 rationale
- `README.md` — **this file** (inject contract for sermon-app)

---

## Inject Points (server-side substitution)

`hf-server` substitutes `{{KEY}}` placeholders before render. Two categories:

### Static text (single value)

| Placeholder | Type | Required | Example |
|---|---|---|---|
| `{{COMPOSITION_ID}}` | string | ✅ | `"abc123de"` (render_id) |
| `{{TOTAL_SEC}}` | number | ✅ | `60` |
| `{{AUDIO_URL}}` | URL | ✅ | `"http://100.89.99.106:5001/api/job/<jid>/audio"` |
| `{{MUSIC_BED_URL}}` | URL | ⚠ optional | `""` (empty string is OK) |
| `{{HOOK_TEXT}}` | string | ✅ | `"너는 예수님을 어떻게 대했냐"` |
| `{{HOOK_ARCHETYPE}}` | string | ✅ | `"질문"` / `"간증"` / `"대조"` |
| `{{AUSTERITY_PHRASE}}` | string | ✅ | `"주님 앞에 잠잠하라"` |
| `{{SCRIPTURE_REF}}` | string | ⚠ | `"요한복음 3:16"` |
| `{{SCRIPTURE_TEXT}}` | string | ⚠ | `"하나님이 세상을 …"` |
| `{{SCRIPTURE_TRANSLATION}}` | string | ⚠ | `"개역개정"` / `"kjv"` |

### JSON arrays (literal JSON injection — be careful with quoting)

| Placeholder | Type | Schema |
|---|---|---|
| `{{WORDS_JSON}}` | array | `[{"word":str,"start":num,"end":num,"is_emphasis":bool}, …]` |
| `{{SCRIPTURE_REFS_JSON}}` | array | `[{"book":str,"chapter":num,"verse_start":num,"verse_end":num,"text":str,"translation":str,"appears_at_sec":num}, …]` |

Both arrays may be `[]` — graceful degradation kicks in.

---

## Graceful Degradation

| Inputs | Visible scenes |
|---|---|
| Words + Scripture | Hook → Scripture → Body → Austerity → Outro (all 5) |
| Words only | Hook → Body → Austerity → Outro |
| Scripture only | Hook → Scripture → Austerity → Outro |
| Neither | Hook → Austerity → Outro |

Layout never breaks. Empty captions container collapses, scripture card hidden.

---

## How sermon-app populates this

```python
# app/render/payload.py::build_short_payload_v2

payload = {
    "composition": "sermon_short_v2",
    "format": "9:16",
    "audio_url": f"{base}/api/job/{job_id}/audio",
    "audio_clip": {"start_sec": clip["start_sec"],
                   "duration": clip["end_sec"] - clip["start_sec"]},
    "words": _filter_words_in_clip(transcript, clip, emphasis_ids),
    "scripture_refs": detect_scripture_refs(transcript, clip, lookup=True),
    "hook_text": " ".join(w["word"] for w in words[:8]).strip(),
    "hook_archetype": clip.get("hook_archetype") or "질문",
    "austerity_phrase": clip.get("austerity_phrase") or "주님 앞에 잠잠하라",
    "music_bed_url": "",
    ...
}
```

`hf-server`'s `_render_sync()` then maps payload keys to placeholders:

```python
repl = {
    "{{COMPOSITION_ID}}": render_id,
    "{{TOTAL_SEC}}": str(payload["audio_clip"]["duration"]),
    "{{AUDIO_URL}}": payload["audio_url"],
    "{{MUSIC_BED_URL}}": payload.get("music_bed_url", ""),
    "{{HOOK_TEXT}}": payload["hook_text"],
    "{{HOOK_ARCHETYPE}}": payload["hook_archetype"],
    "{{AUSTERITY_PHRASE}}": payload["austerity_phrase"],
    "{{SCRIPTURE_REF}}": refs[0].get("...") if refs else "",
    "{{SCRIPTURE_TEXT}}": refs[0].get("text", "") if refs else "",
    "{{SCRIPTURE_TRANSLATION}}": refs[0].get("translation", "") if refs else "",
    "{{WORDS_JSON}}": json.dumps(payload["words"], ensure_ascii=False),
    "{{SCRIPTURE_REFS_JSON}}": json.dumps(payload["scripture_refs"], ensure_ascii=False),
}
```

---

## Local Preview

```bash
cd app/render/compositions/sermon_short_v2
python3 -m http.server 5556 &
open http://localhost:5556/preview.html
```

Edit the JSON in the right panel, click `▶ Inject + Reload` to see changes.

---

## Lint

```bash
cd app/render/compositions/sermon_short_v2
npx hyperframes lint .
```

Target: 0 errors. v0.4.42 checks: composition_id present, timeline registered,
`__hyperframes_ready` flag, `data-duration` numeric, scenes don't overflow.

---

## Render via hf-server

```bash
curl -X POST http://100.104.121.7:8770/render -H 'Content-Type: application/json' -d '{
  "composition": "sermon_short_v2",
  "format": "9:16",
  "audio_clip": {"start_sec":0, "duration":60},
  "hook_text": "너는 예수님을 어떻게 대했냐",
  "hook_archetype": "질문",
  "austerity_phrase": "주님 앞에 잠잠하라",
  "words": [...],
  "scripture_refs": [...]
}'
```

Then `GET /render/<id>/status` until `ready`, then `GET /output/<id>.mp4`.
