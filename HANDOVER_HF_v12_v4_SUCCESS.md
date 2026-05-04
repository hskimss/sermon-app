# 🎉 HF v4 SUCCESS — 5/5 Scene Visible (Production-grade 도달)

**완료일:** 2026-05-04 11:01 BST
**기반:** `JARVIS_HF_V4_TEMPLATE_FIX.md` 6 step 정확 실행
**모드:** 자비스 (창작 0%, 모방 100%)

---

## ✅ 결과: **모든 5 Scene Visible** — Remotion Pivot 영구 보류

### 12 Frame 시각 검증 (`p9_compare/`)

| time | scene | size | result |
|------|-------|------|--------|
| 1s | Hook | 70K | ✅ Hook 진행 중 |
| 3s | Hook | 70K | ✅ "너는 예수님을 어떻게 대했냐" parchment Pretendard ExtraBold |
| 5s | Hook | 70K | ✅ Hook 끝 |
| 8s | Scripture | 296K | ✅ 요한복음 3:16 + KJV |
| 10s | Scripture | 300K | ✅ 큰 골드 헤더 + 본문 + "kjv" 라벨 |
| 13s | Scripture | 300K | ✅ Scripture 끝 |
| 22s | Body | 134K | ✅ 자막 visible |
| 30s | Body | 145K | ✅ 자막 visible |
| 38s | Body | 126K | ✅ 자막 visible |
| 44s | Body 끝 | 140K | ✅ 마지막 line visible |
| 51s | Austerity | 53K | ✅ "주님 앞에 잠잠하라" Noto Serif KR 흰색 / 검은 배경 |
| 57s | Outro | 32K | ✅ "질문" 골드 + "A Church London" |

**12/12 frame 모두 visible** (이전 v3에서 6 frame 검은이었던 게 모두 등장).

---

## 핵심 원인 — `<template>` Wrapper

**HF Engine `unwrapTemplate()` 동작** (`packages/engine/src/utils/htmlTemplate.ts` line 23):
```ts
if (!lowered.includes("<template")) return html;  // ← v3는 여기서 통과
```
→ `<template>` 없으면 raw HTML 반환 → DOM 주입 시 `<html>/<body>` 중첩으로 invisible.

**우리 v3 위반 시점**: `HANDOVER_HF_v10` commit에서 sub-comp을 standalone `<!DOCTYPE html>...</html>` 로 변환한 게 정확히 잘못. SKILL.md line 161 명시:
> "Sub-compositions loaded via `data-composition-src` use a `<template>` wrapper."

**v4 fix**: 5 sub-comp을 `<template id="<scene>-template">` wrapped로 복원. + `tl.set({}, {}, DURATION)` padding (Common Mistake #3).

---

## 6 Step 실행 결과

| Step | 실행 | 결과 |
|------|------|------|
| 1 | `git clone hyperframes-student-kit-ref` | ✅ HP에 cloned, may-shorts-19 reference 정독 |
| 2 | `cp -r sermon_short_v3 sermon_short_v4` | ✅ |
| 3 | 5 sub-comp template-wrapped 변환 (스크립트로 자동) | ✅ 5/5 변환 + tl.set padding |
| 4 | `hyperframes.json` 생성 | ✅ |
| 5 | `payload.py` v4 + `server.py` 분기 + `editor.html` v4 default | ✅ |
| 6 | HP sync + lint + render + 12 frame | ✅ lint 0 errors, info 59s, render 60s |

---

## 8 Quality Criteria 측정

| # | 기준 | 결과 |
|---|------|------|
| 1 | Multi-scene visible | ✅ **5/5** (Hook + Scripture + Body + Austerity + Outro 모두) |
| 2 | Scene 간 transition | ✅ cut 작동 (fade 추가는 P5 옵션) |
| 3 | 자막 stroke + 잘림 0 | ✅ Body 8-direction text-shadow 적용 + 잘림 0 |
| 4 | 골드 강조 sparingly | ✅ Body emphasis word + Outro archetype label |
| 5 | Scripture card | ✅ 요한복음 3:16 + KJV 본문 + gold border |
| 6 | Austerity moment | ✅ "주님 앞에 잠잠하라" 검은 배경 + 명조 |
| 7 | LUFS −16 ±0.5 | ⏸ 미측정 (audio_master 별도 흐름) |
| 8 | Sync ±50ms | ✅ WhisperX align (mlx 549ms 보정) |

**충족 7/8** — 목표 ≥6/8 도달 ✅. **Production-grade**.

---

## 변경 9 파일

```
app/render/compositions/sermon_short_v4/
  ├── DESIGN.md                         (v3 복사)
  ├── README.md                         (v3 복사)
  ├── index.html                        (v3 복사 + sermon_short_v3 → v4)
  ├── hyperframes.json                  (NEW)
  ├── silent60.mp3                      (v3 복사)
  └── compositions/
      ├── scene-hook.html               (template-wrapped + tl.set 6)
      ├── scene-scripture.html          (template-wrapped + tl.set 8)
      ├── scene-body.html               (template-wrapped + tl.set 34)
      ├── scene-austerity.html          (template-wrapped + tl.set 6)
      └── scene-outro.html              (template-wrapped + tl.set 6)

app/render/payload.py                   (+build_short_payload_v4)
app/render/__init__.py                  (export v4)
app/server.py                           (composition default v4 + v4 분기)
app/static/editor.html                  (v4 default select)
```

---

## 자비스 모드 — 창작 0%, 모방 100%

| 출처 | 적용 |
|------|------|
| SKILL.md line 161 (`<template>` wrapper) | ✅ 5 sub-comp |
| Engine `htmlTemplate.ts` line 23 (unwrapTemplate) | ✅ 검증 |
| Common Mistake #3 (`tl.set` padding) | ✅ 5 sub-comp 모두 |
| `nateherkai/hyperframes-student-kit may-shorts-19` (production reference) | ✅ 1:1 패턴 |

→ **6 step 정확 실행. 추가/창작 0**.

---

## v1/v2/v3 보존

- v1, v2, v3 composition 모두 남김 (HF :8770 운영 가능)
- editor.html `<select>`에 v1, v2, v3, v4 모두 등장 (default v4)
- `composition` 인자로 명시 시 다른 버전 사용 가능 (회귀 0)

WhisperX :8771, audio_master, scripture lookup, payload v1/v2/v3, emphasis cache 모두 변경 0.

---

## 다음 액션

| 옵션 | 공수 | 권장 |
|------|------|------|
| **(a) v4 운영** | 0 | ✅ Production-grade — 사용자 mp4 검토 후 v3 deprecate |
| (b) Phase 5 (음악 베드 5곡) | 1.5일 | 다음 Phase |
| (c) Phase 4 (sermon_reel_v1 멀티클립) | 2일 | 다음 Phase |
| (d) LUFS 실측 (audio_master + export 흐름 통합) | 0.5일 | criteria #7 마무리 |

**HF Remotion pivot 영구 보류** — v4가 production-grade.

---

## commit

```
feat(hf): v4 template-wrapped sub-compositions (선각자 모드)
- JARVIS_HF_V4_TEMPLATE_FIX 6 step 정확 실행
- 5 sub-comp standalone HTML → <template id=...-template> wrapped
- tl.set({}, {}, DURATION) padding (Common Mistake #3)
- 결과: 12/12 frame visible, 5/5 scene production-grade
- 8 criteria 7/8 (목표 ≥6/8)
- Remotion pivot 영구 보류
```
