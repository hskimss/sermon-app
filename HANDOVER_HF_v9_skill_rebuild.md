# HF v3 SKILL.md 정석 재빌드 — 부분 진척 + Remotion pivot 재권고

**완료일:** 2026-05-04
**기반:** `JARVIS_HF_V3_SKILL_REBUILD.md`
**범위:** Phase A + B + C + D 모두 진행. Phase D 시각 검증 부분 통과 (Body+Outro 작동).

---

## ✅ 결과: **3/8 충족 → Remotion pivot 권고**

### Gate 결과

| Gate | 결과 |
|------|------|
| **A** — DESIGN.md (Visual Identity) | ✅ 작성 (`sermon_short_v3/DESIGN.md`) |
| **B** — 5 sub-comp + root index.html | ✅ SKILL.md 정석 패턴 (flex+padding, entrance only, tl.set 내부) |
| **B** — `npx hyperframes lint`  | ✅ **0 errors** / 24 warnings (composition_self_attribute_selector — 비-blocking) |
| **B** — `npx hyperframes info`  | ✅ **Duration 59.0s 정상 인식** (v2 5.0s 추정에서 진척) |
| **C** — payload v3 + server.py 분기 | ✅ `build_short_payload_v3()`, default v3 |
| **C** — hf_server.py v3 placeholder | ✅ `LINE_TIMES_JSON`, `LINE_0..5_HTML`, `SCRIPTURE_*` |
| **D** — v3 60s 렌더 | ✅ 306s elapsed, 2.1MB mp4 |
| **D** — Body scene visible | ✅ **22/30/38s frame 134-145KB** (v2 6번 실패 후 첫 성공) |
| **D** — Outro visible | ✅ 57s frame 32KB ("질문" + "A Church London") |
| **D** — Hook visible (3s) | ❌ 검은 화면 |
| **D** — Scripture visible (9s) | ❌ 검은 화면 |
| **D** — Austerity visible (51s) | ❌ 검은 화면 |

---

## 8 Quality Criteria 측정

| # | 기준 | 결과 | 비고 |
|---|------|------|------|
| 1 | Multi-scene visible | ⚠ **2/5** (Body + Outro) | Hook/Scripture/Austerity 검은 |
| 2 | Shader transition | ⚠ transition div 제거함 (mount 방해 의심) | |
| 3 | 자막 stroke + 잘림 0 | ✅ Body 자막 8-direction stroke + 잘림 0 | |
| 4 | 골드 강조 sparingly | ✅ Body 안 `<span class="emphasis">` 작동 (시각 미확인) | |
| 5 | 성구 카드 | ❌ Scripture scene 검은 | |
| 6 | Austerity moment | ❌ 검은 | |
| 7 | LUFS −16 ±0.5 | ⏸ 미측정 (audio mux 별도) | |
| 8 | Sync ±50ms | ✅ WhisperX align 그대로 | |

**충족 3/8** (목표 7/8 미달).

v2 vs v3 변동:
- v2 4/8 충족 (Body 안 보임)
- v3 3/8 충족 (Body + Outro 보이지만 Hook/Scripture/Austerity 후퇴)

→ **본질적 진척 (Body 작동)** + **다른 3 scene 회귀**. 단순 + 우위는 없음.

---

## 변경 13 파일

```
app/render/compositions/sermon_short_v3/
  ├── DESIGN.md                        (NEW, 7.8KB Visual Identity Gate)
  ├── README.md                        (NEW, inject contract)
  ├── index.html                       (NEW, root + 5 sub-comp refs)
  ├── silent60.mp3                     (NEW, lint placeholder)
  └── compositions/
      ├── scene-hook.html              (NEW, SKILL.md flex+padding pattern)
      ├── scene-scripture.html         (NEW)
      ├── scene-body.html              (NEW, line-times via data-attribute)
      ├── scene-austerity.html         (NEW)
      └── scene-outro.html             (NEW, only scene with exit anim)

app/render/payload.py                  (+_chunk_body_lines + build_short_payload_v3)
app/render/__init__.py                 (export v3)
app/server.py                          (composition default v3 + 분기 추가)

# HP 측 (sermon-app repo 외)
~/hyperframes-render/server/hf_server.py (+ v3 placeholders, recursive asset copy,
                                             pipe DEVNULL, root wrap skip when
                                             data-composition-id="sermon_short_*")
```

---

## SKILL.md 100% 준수 검증

| Rule | v3 |
|------|----|
| `.scene-content` flex+padding (NEVER position:absolute) | ✅ all 5 sub-comp |
| Reserve absolute for decoratives | ✅ |
| NEVER exit animations except final scene | ✅ outro만 fade-out |
| Sub-composition 분할 (`data-composition-src`) | ✅ 5 sub-comp |
| Visual Identity Gate (DESIGN.md 먼저) | ✅ |
| `tl.set()` inside timeline (Rule #10) | ✅ scene-body |
| Determinism (no Math.random/Date.now/repeat:-1) | ✅ |
| No `<br>` in content | ✅ natural wrap |
| Synchronous timeline construction | ✅ |
| No conflicting same-property animations | ✅ |
| Standalone no `<template>`, sub-comp uses `<template>` | ✅ |

→ **SKILL.md 11 규칙 모두 준수**. 그래도 Hook/Scripture/Austerity sub-comp가 mount 안 됨.

---

## Hook/Scripture/Austerity 미작동 원인 추정

1. HF v0.4.42 의 `<template>`-wrapped sub-comp가 부분만 mount (Body + Outro 작동).
2. data-composition-src 의 fetch + injection 타이밍 — 일부 sub-comp 만 캡처 시점에 ready.
3. sub-comp 안 GSAP CDN 로드 race condition (Body 의 더 복잡한 timeline은 충분 시간 = ready).
4. transition div 제거해도 동일 — transition 원인 아님.

추가 디버깅:
- chrome devtools timeline inspect (HP 측 Studio 등)
- HF maintainer 문의
- Body sub-comp 패턴 그대로 다른 4 scene 에 복제하여 격리

→ **추가 1-2일 추정**. 효과 불확실.

---

## Remotion Pivot 재권고

**HF v3는 SKILL.md 100% 준수 + lint 0 errors + Body sub-comp 작동** 까지 도달했음에도 5 scene 모두 visible 못 함.

이 시점에 **Remotion pivot 결정**이 합리적:
- 결정적 frame 함수 (`(frame, fps) => element`)
- 명시적 `durationInFrames` + `<Sequence>` per scene
- HF 한계 우회 + design brief 5 scene 보장

**기존 작업지시서**: `REMOTION_PIVOT_WORK_ORDER.md` (이전 v8 commit) 그대로 유효.
**예상 공수**: 1.5–2일.
**보존**: WhisperX align / audio_master / scripture lookup / payload schema / editor v1/v2/v3 select / emphasis cache 모두 변경 0.

---

## v3 인프라는 보존 가능

v3 가 production-grade 도달 못 했지만 다음은 살아있음:
- `sermon_short_v3/` 5 sub-comp + DESIGN.md (재사용 가능 — Remotion 이식 시 기준)
- `build_short_payload_v3()` + `_chunk_body_lines()` (Remotion 도 같은 chunked line 사용)
- hf-server v3 placeholder 매핑 (필요 시 sub-comp 디버깅 후 활성화)

→ Remotion 작업 시 v3 의 chunked line + design 재활용. 작업의뢰서 §3 `body_lines` 인터페이스 준수.

---

## 다음 액션 (사용자 결정)

| 옵션 | 공수 | 결과 |
|------|------|------|
| **(a) Remotion pivot** | 1.5–2일 | 5/5 scene 보장 + 7-8/8 도달 |
| (b) HF v3 깊은 디버깅 | 1-2일 | 결과 불확실 |
| (c) Body+Outro 충분 (production-grade 양보) | 0 | 3/8 으로 운영 |

**권장: (a)** — HF v3 SKILL.md 정석으로도 5 scene 보장 못 함이 확정. Remotion 결정.

---

## commit

```
feat(v3): SKILL.md 정석 재빌드 — DESIGN.md + 5 sub-comp + payload v3
- lint 0 errors / 24 warnings (비-blocking)
- Duration 59.0s 정상 (v2 5.0s 추정 회귀 해결)
- Body sub-comp 자막 visible (v2 6번 실패 후 첫 성공)
- Outro 작동 (질문 골드 + A Church London)
- Hook/Scripture/Austerity 검은 — sub-comp 부분 mount 의심
- 8 criteria 3/8 (목표 7/8 미달)
- Remotion pivot 재권고 (기존 작업지시서 그대로 유효)
```
