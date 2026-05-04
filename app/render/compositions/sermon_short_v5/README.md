# sermon_short_v3 — SKILL.md 정석 재빌드

> **Authority**: HF SKILL.md (https://github.com/heygen-com/hyperframes/blob/main/skills/hyperframes/SKILL.md)
> **Authority**: `DESIGN.md` (Visual Identity Gate)
> **Replaces**: v2 (6번 시도 실패, single-file + absolute content + exit anim violations)

---

## File Map

```
sermon_short_v3/
├── DESIGN.md                            # Visual identity (Phase A gate)
├── README.md                            # This file
├── index.html                           # Root composition (NO <template>)
├── silent60.mp3                         # Audio placeholder for lint
└── compositions/
    ├── scene-hook.html                  # Scene 1 (0–6s)
    ├── scene-scripture.html             # Scene 2 (6–14s)
    ├── scene-body.html                  # Scene 3 (14–48s)  ← critical
    ├── scene-austerity.html             # Scene 4 (48–54s)
    └── scene-outro.html                 # Scene 5 (54–60s)
```

---

## SKILL.md Compliance Matrix

| Rule | v3 Compliance |
|------|---------------|
| `.scene-content` MUST fill via `width:100%; height:100%; padding; flex` | ✅ All 5 sub-comps use flex+padding (no `position:absolute` on content) |
| Reserve `position:absolute` for decoratives only | ✅ Only scripture-card decorative is `position:relative` (still flex inside) |
| NEVER exit animations except final scene | ✅ Only `scene-outro` has `gsap.to(opacity:0)` for soft fade-to-black |
| Sub-composition split via `data-composition-src` | ✅ Root is `data-composition-id="sermon_short_v3"` referencing 5 sub-comps |
| Visual Identity Gate (DESIGN.md before HTML) | ✅ DESIGN.md committed before any composition file |
| `tl.set()` on later clip elements (Rule #10) | ✅ scene-body's line swap uses `tl.set` inside timeline at correct time |
| Determinism (no Math.random/Date.now/repeat:-1) | ✅ |
| No `<br>` in content text | ✅ Natural wrap via `max-width: 920px` |
| Synchronous timeline construction | ✅ All 5 timelines built in plain IIFE, no async |
| No conflicting same-property animations | ✅ Each line/element has at most one entrance + optional `tl.set(opacity:0)` swap |
| Standalone uses no `<template>`, sub-comp uses `<template>` | ✅ `index.html` has no template; 5 sub-comps wrap in `<template id="…-template">` |

---

## Inject Contract

| Placeholder | Where | Type | Required |
|-------------|-------|------|----------|
| `{{HOOK_TEXT}}` | scene-hook | string | ✅ |
| `{{SCRIPTURE_REF}}` | scene-scripture | string (formatted "요한복음 3:16") | optional |
| `{{SCRIPTURE_TEXT}}` | scene-scripture | string | optional |
| `{{SCRIPTURE_TRANSLATION}}` | scene-scripture | string ("개역개정"/"kjv") | optional |
| `{{LINE_0_HTML}}` … `{{LINE_5_HTML}}` | scene-body | HTML (with `<span class="emphasis">`) | up to 6 lines |
| `{{LINE_TIMES_JSON}}` | scene-body | JSON `[{start, duration}, …]` body-local | matched length |
| `{{AUSTERITY_PHRASE}}` | scene-austerity | string (default "주님 앞에 잠잠하라") | ✅ |
| `{{HOOK_ARCHETYPE}}` | scene-outro | string ("질문" / "간증" / "대조") | ✅ |
| `{{AUDIO_URL_OR_SILENT}}` | root audio | URL or `silent60.mp3` | ✅ (default silent60.mp3) |
| `{{MUSIC_BED_URL_OR_SILENT}}` | root audio | URL or `silent60.mp3` | ✅ (default silent60.mp3) |

---

## sermon-app integration

`app/render/payload.py::build_short_payload_v3()` produces:

```python
{
  "composition": "sermon_short_v3",
  "audio_url": ...,
  "music_bed_url": "",
  "hook_text": "...",
  "hook_archetype": "질문",
  "austerity_phrase": "주님 앞에 잠잠하라",
  "scripture_refs": [...],         # first ref → SCRIPTURE_*
  "body_lines": [                  # 4-6 chunks of body window
    {"html": "...", "start": 0.0, "duration": 7.5}
  ]
}
```

`hf_server.py` substitutes placeholders before render.

---

## Lint + Validate

```bash
cd /home/quant/hyperframes-render
npx hyperframes lint compositions/sermon_short_v3
npx hyperframes validate compositions/sermon_short_v3
```

Target: **0 errors**, **0 critical warnings**. `composition_file_too_large` warning NOT applicable now (5 sub-comps, each < 200 lines).

---

## Render

```bash
curl -X POST http://100.104.121.7:8770/render \
  -H 'Content-Type: application/json' \
  -d '{"composition":"sermon_short_v3", ...}'
```
