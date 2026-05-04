# Sermon Short v3 — Visual Identity (A Church London)

**Authority:** SKILL.md "Visual Identity Gate" — Before writing ANY composition HTML, this design is authoritative.

## Style Prompt (one paragraph)

A Church London 한국 디아스포라 교회의 60초 sermon short. **Bible Project minimalism × ESV/Crossway 활자 무게** 융합. Persona #3 *"reverent restraint"* 원칙 — 매 단어 강조하지 않고, 호흡 있는 segment 단위 자막. 모션은 안식, 색은 검소, 음악은 절제. Prosperity-gospel TV 톤 절대 금지, TikTok 메모 캡션 톤 금지, Higgsfield 하이퍼시네매틱 금지. Leather-bound study Bible 이 CGNTV의 모던 미니멀리즘과 만나는 지점.

---

## Colors

| Role | Hex | Use |
|------|-----|-----|
| Primary background (dark) | `#0E1116` | charcoal — default canvas (Hook / Body / Outro) |
| Pure black | `#000000` | austerity scene only |
| Secondary surface (light) | `#F5EFE0` | parchment — scripture card body |
| Primary text on dark | `#FFFFFF` | captions, hook |
| Primary text on light | `#1A2236` | scripture text on parchment (if used) |
| Scripture parchment alt | `#F5EFE0` | scripture card text on dark, semi-transparent overlay |
| Accent gold (border) | `#B8923A` | scripture card left border (solid, never gradient) |
| Accent gold (emphasis) | `#D4AF37` | caption emphasis word, outro archetype label |
| Lament accent (reserved) | `#6B1F26` | NOT USED in v3 — available for future v4 |

**Contrast (WCAG AA mandatory)**:
- White `#FFFFFF` on charcoal `#0E1116`: 19.4:1 ✅
- Gold emphasis `#D4AF37` on charcoal: 7.7:1 ✅
- Parchment `#F5EFE0` on charcoal: 16.5:1 ✅

---

## Typography

| Token | Font Family | Weight | Use |
|-------|-------------|--------|-----|
| `--font-ui` | `'Pretendard Variable', sans-serif` | 600 / 800 | Captions, hook, UI |
| `--font-scripture-ko` | `'Noto Serif KR', serif` | 600 | Scripture body (Korean) |
| `--font-scripture-en` | `'EB Garamond', serif` | 500 | Scripture body (English fallback) |
| `--font-title-ko` | `'Noto Serif KR', serif` | 700 | Austerity phrase, titles |

**Font sizes (1080×1920 vertical)**:
- Hook headline: 84px (Pretendard 800)
- Body caption line: 76px (Pretendard 800)
- Scripture body: 56px (Noto Serif KR 600)
- Scripture ref: 38px (Pretendard 700, gold)
- Austerity phrase: 72px (Noto Serif KR 700)
- Outro brand: 30px (Pretendard 600, opacity 0.7)
- Outro archetype label: 28px (Pretendard 600, gold, uppercase letter-spacing 0.12em)

**Word break (mandatory)**: ALL Korean text uses `word-break: keep-all`. Whitespace breaks only at spaces.

**Stroke (mandatory)**: 8-direction `text-shadow` stack on captions/hook (NEVER `-webkit-text-stroke` — fails in headless Chrome):
```
text-shadow:
  -3px -3px 0 #000, 3px -3px 0 #000, -3px 3px 0 #000, 3px 3px 0 #000,
  -3px  0   0 #000, 3px  0   0 #000,  0  -3px 0 #000,  0  3px 0 #000;
```

**No `<br>` in content text** (SKILL.md non-negotiable rule #11). Natural wrap via container width.

---

## Motion Rules

| Element | Entrance | Exit |
|---------|----------|------|
| Hook headline | `gsap.from({y:50, opacity:0, duration:0.7, ease:"power3.out"})` at 0.3s | NONE — transition handles |
| Scripture card | `gsap.from({y:40, opacity:0, duration:0.8, ease:"power2.out"})` at 0.5s | NONE |
| Body line (per segment) | `gsap.from({y:30, opacity:0, duration:0.4, ease:"power3.out"})` at line.start | `tl.set(opacity:0)` AT line.end (next segment swap) |
| Austerity phrase | `gsap.from({opacity:0, duration:1.0, ease:"power2.out"})` at 0.4s | NONE |
| Outro archetype | `gsap.from({opacity:0, scale:0.92, duration:0.6})` at 0.4s | **FINAL FADE OK** — last 0.5s `gsap.to({opacity:0})` |

**Eases used (≥3 distinct per scene)**: `power3.out`, `power2.out`, `expo.out`, `power3.inOut`, `sine.out`.

**Cuts/min ceiling**: 10 (sermon content). v3 has 5 scenes in 60s = **5/min** — well within.

**Scene transitions** (between scenes — handled at root):
- Hook → Scripture: shader dissolve 0.6s
- Scripture → Body: shader dissolve 0.5s
- Body → Austerity: shader dissolve 0.6s
- Austerity → Outro: hard cut (decisive after silence)

**Forbidden** (SKILL.md mandatory):
- `Math.random()`, `Date.now()`, `repeat: -1` — deterministic only
- `gsap.set()` on later scene clip elements — use `tl.set()` inside timeline
- exit animations except final scene
- `position: absolute; top: Npx;` on content containers (use flex + padding)
- `<br>` in content text
- async/Promise/setTimeout in timeline construction

---

## Scene Architecture

| Scene | Time | Duration | Content | Background |
|-------|------|----------|---------|------------|
| 1. Hook | 0–6s | 6s | Single headline (clip's hook line) | charcoal |
| 2. Scripture | 6–14s | 8s | Scripture card with verse text + ref | charcoal |
| 3. Body | 14–48s | 34s | 4–6 segment lines (lower-third equivalent) | charcoal |
| 4. Austerity | 48–54s | 6s | One short Korean phrase (Noto Serif KR) | **pure black** |
| 5. Outro | 54–60s | 6s | Archetype label + brand mark | charcoal |

**Layout pattern (SKILL.md mandatory)**: Every scene-content uses
```css
.scene-content {
  width: 100%; height: 100%;
  padding: 220px 80px 270px 80px;  /* TikTok safe zones */
  display: flex; flex-direction: column;
  justify-content: <position>;       /* center / flex-end / flex-start */
  box-sizing: border-box;
}
```
NEVER `position: absolute; top: Npx`. Decoratives (scripture-card border) only may be absolute.

---

## Audio

- Voice: −16 LUFS integrated, −1.5 dBTP (post-render via `audio_master.py`)
- Music bed (optional): −22 LUFS, sidechain duck (FFmpeg post-step)
- Austerity scene: full silence (audio mute via Animation `tl.call(() => muteAll())` at scene boundary OR pre-edited audio segment)

---

## Persona #3 Forbidden List (16 items — must NOT appear)

1. AI-generated faces of Christ or any human
2. Music swell synchronized to scripture reveal (manipulation)
3. Gold gradients (solid only)
4. Handwritten-style scripture fonts
5. Mixed 명조/고딕 inside one verse
6. Adult-targeted NIV-Korean rhetoric
7. European-features Christ depictions
8. Tissot / master-painting Ken Burns over scripture
9. Intro bumper > 4 seconds
10. Glow / extrude / drop-shadow on scripture text
11. Clickbait cut grammar
12. cuts/min > 12 (sermon)
13. Exit animations on non-final scenes (SKILL.md)
14. `position: absolute; top: Npx;` content containers (SKILL.md)
15. Single 60s file (SKILL.md — sub-composition mandatory)
16. Composition without DESIGN.md gate (SKILL.md)

---

## Content Inject Contract

sermon-app `app/render/payload.py::build_short_payload_v3()` will inject:

```jsonc
{
  "composition": "sermon_short_v3",
  "audio_url": "<HTTP URL>",
  "audio_clip": {"start_sec": 0, "duration": 60},
  "music_bed_url": "",                     // optional
  "hook_text": "너는 예수님을 어떻게 대했냐",
  "hook_archetype": "질문",
  "austerity_phrase": "주님 앞에 잠잠하라",
  "scripture_ref": "요한복음 3:16",       // formatted
  "scripture_text": "하나님이 세상을 …",
  "scripture_translation": "개역개정",
  "body_lines": [                          // 4-6 lines for body 34s
    {"html": "너는 <span class='emphasis'>예수님을</span> 어떻게…",
     "start": 0.0,                         // body-local seconds
     "duration": 7.5}
  ]
}
```

If `body_lines` empty, scene-body collapses to "Continued…" placeholder.
If `scripture_text` empty, scene-scripture collapses to a 0.5s blank pad.

---

## Render Targets

- 1080×1920 vertical (9:16)
- 30 fps
- h264 (NVENC on HP), CRF 20 standard preset
- SDR rec.709
- File size target: 2–4 MB for 60s (sufficient for social platforms)
- Render time target: ≤ 60s on HP (2 RTX 3060)
