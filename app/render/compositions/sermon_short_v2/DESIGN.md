# sermon_short_v2 — Design Choices

> Authority: `CLAUDE_DESIGN_BRIEF.md` (A Church London brand)
> Aesthetic anchor: *Bible Project minimalism × ESV/Crossway typographic weight*
> Anti-pattern: NOT prosperity-gospel TV, NOT TikTok meme captions, NOT Higgsfield hyper-cinematic

---

## 1. Five-Scene Architecture

| # | Name | Default range | Purpose | Inject |
|---|------|---------------|---------|--------|
| 1 | Hook | 0–6s | Capture attention with the clip's central question/statement | `HOOK_TEXT` |
| 2 | Scripture card | 6–14s | Anchor the message in scripture (the theological "why") | `SCRIPTURE_*`, `SCRIPTURE_REFS_JSON` |
| 3 | Body / lower-third | 14–48s (or until 6s before end) | Word-by-word captions with emphasis on Gemma-selected key words | `WORDS_JSON` |
| 4 | Austerity | (TOTAL−12)–(TOTAL−6) | Reverent restraint — black screen, white serif Korean phrase, audio silenced | `AUSTERITY_PHRASE` |
| 5 | Outro | last 6s | Brand mark + archetype label, music fades in | `HOOK_ARCHETYPE` |

**Graceful degradation**: scene 2 collapses if no scripture; scene 3 collapses if no words. Total stays 60s.

---

## 2. Typography

```
captions          Pretendard Variable ExtraBold (800), 84px
hook              Pretendard Variable ExtraBold (800), 96px
scripture body    Sandoll Myungjo Neo1 SemiBold (600) → Noto Serif KR fallback, 56px
scripture ref     Pretendard 700, 40px, gold
austerity phrase  Sandoll Myungjo Neo1 (Noto Serif KR fallback) 600, 76px
outro brand       Pretendard 600, 30px, opacity 0.7
outro archetype   Pretendard 600, 28px, gold, letter-spacing 0.12em
```

**Why mixed typography**: Pretendard's broad-stroke modernity for active speech; Sandoll/Noto Serif's measured weight for scripture and contemplative text. **Never mix within a single line.**

**Word-break**: `keep-all` on every Korean text element. Without it, Korean lines split mid-word in headless Chrome.

---

## 3. Color System

`:root` declares all six brand colors as custom properties. Designers can re-skin by changing one selector. Per Persona #3:

- Gold (`#B8923A`) is **solid only** — gradients on gold = prosperity-gospel TV.
- Emphasis gold (`#D4AF37`) is a single brighter variant for caption emphasis only.
- Oxblood (`#6B1F26`) reserved for lament/warning content (not used in this composition; available for future v3).
- Charcoal (`#0E1116`) is the default canvas. **Pure black `#000`** only in the austerity scene to amplify reverence.

---

## 4. Animation Principles (strict)

1. **No `-webkit-text-stroke`** — fails in headless Chromium. Replaced by 8-direction `text-shadow` stack (`var(--stroke-8)`).
2. **Word fade-in 0.35s `power2.out`** — gentle, not bouncy. Bouncy springs read as TikTok-amateur.
3. **Scripture fade 0.6–0.8s** — never slide / type-on / bounce. Reverence demands stillness.
4. **Cross-dissolve 0.8s** between scene 1→2 and 3→4 (per brief: 2 transitions).
5. **Hard cut** between 4→5 — outro should feel decisive after austerity.
6. **Cuts/min ceiling 12**: this composition has 5 scenes = 5 cuts in 60s = **5/min**. Within budget.
7. **No emojis**, no glow, no extrude, no drop-shadow on scripture.
8. **Music bed silenced during austerity** via `muteAllAudio(true)` GSAP `.call()` keyframes — programmatic, not just visual.

---

## 5. Safe Zones

- Top 220px: TikTok clock + handle area
- Bottom 270px: TikTok action buttons + caption strip

Captions (scene 3) live in the **center 1430px stripe** — `top: 1080px; height: 540px;` keeps them safely above the bottom controls and below the top UI.

---

## 6. Audio Architecture

Two `<audio>` tracks (HF picks them up automatically):

```
data-track-index="1" data-volume="1.0"    <- sermon voice
data-track-index="2" data-volume="0.4"    <- music bed (placeholder)
```

The composition itself does NOT do sidechain compression — that's an FFmpeg post-step on the produced mp4. The composition only handles the **mute-during-austerity** behavior because it's a deliberate compositional choice (silence as theology), not a mixing detail.

---

## 7. Graceful Degradation (failure modes)

| Missing | Effect |
|---------|--------|
| `WORDS_JSON = []` | Scene 3 collapses. Hook/Scripture/Austerity/Outro still play. |
| `SCRIPTURE_REFS_JSON = []` | Scene 2 collapses. Cross-dissolve goes Hook → Body. |
| Both empty | Hook → Austerity → Outro (still ~18s of structure). |
| `MUSIC_BED_URL = ""` | Single track only. `muteAllAudio` still works. |
| `HOOK_TEXT = ""` | Hook scene visually empty but timing preserved. |

The composition **never crashes** on missing inputs.

---

## 8. What this composition does NOT do (per Persona #3)

- ❌ AI-generated faces (especially of Christ)
- ❌ Gold gradients
- ❌ Glow / extrude / drop-shadow on scripture text
- ❌ Mixed 명조/고딕 inside a single verse
- ❌ Music swell synchronized to scripture reveal (manipulation)
- ❌ Pop / bounce / springy animations on theological text
- ❌ Any emojis
- ❌ Bright neon caption colors
- ❌ Background video / b-roll behind captions (deliberate emptiness)

If a future v3 wants any of these, it should be explicitly debated in a separate brief.

---

## 9. Render Targets

| Spec | Value |
|------|-------|
| Resolution | 1080×1920 |
| FPS | 30 |
| Codec | h264 (NVENC on HP) |
| Bitrate | quality="standard" preset (HF default) |
| Color | SDR (rec.709) |
| LUFS target (post-mux) | −16 LUFS, −1.5 dBTP |

Rendered mp4 is then streamed through `audio_master.py::master_audio()` for two-pass loudnorm normalization (Phase D).

---

## 10. Why a v2 (not v1.5)?

v1 was a **single-scene** composition (lower-third captions on charcoal). It worked but felt thin — no visual rhythm, no scriptural anchoring, no austerity moment. v2 is a complete re-architecture, not an incremental tweak. Hence the version bump and the `composition` parameter on `/api/job/<id>/render` for opt-in (default v2 going forward).

v1 remains in the codebase as a fallback for clips where Gemma-4 fails to extract a usable hook or where transcript word timing is unreliable.
