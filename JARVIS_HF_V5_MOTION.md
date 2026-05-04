# JARVIS_HF_V5_MOTION

작성: 2026-05-04 / 우선순위: P0
대상: linux-quant `claude` CLI (jarvis-v5 tmux session)
모드: 선각자 (창작 0% / GitHub student-kit 1:1 모방 100%)

---

## 0. 컨텍스트

- v4 = production base (placeholder 치환 OK, 5/5 scene visible, 음성 -42dB 정상)
- v4_REAL.mp4 (http://100.116.4.84:9876/v4_REAL.mp4) 사용자 OK 받음
- 정적 디자인만 → 이제 **모션 그래픽** 추가가 v5 목표

## 1. 통신 매핑 (절대 외우지 말고 이 작업지시서만 보고 진행)

| 노드 | LAN IP | 진입 키 |
|---|---|---|
| linux-quant (자기) | 100.116.4.84 / 192.168.1.119 | (현재 위치) |
| HP-Z2-LLM render server :8770 | 192.168.1.111 (Tailscale 100.104.121.7는 auth 막힘) | `~/.ssh/id_ed25519` |
| Mac (sermon mp3 source) | 100.89.99.106 | `~/.ssh/id_ed25519` |

**HP-Z2-LLM SSH** (LAN으로):
```bash
ssh -i ~/.ssh/id_ed25519 quant@192.168.1.111
```

**HP-Z2-LLM composition 위치** (sermon-app과 별도 자체 사본):
```
/home/quant/hyperframes-render/compositions/sermon_short_v5/
```

## 2. 산출물 (정확히 이것만)

`/home/quant/sermon-app/app/render/compositions/sermon_short_v5/` (linux-quant 작업 위치)
+ HP-Z2-LLM 동기화

```
sermon_short_v5/
  ├── DESIGN.md             # v5 모션 가이드 (사용자 검토용)
  ├── README.md
  ├── hyperframes.json
  ├── index.html            # 5씬 + shader transition 1개
  ├── silent60.mp3
  └── compositions/
      ├── scene-hook.html        # kinetic typography (글자 wipe-in stagger)
      ├── scene-scripture.html   # 골드 보더 draw + 본문 fade-in line별
      ├── scene-body.html        # 단어별 highlight + emphasis word flash
      ├── scene-austerity.html   # contrast 1→1.5 + vignette deepen
      ├── scene-outro.html       # archetype label slide + tag pulse
      └── components/
          ├── kinetic-type.html  # student-kit linear-promo `01-problem-type` 1:1
          ├── card-glow.html     # student-kit claude-edit-intro card pattern 1:1
          ├── word-highlight.html # may-shorts-19 scene2 1:1
          └── archetype-reveal.html # may-shorts-19 scene7 1:1
```

## 3. 6 step 작업

### Step 1 — sermon-app pull + student-kit 참조 정독

```bash
cd /home/quant && (test -d sermon-app && cd sermon-app && git pull origin main) || git clone ssh://git@localhost:2222/quant/sermon-app.git
cd /home/quant && (test -d hyperframes-student-kit-ref || git clone --depth=1 https://github.com/nateherkai/hyperframes-student-kit.git hyperframes-student-kit-ref)
```

**1:1 모방할 4개 파일 정독 (반드시 grep 후 코드 패턴 머리에 넣기)**:
- `~/hyperframes-student-kit-ref/video-projects/linear-promo-30s/compositions/01-problem-type.html` — kinetic typography
- `~/hyperframes-student-kit-ref/video-projects/may-shorts-19/compositions/scene2-rejection.html` — word highlight
- `~/hyperframes-student-kit-ref/video-projects/may-shorts-19/compositions/scene7-cta.html` — archetype reveal
- `~/hyperframes-student-kit-ref/video-projects/aisoc-app-release/compositions/*.html` — card-glow 패턴 1개 골라

### Step 2 — sermon_short_v5/ 생성 (v4 base 복사)

```bash
cd /home/quant/sermon-app/app/render/compositions
cp -r sermon_short_v4 sermon_short_v5
sed -i 's/sermon_short_v4/sermon_short_v5/g' sermon_short_v5/index.html
sed -i 's/sermon_short_v4/sermon_short_v5/g' sermon_short_v5/compositions/scene-*.html
```

### Step 3 — components/ 4개 모션 partial 생성 (창작 0%, 1:1 복붙)

각 partial은 `<template id="<name>-template">` wrapping 사용 (HF v0.4 규칙).

- `components/kinetic-type.html` — linear-promo `01-problem-type` 의 timeline 패턴 그대로 (입자 stagger + scale)
- `components/card-glow.html` — clipPath inset reveal + 골드 border draw
- `components/word-highlight.html` — may-shorts-19 scene2 word-by-word highlight + emphasis flash
- `components/archetype-reveal.html` — may-shorts-19 scene7 slide-up + pulse

각 partial은 GSAP timeline 만들고 `window.__motionPartials = window.__motionPartials || {}; window.__motionPartials["<name>"] = (sel) => { /* tl */ }` 패턴으로 export. (sub-comp scene 안에서 호출하기 위해)

### Step 4 — 5 scene-*.html 에 모션 적용

각 scene 의 timeline 마지막에 motion partial 호출 추가:

```javascript
// scene-hook.html 안 timeline 끝에
if (window.__motionPartials && window.__motionPartials["kinetic-type"]) {
  window.__motionPartials["kinetic-type"](`[data-composition-id="scene-hook"]`)(tl, 0);
}
```

- scene-hook ← `kinetic-type`
- scene-scripture ← `card-glow`
- scene-body ← `word-highlight`
- scene-austerity ← `vignette-deepen` (직접 추가, 단순 contrast/opacity)
- scene-outro ← `archetype-reveal`

### Step 5 — index.html 에 shader transition 1개 추가

Hook → Scripture 전환에 whip-fade. `@hyperframes/shader-transitions` 사용.

`hyperframes.json` 의 dependencies 에 추가 (선각자 모드 — student-kit 의 `linear-promo-30s/hyperframes.json` 참조):

```json
"dependencies": {
  "@hyperframes/shader-transitions": "^0.4.0"
}
```

index.html 에 transition 선언:
```html
<div class="transition-layer"
     data-transition="whip-fade"
     data-from="scene-hook"
     data-to="scene-scripture"
     data-start="3.8"
     data-duration="0.4"></div>
```

### Step 6 — git commit + HP-Z2-LLM 동기화 + 검증 렌더

```bash
cd /home/quant/sermon-app
git -c user.email=jacob.kim@achurch.net -c user.name=jacob add -A
git -c user.email=jacob.kim@achurch.net -c user.name=jacob commit -m "feat(v5): motion graphics — kinetic type + card glow + word highlight + transitions"
git push origin main

# HP-Z2-LLM에 v5 composition 전달 (Gitea pull 안 됨, 직접 rsync)
ssh -i ~/.ssh/id_ed25519 quant@192.168.1.111 "mkdir -p /home/quant/hyperframes-render/compositions/sermon_short_v5"
rsync -av -e "ssh -i ~/.ssh/id_ed25519" /home/quant/sermon-app/app/render/compositions/sermon_short_v5/ quant@192.168.1.111:/home/quant/hyperframes-render/compositions/sermon_short_v5/

# v5 audio src 패치 (v4와 동일 — silent60.mp3 → {{AUDIO_URL}})
ssh -i ~/.ssh/id_ed25519 quant@192.168.1.111 'sed -i "s|src=\"silent60.mp3\"|src=\"{{AUDIO_URL}}\"|" /home/quant/hyperframes-render/compositions/sermon_short_v5/index.html'

# render server 의 composition 등록 갱신 (server가 자동 인식 안 하면 SIGHUP)
curl -s http://100.104.121.7:8770/health | grep v5

# 등록 안돼있으면 server 재시작 필요할 수도. 일단 health 체크.

# 검증 render
python3 << 'PY'
import json, requests, time
p = json.load(open('/tmp/v4_payload.json'))
p['composition'] = 'sermon_short_v5'
p['audio_url'] = 'http://100.116.4.84:9876/v4_audio.mp3'
r = requests.post('http://100.104.121.7:8770/render', json=p, timeout=30)
print(r.json())
rid = r.json()['render_id']
for i in range(40):
    time.sleep(3)
    s = requests.get(f'http://100.104.121.7:8770/render/{rid}/status').json()
    print(s.get('status'), s.get('audio_mux_warning',''))
    if s.get('status') in ('ready','failed'): break
import urllib.request as u
u.urlretrieve(f'http://100.104.121.7:8770/output/{rid}.mp4', '/tmp/sermon-app/renders/v5_FIRST.mp4')
print('OK')
PY

ls -lh /tmp/sermon-app/renders/v5_FIRST.mp4
ffmpeg -i /tmp/sermon-app/renders/v5_FIRST.mp4 -af volumedetect -vn -f null - 2>&1 | grep mean_volume
```

## 4. 완료 보고 (정확히 이 형식으로 `~/sermon-app/HANDOVER_HF_v13_motion.md` 작성)

```markdown
# HF v5 Motion — Result

## v5 mp4
- 경로: /tmp/sermon-app/renders/v5_FIRST.mp4
- URL: http://100.116.4.84:9876/v5_FIRST.mp4
- 사이즈: <X>MB
- mean_volume: <Y> dB
- duration: <Z>s

## 적용된 모션 (5개 + shader 1)
| Scene | 모션 | 모방 출처 | 적용 |
|---|---|---|---|
| Hook | kinetic-type stagger | linear-promo 01-problem-type | ✅/❌ |
| Scripture | card-glow border draw | aisoc-* | ✅/❌ |
| Body | word-highlight + emphasis flash | may-shorts-19 scene2 | ✅/❌ |
| Austerity | vignette-deepen contrast | linear-promo vignette | ✅/❌ |
| Outro | archetype-reveal slide+pulse | may-shorts-19 scene7 | ✅/❌ |
| Hook→Scripture | whip-fade shader | hyperframes-launch-video | ✅/❌ |

## git commit
<commit hash + message>

## 다음 액션
사용자 v5_FIRST.mp4 시청 → 톤 OK 시 W3 finalize. FAIL 시 어느 scene 톤 안 맞는지 1줄.
```

## 5. 정책 (절대 위반 금지)

1. **선각자 모드 강제** — components/ 4개 모션 partial은 student-kit 코드 1:1 복붙. 변수명/색깔만 sermon-app 에 맞춤. 새 GSAP 패턴 창작 금지.
2. **v4 회귀 금지** — sermon_short_v4 폴더 손대지 말 것. v5는 별도.
3. **HP-Z2-LLM 통신** — Tailscale 100.104.121.7 SSH 시도 금지 (auth 막힘). 무조건 LAN 192.168.1.111.
4. **검증 실패시** — 추가 패치 시도 금지. HANDOVER에 정확히 어디서 막혔는지 1줄로 보고.
5. **render server :8770 응답 audio_mux_warning** 발생시 audio_url 접근 가능 여부 먼저 확인.

진행해. 완료시 HANDOVER 만들고 종료.
