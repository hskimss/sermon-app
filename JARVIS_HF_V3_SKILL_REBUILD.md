# JARVIS HF v3 — SKILL.md 정석 재빌드 작업지시서

> 위임 대상: Claude Code (sermon-app 또는 linux-quant 세션)
> **전제 정정**: HF v0.4는 결함 아님. 우리 v2 6번 시도 모두 SKILL.md 6+ 규칙 위반.
> **이번 v3는 SKILL.md 100% 준수**로 정상 작동 보장 (HeyGen launch video 같은 quality 가능).
> **Remotion pivot 보류** — HF 정석으로 1.5일 안 8.5/10 도달 검증.
> 자체 완결 — 본 문서 + SKILL.md 정독만으로 진행
> 예상 공수: **1.5일** (DESIGN.md + 5 sub-comp + lint + validate + 시각 검증)

---

## 0. 시작 절차 (필수 — 정독 순서)

```bash
# 1. 작업 환경
SERMON="/Users/hwasungkim/Library/CloudStorage/GoogleDrive-sharonkim71@gmail.com/내 드라이브/AI/교회 앱/sermon-app"
cd "$SERMON"

# 2. SKILL.md 정독 — 본 작업의 절대 기준
curl -s https://raw.githubusercontent.com/heygen-com/hyperframes/main/skills/hyperframes/SKILL.md > /tmp/HF_SKILL.md
wc -l /tmp/HF_SKILL.md   # 약 350 lines
cat /tmp/HF_SKILL.md     # 처음부터 끝까지 정독 obligatory

# 3. References 정독 (SKILL.md 끝 ## References 섹션) — 최소 4개
curl -s https://raw.githubusercontent.com/heygen-com/hyperframes/main/skills/hyperframes/references/captions.md > /tmp/HF_captions.md
curl -s https://raw.githubusercontent.com/heygen-com/hyperframes/main/skills/hyperframes/references/transitions.md > /tmp/HF_transitions.md
curl -s https://raw.githubusercontent.com/heygen-com/hyperframes/main/skills/hyperframes/references/typography.md > /tmp/HF_typography.md
curl -s https://raw.githubusercontent.com/heygen-com/hyperframes/main/skills/hyperframes/references/motion-principles.md > /tmp/HF_motion.md

# 4. HeyGen launch video 정독 — 15-sub-comp pattern reference
curl -s https://raw.githubusercontent.com/heygen-com/hyperframes-launch-video/main/STORYBOARD.md > /tmp/HF_storyboard.md

# 5. 우리 v2 실패 분석 정독
cat sermon-app/HANDOVER_HF_v8_failure_pivot.md
cat CLAUDE_DESIGN_BRIEF.md
cat GIANT_MODE_v2_RESEARCH.md

# 6. 환경 health
curl -s http://localhost:5001/api/render/health
ssh -o BatchMode=yes quant@100.104.121.7 'systemctl is-active hf-server whisperx-server'
```

**중단 조건**:
- SKILL.md fetch 실패 → 사용자 보고 후 중단
- HP `:8770` 비활성 → systemd 점검
- Mac Flask 다운 → 재기동

---

## 1. 가드레일 (절대 규칙 — SKILL.md 직접 인용)

### 1.1 Gitea 전용
- Repo: `quant/sermon-app`. GitHub 금지. 신규 repo 금지.

### 1.2 SKILL.md 6+ 규칙 100% 준수 (이번 작업 전체 핵심)

| # | SKILL.md 규칙 | 우리 v2 위반 | v3 준수 방법 |
|---|---|---|---|
| 1 | **`.scene-content` MUST fill scene via `width:100%; height:100%; padding; flex`** | `position:absolute; top:1080px` | scene-content는 항상 flex container, padding으로 위치 |
| 2 | **"Reserve `position:absolute` for decoratives only"** | content container를 absolute로 | scripture-card 같은 decorative만 absolute, 자막은 flex |
| 3 | **"NEVER exit animations except final scene"** | Body chunk fade-out | entrance만 (`gsap.from`), 마지막 outro만 fade-out 허용 |
| 4 | **Sub-composition 분할 + `data-composition-src`** | 단일 60s GSAP timeline | 5 scene 별도 파일, root는 `data-composition-src` |
| 5 | **Visual Identity Gate** — DESIGN.md 없으면 composition 작성 금지 | brief 인라인만 | DESIGN.md 먼저 작성 |
| 6 | **`tl.set()` Rule #10** — 클립 elements는 timeline 안 `tl.set(selector, vars, timePosition)` | 시작 시 모든 wordSpans `gsap.set(opacity:0)` | timeline 안 tl.set으로만 |
| 7 | **Determinism** — `Math.random()`, `Date.now()`, `repeat:-1` 금지 | (확인 필요) | 사용 0 |
| 8 | **No `<br>` in content text** — natural wrap via max-width | (확인 필요) | `<br>` 사용 0 |
| 9 | **Synchronous timeline construction** — `async`/`setTimeout`/`Promise` 안 사용 | (확인 필요) | sync only |
| 10 | **Animation conflicts** — same property + same element 다수 timeline 동시 안 함 | (확인 필요) | 하나씩 |

### 1.3 검증 frame obligatory
- 매 Gate 통과 시 frame 캡처 + GDrive 자동 저장
- v2 vs v3 비교 frame 6개 (각 scene 1개)

### 1.4 보존 (변경 0)
다음은 v2에서 v3로 그대로 유지:
- `app/render/payload.py` (build_short_payload_v2 그대로 — composition만 v3로 변경)
- `app/render/audio_master.py` (ffmpeg loudnorm)
- `app/render/scripture.py` + `app/render/bible/{krv,kjv}.json`
- WhisperX server :8771 (변경 0)
- `app/static/editor.html` v1/v2 select에 v3 옵션 추가만
- `app/server.py::api_render` composition 분기에 sermon_short_v3 추가만
- v1, v2 composition 파일 그대로 보존 (회귀 위험 0)

---

## 2. Phase A — DESIGN.md (Visual Identity Gate)

SKILL.md: "Before writing ANY composition HTML, you MUST have a visual identity defined."

### 2.1 `app/render/compositions/sermon_short_v3/DESIGN.md` 작성

내용 구조 (SKILL.md 참조):

```markdown
# Sermon Short v3 — Visual Identity (A Church London)

## Style Prompt (한 단락)
A Church London 한국 디아스포라 교회의 60초 sermon short.
Bible Project minimalism × ESV/Crossway 활자 무게 융합.
"Reverent restraint" — 매 단어 강조 X, 호흡 있는 문장 단위.
Persona #3 가이드 절대 안 함 16건 모두 준수.

## Colors
| Role | Hex | Use |
|---|---|---|
| Primary background (dark) | #0E1116 | charcoal default |
| Secondary background (light) | #F5EFE0 | parchment for scripture |
| Primary text on dark | #FFFFFF | captions |
| Primary text on light | #1A2236 | ink scripture |
| Accent gold | #D4AF37 | emphasis (sparingly) |
| Border accent | #B8923A | scripture card border |

## Typography
- UI / Captions: Pretendard Variable (CDN)
- Scripture (Korean): Noto Serif KR SemiBold
- Scripture (English): EB Garamond
- Title display: Ridibatang or Noto Serif KR
- All Korean text: word-break: keep-all (mandatory)

## Motion Rules
- Word fade-in: 0.3-0.4s, power2.out (NEVER bouncy)
- Scripture card: 0.6-1.0s fade, hold (read_time + 1.5s silence)
- Cuts/min ≤ 10 (sermon content)
- Austerity moment: 1회 6s 검은화면 + 흰명조 + silence
- Shader transitions: 2개 key 모먼트 (Hook→Scripture, Body→Austerity)
- Sound: voice -16 LUFS, bed -22 LUFS sidechain duck

## What NOT to Do (Persona #3 16건)
1. AI 생성 예수 얼굴
2. 음악 swell sync to scripture (감정 사기)
3. Gold gradients (solid only)
4. 손글씨체 성구
5. 명조/고딕 한 절 안 혼용
6. NIV-Korean 어덜트 설교
7. 유럽인 외모 그리스도
8. Tissot 등 마스터 페인팅 Ken Burns
9. 인트로 범퍼 4초 초과
10. 성구 텍스트 glow/extrude/shadow
11. 클릭베이트 컷 그래머
12. cuts/min 12 초과 (sermon)
13. (위 SKILL.md 규칙 6번 — exit 애니메이션)
14. (위 SKILL.md 규칙 1-2번 — absolute 컨테이너)
15. (위 SKILL.md 규칙 4번 — 단일 파일 60s)
16. (위 SKILL.md 규칙 5번 — DESIGN.md 없이)
```

### 2.2 Gate A 통과 조건
- [ ] `app/render/compositions/sermon_short_v3/DESIGN.md` 존재
- [ ] Style Prompt + Colors + Typography + Motion Rules + What NOT 모두 작성
- [ ] 다른 composition 파일 작성 X (DESIGN.md만)

---

## 3. Phase B — Sub-composition 5개 + root index.html

SKILL.md: 사용자가 받은 STORYBOARD.md 처럼 root + 5 sub-comp 파일 분할.

### 3.1 디렉토리 구조

```
app/render/compositions/sermon_short_v3/
├── index.html                    # root (data-composition-src로 5 scene 합침)
├── DESIGN.md                     # (Phase A)
├── README.md                     # inject contract + Gate criteria
├── compositions/
│   ├── scene-hook.html           # 0-6s
│   ├── scene-scripture.html      # 6-14s
│   ├── scene-body.html           # 14-48s ← 핵심
│   ├── scene-austerity.html      # 48-54s
│   └── scene-outro.html          # 54-60s
└── silent60.mp3                  # placeholder audio
```

### 3.2 root `index.html`

SKILL.md: "**Standalone compositions (the main index.html) do NOT use `<template>`** — they put the `data-composition-id` div directly in `<body>`."

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <title>Sermon Short v3 (A Church London)</title>
  <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/variable/pretendardvariable-dynamic-subset.css');
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@600&display=swap');
    body { margin:0; background:#0E1116; }
    [data-composition-id="sermon_short_v3"] { width:1080px; height:1920px; position:relative; overflow:hidden; }
  </style>
</head>
<body>
<div data-composition-id="sermon_short_v3" data-width="1080" data-height="1920">
  
  <!-- 5 sub-compositions (SKILL.md sub-composition pattern) -->
  <div id="el-hook" 
       data-composition-id="scene-hook" 
       data-composition-src="compositions/scene-hook.html"
       data-start="0" data-duration="6" data-track-index="1"></div>
  
  <div id="el-scripture"
       data-composition-id="scene-scripture"
       data-composition-src="compositions/scene-scripture.html"
       data-start="6" data-duration="8" data-track-index="1"></div>
  
  <div id="el-body"
       data-composition-id="scene-body"
       data-composition-src="compositions/scene-body.html"
       data-start="14" data-duration="34" data-track-index="1"></div>
  
  <div id="el-austerity"
       data-composition-id="scene-austerity"
       data-composition-src="compositions/scene-austerity.html"
       data-start="48" data-duration="6" data-track-index="1"></div>
  
  <div id="el-outro"
       data-composition-id="scene-outro"
       data-composition-src="compositions/scene-outro.html"
       data-start="54" data-duration="6" data-track-index="1"></div>
  
  <!-- Audio track (sermon-app injects audio_url) -->
  <audio id="el-voice"
         data-start="0" data-duration="60" data-track-index="2"
         src="{{AUDIO_URL}}" data-volume="1.0"></audio>
  
  <!-- Music bed (optional, sidechain duck) -->
  <audio id="el-bed"
         data-start="0" data-duration="60" data-track-index="3"
         src="{{MUSIC_BED_URL}}" data-volume="0.4"
         class="optional-bed"></audio>

</div>
<!-- Root has no GSAP timeline — sub-comp timelines are auto-nested by HF -->
</body>
</html>
```

**핵심 원칙**:
- root는 GSAP timeline 0 (sub-comp timelines auto-nest)
- 각 sub-comp의 `data-duration` 이 진실 (SKILL.md "Duration comes from data-duration, not from GSAP timeline length")

### 3.3 Sub-composition 패턴 (예: scene-body.html)

```html
<template id="scene-body-template">
  <div data-composition-id="scene-body" data-width="1080" data-height="1920">
    <style>
      [data-composition-id="scene-body"] {
        width: 1080px; height: 1920px;
        background: #0E1116;
        position: relative;
        overflow: hidden;
      }
      /* SKILL.md: scene-content fills scene via flex + padding */
      [data-composition-id="scene-body"] .scene-content {
        width: 100%; height: 100%;
        padding: 220px 80px 270px 80px;  /* safe zones */
        display: flex;
        flex-direction: column;
        justify-content: flex-end;        /* lower-third equivalent */
        gap: 16px;
        box-sizing: border-box;
      }
      [data-composition-id="scene-body"] .body-line {
        font-family: 'Pretendard Variable', sans-serif;
        font-weight: 800;
        font-size: 76px;
        line-height: 1.22;
        text-align: center;
        color: #FFFFFF;
        word-break: keep-all;
        text-shadow:
          -3px -3px 0 #000, 3px -3px 0 #000, -3px 3px 0 #000, 3px 3px 0 #000,
          -3px 0 0 #000, 3px 0 0 #000, 0 -3px 0 #000, 0 3px 0 #000;
        opacity: 0;  /* CSS initial state, NOT GSAP set */
      }
      [data-composition-id="scene-body"] .body-line .emphasis {
        color: #D4AF37;
      }
    </style>
    
    <!-- scene-content fills via flex + padding (SKILL.md compliant) -->
    <div class="scene-content">
      <!-- 4-6 segment lines, sermon-app injects via {{BODY_LINES_HTML}} -->
      <div class="body-line" data-line="0">{{LINE_0_HTML}}</div>
      <div class="body-line" data-line="1">{{LINE_1_HTML}}</div>
      <div class="body-line" data-line="2">{{LINE_2_HTML}}</div>
      <div class="body-line" data-line="3">{{LINE_3_HTML}}</div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
    <script>
      window.__timelines = window.__timelines || {};
      const tl = gsap.timeline({ paused: true });
      
      // SKILL.md: ENTRANCE ONLY (gsap.from), no exit animation.
      // Transition between scenes handled by root composition's transition layer.
      // Scene duration = 34s (14-48s in root timeline)
      
      const LINE_TIMES = {{LINE_TIMES_JSON}};  // [{start: 0.0, duration: 8.5}, ...]
      
      LINE_TIMES.forEach((t, i) => {
        // Entrance: fade in + slight y rise
        tl.from(`.body-line[data-line="${i}"]`, {
          y: 30, opacity: 0,
          duration: 0.4, ease: 'power3.out'
        }, t.start);
        
        // After this line ends, BEFORE next line: tl.set to opacity:0 INSIDE timeline
        // (SKILL.md Rule #10 — tl.set inside timeline at correct time, not gsap.set on init)
        if (i < LINE_TIMES.length - 1) {
          tl.set(`.body-line[data-line="${i}"]`, { opacity: 0 }, t.start + t.duration);
        }
      });
      
      window.__timelines["scene-body"] = tl;
    </script>
  </div>
</template>
```

**핵심**: 
- `.scene-content { display:flex; flex-direction:column; justify-content:flex-end; padding:220px 80px 270px 80px }` — SKILL.md flex+padding 패턴
- `position: absolute` 0 사용 (decoratives X — text는 content)
- 각 line opacity 초기 CSS (`opacity: 0`) — `gsap.set()` 안 씀
- `tl.from()` entrance만, exit는 `tl.set()` 으로 timeline 안에서 (SKILL.md Rule #10)
- 다음 line이 보이면 이전 line은 사라짐 (segment swap, overlap 0)

### 3.4 다른 4 scenes 동일 패턴

- `scene-hook.html`: 1 line, gsap.from y+opacity
- `scene-scripture.html`: scripture-card decorative (absolute OK), text는 flex
- `scene-austerity.html`: 1 line 명조 검은배경
- `scene-outro.html`: 마지막 — entrance + final fade-out 허용 (SKILL.md 예외)

### 3.5 Shader transitions

`@hyperframes/shader-transitions` 정식 패키지 사용. 우리 직접 코딩 X.
- Hook → Scripture: dissolve transition
- Body → Austerity: dissolve transition

```bash
ssh quant@100.104.121.7 'cd /home/quant/hyperframes-render && npm install @hyperframes/shader-transitions'
```

Root index.html 에 transition 등록 — SKILL.md transitions reference 정독 후 정확 패턴.

### 3.6 Lint + Validate

```bash
ssh quant@100.104.121.7 'cd ~/sermon-composition-v3 && npx hyperframes lint . && npx hyperframes validate .'
```

- lint: 0 errors 필수
- validate (WCAG contrast audit): warnings 모두 해결 (SKILL.md Quality Checks)

### 3.7 Gate B 통과 조건

- [ ] 5 sub-comp 파일 + root index.html + DESIGN.md + README.md 모두 존재
- [ ] `npx hyperframes lint .` 0 errors
- [ ] `npx hyperframes validate .` WCAG contrast warnings 0
- [ ] HP `/home/quant/hyperframes-render/compositions/sermon_short_v3/` 동기화

---

## 4. Phase C — sermon-app 통합 (분기만 추가)

### 4.1 `app/render/payload.py`

```python
def build_short_payload_v3(job_id, clip, *, jobs_dir, ...):
    # v2 와 거의 동일, composition만 sermon_short_v3
    payload = build_short_payload_v2(job_id, clip, jobs_dir=jobs_dir, ...)
    payload["composition"] = "sermon_short_v3"
    
    # v3 전용: BODY_LINES_HTML + LINE_TIMES
    # transcript_segments → 4-6 line으로 chunking (각 line ~8s)
    body_segs = [s for s in payload["transcript_segments"]
                 if 14.0 <= s["start"] <= 48.0]
    lines = []
    for seg in body_segs:
        # emphasis word를 inline span으로
        words_html = []
        for w in seg.get("words", []):
            cls = "emphasis" if w.get("is_emphasis") else ""
            tag = f'<span class="{cls}">{w["word"]}</span>' if cls else w["word"]
            words_html.append(tag)
        line_html = " ".join(words_html)
        lines.append({
            "html": line_html,
            "start": seg["start"] - 14.0,  # body-local timing
            "duration": seg["end"] - seg["start"],
        })
    
    payload["body_lines"] = lines  # max 4-6 lines for 34s body
    return payload
```

### 4.2 `app/server.py` 분기 추가

```python
comp = body.get("composition", "sermon_short_v3")  # default v3
if comp == "sermon_short_v3":
    payload = build_short_payload_v3(...)
elif comp == "sermon_short_v2":
    payload = build_short_payload_v2(...)
else:
    payload = build_short_payload(...)  # v1
```

### 4.3 HP `hf_server.py` placeholder 매핑

`compositions/scene-body.html` 의 `{{LINE_TIMES_JSON}}` `{{LINE_0_HTML}}` ... 등을 payload `body_lines` 로 치환.

### 4.4 `app/static/editor.html` select 추가

```html
<select id="hf-comp-select">
  <option value="sermon_short_v3" selected>v3 (SKILL.md 정석)</option>
  <option value="sermon_short_v2">v2 (체험)</option>
  <option value="sermon_short_v1">v1 (단순)</option>
</select>
```

### 4.5 Gate C 통과 조건

- [ ] dry_run POST `/api/job/<id>/render` with composition=sermon_short_v3 → payload preview 에 `body_lines` 4-6개 채워짐
- [ ] 회귀: composition=sermon_short_v2 명시하면 기존 그대로
- [ ] editor.html v3 default 토글 작동

---

## 5. Phase D — 종합 검증 (Gate E — 최종)

### 5.1 v2 vs v3 mp4 2개

같은 5분 sermon (`20260428_233109_u7DodpeoTzg_audio`) 의 0-60s 클립으로:

```bash
# v2
curl -X POST http://localhost:5001/api/job/.../render \
  -d '{"clip":{"start_sec":0,"end_sec":60},"composition":"sermon_short_v2"}'

# v3
curl -X POST http://localhost:5001/api/job/.../render \
  -d '{"clip":{"start_sec":0,"end_sec":60},"composition":"sermon_short_v3"}'
```

### 5.2 Frame 캡처 12개 (각 scene 2개 × 2 versions)

```
GDrive/p9_compare/
  v2_3s.png  v3_3s.png    # Hook
  v2_9s.png  v3_9s.png    # Scripture
  v2_30s.png v3_30s.png   # Body (핵심 비교)
  v2_44s.png v3_44s.png   # Body 후반
  v2_51s.png v3_51s.png   # Austerity
  v2_57s.png v3_57s.png   # Outro
```

### 5.3 8 quality criteria 측정

| # | 기준 | v2 | v3 | 측정 |
|---|---|---|---|---|
| 1 | Multi-scene visible | 4/5 | **5/5 필수** | frame 12개 직접 |
| 2 | Shader transition | partial | **2개 정식 작동** | transition frame |
| 3 | 자막 stroke + 잘림 | ⚠️ | **0 잘림** | Body 30/44s 핵심 |
| 4 | 골드 강조 sparingly | ✅ | ✅ | unchanged |
| 5 | 성구 카드 | ✅ | ✅ | unchanged |
| 6 | Austerity moment | ✅ | ✅ | unchanged |
| 7 | LUFS −16 | ⏸ | **±0.5** | ffmpeg loudnorm 측정 |
| 8 | Sync ±50ms | ✅ | ✅ | WhisperX 그대로 |

**목표**: 8/8 충족. **5/10 → 9/10 도달 측정**.

### 5.4 사용자 보고 형식

```markdown
## ✅ HF v3 SKILL.md 정석 재빌드 완료
### 변경 N 파일
- app/render/compositions/sermon_short_v3/* (root + 5 sub-comp + DESIGN.md + README.md)
- app/render/payload.py (+build_short_payload_v3)
- app/server.py (+v3 분기)
- app/static/editor.html (+v3 default select)

### Gate 결과
| Gate | 결과 |
|---|---|
| A — DESIGN.md | ✅/❌ |
| B — 5 sub-comp + lint + validate | ✅/❌ |
| C — payload v3 + 분기 | ✅/❌ |
| E — 8 criteria | N/8 충족 |

### v2 → v3 quality 점프
- 5/10 → N/10
- Body scene visible: ❌ → ✅
- 5/5 scenes: 4/5 → 5/5

### 시각 비교 frame 12개
GDrive/p9_compare/

### Remotion pivot 결정
- 8/8 충족 → Remotion 보류 (HF v3로 production-grade 도달)
- 5-7/8 → Remotion 검토 재개

### 다음 Phase
- LUFS audio_master 실 export 흐름 통합 (P5와 함께)
- P5 (음악 베드 5곡) — 1.5일
- P4 (sermon_reel_v1 — 멀티클립 reel) — 2일
```

---

## 6. 위험 + 대응

| 위험 | 대응 |
|---|---|
| `data-composition-src` cross-origin file 로드 실패 | HP에 모든 파일 같은 디렉토리 배치 (CORS 우회) |
| Sub-comp의 GSAP timeline auto-nest 안 됨 | SKILL.md "Framework auto-nests sub-timelines" 재정독, `window.__timelines["scene-body"] = tl` 등록 확인 |
| Body 4-6 line chunking 시 transcript 단위 부정합 | Whisper segment를 그대로 line으로, 6개 초과 시 가장 짧은 segments merge |
| Pretendard / Noto Serif KR 사용 시 lint warning | SKILL.md typography reference 정독, `font-family` CSS 선언 + 컴파일러가 자동 embed |
| transitions 패키지 install 실패 | `@hyperframes/shader-transitions` 공식 npm install. 실패 시 CSS-only crossfade로 graceful fallback |
| WCAG validate warnings | DESIGN.md 색상 대비 조정 (gold #D4AF37 on dark OK 4.5:1+, light bg 시 darker gold) |

---

## 7. 보고 + 커밋

### 7.1 HANDOVER 작성
`HANDOVER_HF_v9_skill_rebuild.md` — Gate A/B/C/E 결과 + 12 frame 경로 + 8 criteria 측정 + Remotion pivot 결정

### 7.2 commit 단위
```
feat(v3-A): DESIGN.md (visual identity gate)
feat(v3-B): 5 sub-compositions (scene-hook/scripture/body/austerity/outro) + root index.html + transitions
feat(v3-C): payload v3 + server 분기 + editor v3 default
feat(v3-E): 종합 검증 — v2 vs v3 frame 12 + 8 criteria 측정
```

### 7.3 push
`main` 직접 push (sermon-app 단일 branch).

---

## 8. 환경 (변동 없음)

| 항목 | 값 |
|---|---|
| Mac sermon-app | `/Users/.../sermon-app` |
| HP hf-server | http://100.104.121.7:8770 |
| HP whisperx-server | http://100.104.121.7:8771 |
| HP ollama | http://100.104.121.7:11434 |
| Mac Tailscale | 100.89.99.106 |
| Gitea | http://100.116.4.84:3000/quant/sermon-app |
| HF Skill repo | https://github.com/heygen-com/hyperframes |

---

## 9. 즉시 다음 액션 (자비스 순서)

1. § 0 시작 절차 (15분) — SKILL.md + 4 references + STORYBOARD.md 정독
2. § 2 Phase A — DESIGN.md (1시간) → Gate A
3. § 3 Phase B — 5 sub-comp + transitions (4-6시간) → Gate B (lint + validate pass)
4. § 4 Phase C — sermon-app 분기 (1시간) → Gate C
5. § 5 Phase D — 종합 검증 + 12 frame + 8 criteria (1-2시간) → Gate E
6. § 7 commit + push + HANDOVER + 사용자 보고

총 1.5일 (8-10시간 effective).

---

## 10. 핵심 다른점 (v2 vs v3)

| 항목 | v2 (실패) | v3 (정석) |
|---|---|---|
| 파일 구조 | 단일 60s `index.html` | root + 5 sub-comp 분할 |
| `.scene-content` | `position:absolute; top:1080px` | `width:100%;height:100%;padding;flex` |
| 자막 위치 | absolute 컨테이너 | flex `justify-content: flex-end` (lower-third equivalent) |
| Exit 애니메이션 | 있음 (Body chunk fade-out) | **없음** (transition이 exit 담당) |
| `gsap.set()` 사용 | 시작 시 모든 wordSpans opacity:0 | timeline 안 `tl.set()` (SKILL.md Rule #10) |
| Visual Identity | brief 인라인 | DESIGN.md 먼저 (Gate A) |
| Transitions | 없음 또는 자체 코딩 | `@hyperframes/shader-transitions` 정식 |
| Validate | lint만 | lint + WCAG contrast audit |

이 10가지 차이가 Body 깨짐의 정확한 원인. SKILL.md 100% 준수 시 v3는 작동 보장.

---

## 변경 이력

| 버전 | 일자 | 변경 |
|---|---|---|
| v1.0 | 2026-05-03 | 최초 — github SKILL.md 정독 후 v3 정석 재빌드 |
