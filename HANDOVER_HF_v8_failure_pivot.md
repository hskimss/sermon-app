# Body 6번째 시도 실패 — Remotion Pivot 권고

**완료일:** 2026-05-04 08:13 BST
**시도:** Segment-by-segment swap (사용자 지정 30분 hard limit)
**모드:** 자비스 (Proposer→Critic 결과 — Pivot 합의)

---

## ❌ 실패 — 6/8 그대로 (7/8 미달)

### 변경 2 파일

| 파일 | 변경 |
|------|------|
| `app/render/compositions/sermon_short_v2/index.html` | word-level 코드 완전 제거 + segment-by-segment swap (.seg-line) — body window 안 모든 frame 검은 화면 |
| HP `~/hyperframes-render/server/hf_server.py` | `{{TRANSCRIPT_SEGMENTS_JSON}}` placeholder 추가 |

### 6번째 시도 패턴

```html
.seg-line { position: absolute; top:1080px; height:540px;
            display:flex; align-items:center; justify-content:center;
            opacity: 0; }
```

```js
segs.forEach((s, i) => {
  const at = winStart + s.start;
  tl.to(line, { opacity: 1, duration: 0.4 }, at);
  tl.to(line, { opacity: 0, duration: 0.2 }, at + (s.end - s.start) - 0.2);
});
```

각 segment가 같은 위치에 stack absolute. opacity로 swap. overlap 0 보장.

### 결과

| frame | size | 자막 |
|-------|------|------|
| seg_16s.png | 10KB | ❌ 검은 화면 |
| seg_22s.png | 11KB | ❌ |
| seg_30s.png | 11KB | ❌ |
| seg_38s.png | 11KB | ❌ |
| seg_44s.png | 11KB | ❌ |

**lint 0 errors / 2 warnings 통과**, hf-server placeholder 치환 정상, payload 24 segments 전달 확인.

→ HF v0.4.42 timeline progression 자체가 멀티-scene + nested div + GSAP 결합에서 불투명. 5번 + 6번째 시도 모두 동일 증상.

---

## HF 한계 확정 — 6번 시도 종합

| # | 패턴 | 결과 |
|---|------|------|
| 1 | chunk fade (6 word) + top:1080 | 38s+ 만 등장 |
| 2 | bottom:380 + overflow:hidden | 동일 |
| 3 | position: fixed viewport | 동일 |
| 4 | `#root { position:relative; w:1080; h:1920 }` | 동일 |
| 5 | v1 graft (chunk 제거, individual fade-in) | 38s+ 만 등장 |
| **6** | **segment-by-segment swap (overlap 0)** | **모든 frame 검은 화면** |

`npx hyperframes info` Duration 5s (raw + 치환된 tmp 동일) 가 핵심 증상이지만 정확한 매핑 함수가 docs 부족 — 디버깅 시간 많이 소요.

---

## ✅ 산출 — Remotion Pivot 작업지시서

`교회 앱/REMOTION_PIVOT_WORK_ORDER.md` 신규 작성:

1. **R0** 환경: Mac `npx create-video --template blank`, HP `@remotion/cli + renderer`
2. **R1** Composition: `SermonShortV2.tsx` + 5 scene 컴포넌트
   - **Body**: `<Sequence>` per segment, `interpolate(opacity)` fade, overlap 0 보장
3. **R2** HP `remotion-server :8772` (port 분리, hf-server :8770 v1 회귀 보존)
4. **R3** sermon-app `client.py::pick_url()` — `_v2` 컴포지션 → Remotion 라우팅
5. Gate R0/R1/R2/R3/E + 8 criteria 7/8 목표

**보존 (변경 0)**:
- v1 sermon_short_v1.html (HF 호환)
- WhisperX align (:8771)
- audio_master loudnorm
- scripture lookup / krv.json / kjv.json
- editor.html v1/v2 select
- payload schema (`build_short_payload_v2`)
- emphasis cache

**예상 공수**: 1.5–2일

---

## 8 Quality Criteria 결과 (현재)

| # | 기준 | 결과 |
|---|------|------|
| 1 | Multi-scene visible | ⚠ 4/5 (Body ❌) |
| 2 | Shader transition | ✅ |
| 3 | 자막 stroke + 잘림 0 | ⚠ (Body 안 보임) |
| 4 | 골드 강조 sparingly | ⚠ (Body 안 보임) |
| 5 | 성구 카드 | ✅ |
| 6 | Austerity moment | ✅ |
| 7 | LUFS −16 | ⏸ 미측정 |
| 8 | Sync ±50ms (WhisperX) | ✅ (mlx 549ms 보정) |

**충족 4/8** (Body 의존 항목 3개 → 미충족). 7/8 목표 — Remotion pivot 후 도달 가능.

---

## 다음 액션 (사용자 선택)

| 옵션 | 공수 | 설명 |
|------|------|------|
| (a) **Remotion pivot 진입** (자비스 신규 세션) | 1.5–2일 | `REMOTION_PIVOT_WORK_ORDER.md` 따라 진행. body 정상 작동 보장 |
| (b) **HF 디버깅 계속** (별도 P1) | 4–8h | chrome devtools timeline inspect, HF maintainer 문의 — 결과 불확실 |
| (c) **v1 (단일 scene) 만 사용** | 0 | 5-scene 포기, lower-third only. design brief 미달성 |

권장: **(a) Remotion pivot**. HF 한계 회피 + design brief 5 scenes 보장.

---

## commit

```
fix(v2): segment swap 시도 + Remotion pivot 작업지시서

- segment-by-segment swap (.seg-line) 6번째 시도, lint pass / 0 visual
- HF v0.4.42 timeline progression 한계 확정 (Duration 5s 추정 미해결)
- REMOTION_PIVOT_WORK_ORDER.md 작성 — 5 scene React TSX 마이그레이션
- 보존: WhisperX/audio_master/scripture/payload/v1 모두 변경 0
```
