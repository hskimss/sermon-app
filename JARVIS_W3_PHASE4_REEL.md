# JARVIS_W3_PHASE4_REEL — sermon_reel_v1 (2-3분 멀티씬)

작성: 2026-05-04 / 우선순위: P0 (B 마지막 — A + C 완료 후)
대상: linux-quant `claude` CLI (tmux: jarvis-w3)
모드: 선각자 (창작 0% / hyperframes-launch-video + linear-promo-30s 1:1 vendor)

---

## 0. 컨텍스트

A (음악 베드) + C (v6 layout vendor) 완료 후 진입. v6 가 60s short. 이번 작업 = **2-3분 reel** 만들기. chapter 자동 분할 + shader transitions + 7-10 sub-comp.

reel 사용 시나리오: sermon clip 1 + chapter 3-4개 (요약 / Scripture / 핵심 메시지 / CTA).

## 1. 통신 매핑 (JARVIS_W2 동일)

## 2. 산출물

`/home/quant/sermon-app/app/render/compositions/sermon_reel_v1/`

```
sermon_reel_v1/
  ├── index.html           # 2-3분 root, 7-10 sub-comp 호출 + shader transitions
  ├── DESIGN.md
  ├── README.md
  ├── hyperframes.json     # 의존성 + paths
  ├── silent_180.mp3       # 180s silent placeholder
  └── compositions/
      ├── intro.html       # 10s 대주제 (linear-promo-30s 01-problem-type 1:1)
      ├── chapter-1.html   # 30-40s (linear-promo 02 또는 04 1:1)
      ├── chapter-2.html   # 30-40s
      ├── chapter-3.html   # 30-40s
      ├── highlight-quote.html # 8s gold pull-quote (linear-promo 03 1:1)
      ├── scripture-card.html  # 8s (linear-promo 또는 may-shorts-19 1:1)
      ├── outro.html       # 10s (linear-promo 08-cta 1:1)
      └── components/      # v5에서 재사용
```

## 3. 7 step

### Step 1 — chapter 자동 분할 (Gemma 4)

`/home/quant/sermon-app/app/render/reel_chapter.py` 신규:

```python
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
        "messages": [{"role":"user","content": prompt}],
        "think": False,
        "format": CHAPTER_SCHEMA,
        "stream": False,
        "options": {"temperature":0.0, "repeat_penalty":1.3, "num_predict":2000}
    }, timeout=120)
    return json.loads(r.json()["message"]["content"])["chapters"]
```

### Step 2 — student-kit 정독 + 1:1 vendor 대상 결정

```bash
ls ~/hyperframes-student-kit-ref/video-projects/linear-promo-30s/compositions/
# 01-problem-type.html → intro
# 02-card-to-logo.html → chapter-1
# 03-brand-reveal.html → highlight-quote
# 04-benefits-flowchart.html → chapter-2
# 05-product-surfaces.html → chapter-3
# 06-wheel-pillars.html → scripture-card
# 07-foundation.html → 추가 자료 또는 skip
# 08-cta-outro.html → outro
```

### Step 3 — sermon_reel_v1 디렉토리 + 7 sub-comp 1:1 vendor

```bash
mkdir -p /home/quant/sermon-app/app/render/compositions/sermon_reel_v1/compositions
cd /home/quant/sermon-app/app/render/compositions/sermon_reel_v1/compositions

# 1:1 복붙 + 변수만 sermon에 swap
for src,dst in [(01,intro), (02,chapter-1), (03,highlight-quote), (04,chapter-2), (05,chapter-3), (06,scripture-card), (08,outro)]; do
  cp ~/hyperframes-student-kit-ref/video-projects/linear-promo-30s/compositions/${src}-*.html ./${dst}.html
  # 색상/폰트만 swap (W3 C 단계와 동일 룰)
done
```

### Step 4 — index.html 작성 (2-3분 root)

`compositions/sermon_reel_v1/index.html`:

```html
<!doctype html>
<html><head>...</head><body>
<div id="root" data-composition-id="sermon_reel_v1" data-start="0" data-duration="180" data-width="1080" data-height="1920">
  <div data-composition-src="compositions/intro.html" data-start="0" data-duration="10" data-track-index="0"></div>
  <div data-composition-src="compositions/chapter-1.html" data-start="10" data-duration="40" data-track-index="0"></div>
  <div data-composition-src="compositions/chapter-2.html" data-start="50" data-duration="40" data-track-index="0"></div>
  <div data-composition-src="compositions/highlight-quote.html" data-start="90" data-duration="8" data-track-index="0"></div>
  <div data-composition-src="compositions/chapter-3.html" data-start="98" data-duration="40" data-track-index="0"></div>
  <div data-composition-src="compositions/scripture-card.html" data-start="138" data-duration="22" data-track-index="0"></div>
  <div data-composition-src="compositions/outro.html" data-start="160" data-duration="20" data-track-index="0"></div>
  
  <audio id="el-voice" data-start="0" data-duration="180" data-track-index="2" data-volume="1.0"
    data-audio-url="{{AUDIO_URL}}" src="{{AUDIO_URL}}" crossorigin="anonymous"></audio>
</div>
<script>
  window.__timelines = {};
  const tl = gsap.timeline({paused:true});
  tl.set({}, {}, 180);
  window.__timelines["sermon_reel_v1"] = tl;
</script>
</body></html>
```

### Step 5 — payload + reel 빌더

`/home/quant/sermon-app/app/render/payload.py` 에 `build_reel_payload_v1` 추가 (chapter 자동 분할 호출 + 각 chapter placeholder 채움).

### Step 6 — 검증 render

```bash
# 180s sermon clip + chapter 자동 분할
ffmpeg -y -i /tmp/sermon_real.mp3 -ss 0 -t 180 -c:a libmp3lame -b:a 96k /tmp/sermon-app/renders/audio_reel_180.mp3

python3 -c "
import json, requests, time
from pathlib import Path
import sys; sys.path.insert(0,'/tmp/sermon-app')
from app.render.payload import build_reel_payload_v1
p = build_reel_payload_v1(
    job_id='reel_test',
    clip={'start_sec':0.0,'end_sec':180.0,'id':'reel_test'},
    jobs_dir=Path('/tmp/sermon-app/jobs'),
)
p['audio_url'] = 'http://100.116.4.84:9876/audio_reel_180.mp3'
print('chapters:', len(p.get('chapters',[])))
r = requests.post('http://100.104.121.7:8770/render', json=p, timeout=60)
rid = r.json()['render_id']
for _ in range(80):
    time.sleep(5)
    s = requests.get(f'http://100.104.121.7:8770/render/{rid}/status').json()
    print(s.get('status'))
    if s.get('status')=='ready': break
import urllib.request as u
u.urlretrieve(f'http://100.104.121.7:8770/output/{rid}.mp4', '/tmp/sermon-app/renders/reel_v1.mp4')
"
```

### Step 7 — git + HANDOVER

`~/sermon-app/HANDOVER_W3_phase4.md`:

```markdown
# W3 Phase 4 — sermon_reel_v1 Complete

## reel mp4
- URL: http://100.116.4.84:9876/reel_v1.mp4
- 길이: <X>분 <Y>초
- chapters: <N>
- mean_volume: <Z>dB

## chapter 자동 분할 결과 (Gemma 4)
| # | title | start | end | quote |
|---|---|---|---|---|
| 1 | ... | ... | ... | ... |

## 1:1 vendor 검증
| sub-comp | source | changed |
|---|---|---|
| intro | linear-promo 01-problem-type | palette + text |
| ... | ... | ... |

## git
<commit>

## 다음
사용자 reel 시청 → OK 시 W4 (Gate review + Phase 6+7) 진입.
```

## 4. 정책

1. **선각자 1:1 vendor 강제** — linear-promo-30s 의 GSAP timeline 변경 금지. CSS 색깔/폰트만 swap.
2. **chapter 자동 분할** Gemma 4 호출 — 실패 시 fallback (segments duration 균등 분할).
3. **render duration 180s** — :8770 server timeout 더 길게 (60초가 아니라 240초). estimated_sec 도 180.
4. **검증 실패** — 추가 시도 금지. HANDOVER 1줄 보고.

## 5. 시작

`/tmp/sermon-app` 에서 git pull origin main 후 7 step. 완료시 HANDOVER_W3_phase4.md.
