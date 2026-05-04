# sermon_reel_v1 — DESIGN

## Overview
2-3분 (180s) vertical reel (1080×1920 / 9:16).
7 sub-comp 구조: intro → 3 chapters → highlight-quote → scripture-card → outro.

## Vendor Policy (선각자 1:1)
Source: `hyperframes-student-kit-ref/video-projects/linear-promo-30s/`

| sub-comp | vendor src | changed |
|---|---|---|
| intro | 01-problem-type | palette (gold), font (Noto Sans KR), text vars, SLOT=10, dims 1080×1920 |
| chapter-1 | 02-card-to-logo | card color (blue), cross SVG, font, text vars, SLOT=40 |
| chapter-2 | 04-benefits-flowchart | edge/glow colors (gold), font, text vars, SVG viewBox adjusted, SLOT=40 |
| highlight-quote | 03-brand-reveal | cross SVG, gold gradient, column layout, font, text vars, SLOT=8 |
| chapter-3 | 05-product-surfaces | panel-block replaces screenshot, gold headline, font, text vars, SLOT=40 |
| scripture-card | 06-wheel-pillars | wheel colors (gold/blue), panel layout adjusted, font, text vars, SLOT=22 |
| outro | 08-cta-outro | cross SVG, gold border/glow, font, text vars, SLOT=20 |

**GSAP timeline choreography: 0% changed.**

## Color Palette
- Gold primary: `#B8923A` / `#E8C876`
- Scripture blue: `#4A6FA5`
- Background: `#000`
- Text: white gradient (unchanged from vendor)

## Template Variables
Injected by `build_reel_payload_v1()` via chapter auto-split (Gemma 4).

## Timeline
```
0s   [intro        10s]
10s  [chapter-1         40s]
50s  [chapter-2         40s]
90s  [hl-quote  8s]
98s  [chapter-3         40s]
138s [scripture-card  22s]
160s [outro         20s]
180s END
```
