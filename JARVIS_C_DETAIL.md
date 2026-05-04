# JARVIS_C_DETAIL — v5 디테일 패치 (자막 톤 균일 + 폰트/색)

작성: 2026-05-04 / 우선순위: P0 (B 두 번째 — A 음악 베드 완료 후)
대상: linux-quant `claude` CLI (tmux: jarvis-c)
모드: 선각자 (창작 0% / student-kit may-shorts-19 1:1 vendor)

---

## 0. 컨텍스트

W2 (음악 베드) 완료 후 진입. v5 layout이 자체 디자인 → student-kit 톤과 불일치 = 사용자 지적 "이미 만들어진 것 쓰는 거 아닌가?" 의 본질. 이번 작업으로 layout 자체를 student-kit may-shorts-19 1:1 vendor in.

## 1. 통신 매핑

(JARVIS_W2_PHASE5_MUSIC.md 의 1번 섹션 동일)

## 2. 산출물

`/home/quant/sermon-app/app/render/compositions/sermon_short_v6/` (v5 base 위에 layout 교체)

```
sermon_short_v6/
  ├── (v5 그대로 복사 + 다음만 변경)
  └── compositions/
      ├── scene-hook.html       # may-shorts-19 scene1-intro 1:1 vendor
      ├── scene-scripture.html  # may-shorts-19 scene3-pointless 또는 scene6-only-ones 1:1 vendor
      ├── scene-body.html       # may-shorts-19 scene2-rejection 1:1 vendor (단어별 highlight 패턴 그대로)
      ├── scene-austerity.html  # may-shorts-19 scene4-six 1:1 vendor (큰 숫자/글자 emphasis 패턴)
      ├── scene-outro.html      # may-shorts-19 scene7-cta 1:1 vendor (golden CTA 패턴)
      └── components/           # v5 그대로 (motion partials)
```

**선각자 1:1 모방 룰 — 절대 변경 금지**:
- HTML 구조 (div/span class hierarchy)
- CSS (font-family, weight, size, letter-spacing, color, transform)
- GSAP timeline (각 .from/.to/.set 호출 — duration / ease / position 그대로)
- 변경 가능한 것 ONLY: 텍스트 placeholder ({{HOOK_TEXT}} 등) 와 색상/폰트 sermon-app palette 1줄 swap

sermon-app palette (vendor 후 변경):
- 배경: `#0E1116` (검은-네이비)
- 텍스트 메인: `#F5EFE0` (parchment)
- 골드: `#C8A35F` (sparing — emphasis word + CTA만)
- 한글 본문: `Pretendard Variable` 800
- 명조 (Austerity): `Noto Serif KR` 600

## 3. 6 step

### Step 1 — student-kit ref 정독

```bash
cd /home/quant
test -d hyperframes-student-kit-ref || git clone --depth=1 https://github.com/nateherkai/hyperframes-student-kit.git hyperframes-student-kit-ref

# 5개 reference 정독
for f in scene1-intro scene2-rejection scene3-pointless scene4-six scene7-cta; do
  echo "=== $f ==="
  head -100 ~/hyperframes-student-kit-ref/video-projects/may-shorts-19/compositions/$f.html
  echo
done
```

### Step 2 — v6 디렉토리 (v5 base 복사 + scene 교체)

```bash
cd /home/quant/sermon-app/app/render/compositions
cp -r sermon_short_v5 sermon_short_v6
sed -i 's/sermon_short_v5/sermon_short_v6/g' sermon_short_v6/index.html sermon_short_v6/compositions/scene-*.html
```

### Step 3 — scene-hook 1:1 vendor (may-shorts-19/scene1-intro)

`compositions/sermon_short_v6/compositions/scene-hook.html` 통째로 may-shorts-19/scene1-intro 패턴으로 교체:

- `<template id="scene-hook-template">` wrapping 유지
- `data-composition-id="scene-hook"` (v5와 동일 — root index.html 호환)
- `data-duration="6"` 유지
- 안의 콘텐츠: scene1-intro 패턴 그대로 (s1-label / s1-counter / s1-stamp 같은 div 구조 + GSAP timeline 그대로)
- 변경 ONLY:
  - 텍스트: `<span id="hook-text">{{HOOK_TEXT}}</span>` (placeholder 유지)
  - 색깔: scene1 의 `#37bdf8` (skyblue) → `#F5EFE0` (sermon parchment)
  - `#f09025` (orange plus) → `#C8A35F` (sermon gold)
  - 폰트: Roboto Mono → Pretendard Variable (한글), Montserrat → Noto Serif KR (영문)
  - GSAP timeline 변경 0%

### Step 4 — scene-scripture / scene-body / scene-austerity / scene-outro 동일 패턴

| sermon scene | may-shorts-19 source | 1:1 변경 |
|---|---|---|
| scene-scripture | scene3-pointless 또는 scene6-only-ones | 카드 layout + golden border draw |
| scene-body | scene2-rejection | 단어별 highlight |
| scene-austerity | scene4-six (big-number reveal) | 큰 글자 emphasis |
| scene-outro | scene7-cta | golden CTA pulse |

각 scene 의 `data-duration` 은 v5와 동일 유지 (Hook 6 / Scripture 8 / Body 28 / Austerity 6 / Outro 6 — 합계 60s).

### Step 5 — index.html scene start 시각 + shader transitions

v5 의 `data-start` 값 그대로 유지:
- scene-hook: 0
- scene-scripture: 6
- scene-body: 14
- scene-austerity: 42
- scene-outro: 48

linear-promo-30s 의 shader transition 패턴 (whip-fade / morph / fade-to-black) 1:1 적용:
- Hook(6) → Scripture(6): whip-fade 0.4s
- Body(28) → Austerity(42): fade-to-black 0.5s
- Austerity(48) → Outro(48): fade-up 0.4s

### Step 6 — v6 검증 + HP-Z2-LLM 동기화 + 5 mood × 5 sample render

```bash
git add -A
git -c user.email=jacob.kim@achurch.net -c user.name=jacob commit -m "feat(c): v6 layout vendor — may-shorts-19 1:1"
git push origin main

# HP rsync
ssh -i ~/.ssh/id_ed25519 quant@192.168.1.111 "mkdir -p /home/quant/hyperframes-render/compositions/sermon_short_v6"
rsync -av -e "ssh -i ~/.ssh/id_ed25519" /home/quant/sermon-app/app/render/compositions/sermon_short_v6/ quant@192.168.1.111:/home/quant/hyperframes-render/compositions/sermon_short_v6/

# audio src patch
ssh -i ~/.ssh/id_ed25519 quant@192.168.1.111 'sed -i "s|src=\"silent60.mp3\"|src=\"{{AUDIO_URL}}\"|" /home/quant/hyperframes-render/compositions/sermon_short_v6/index.html'

# 5 mood × v6 render
for mood in reverent hope conviction joy silent; do
  python3 -c "
import json, requests, time
p = json.load(open('/tmp/v5_payload.json'))
p['composition'] = 'sermon_short_v6'
p['audio_url'] = 'http://100.116.4.84:9876/audio_$mood.mp3'
r = requests.post('http://100.104.121.7:8770/render', json=p, timeout=30)
rid = r.json()['render_id']
for _ in range(40):
    time.sleep(3)
    s = requests.get(f'http://100.104.121.7:8770/render/{rid}/status').json()
    if s.get('status')=='ready': break
import urllib.request as u
u.urlretrieve(f'http://100.104.121.7:8770/output/{rid}.mp4', '/tmp/sermon-app/renders/v6_${mood}_VENDORED.mp4')
print('OK $mood')
"
done

ls -lh /tmp/sermon-app/renders/v6_*_VENDORED.mp4
```

## 4. HANDOVER

`~/sermon-app/HANDOVER_C_detail.md`:

```markdown
# C. Detail Patch (v6 = may-shorts-19 1:1 vendor)

## v6 mp4 (5 mood)
- http://100.116.4.84:9876/v6_reverent_VENDORED.mp4
- http://100.116.4.84:9876/v6_hope_VENDORED.mp4
- http://100.116.4.84:9876/v6_conviction_VENDORED.mp4
- http://100.116.4.84:9876/v6_joy_VENDORED.mp4
- http://100.116.4.84:9876/v6_silent_VENDORED.mp4

## 1:1 vendor 검증 (변경한 부분 명시)
| scene | source | changed (must be palette/font/text only) |
|---|---|---|
| scene-hook | scene1-intro | colors → sermon palette, fonts → Pretendard/Noto Serif KR, text {{HOOK_TEXT}} |
| ... | ... | ... |

## git
<commit>

## 다음
사용자 5 mp4 시청 → 톤 OK 시 B (reel) 진입.
```

## 5. 정책

1. **1:1 vendor 강제** — GSAP timeline / ease / duration 변경 금지. CSS 색깔/폰트만 swap.
2. **v5 회귀 금지** — sermon_short_v5 그대로 보존 (옵션 fallback).
3. **검증 실패** = 추가 시도 금지. HANDOVER 1줄 보고.

시작 명령: `/tmp/sermon-app` 에서 git pull 후 6 step.
