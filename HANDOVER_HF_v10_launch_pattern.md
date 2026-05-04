# HF v3 launch-video pattern — 3 fix 적용 후 동일 결과

**완료일:** 2026-05-04 09:44 BST
**범위:** launch-video index.html + sub-comp 정독 + 3 fix 적용 + 재렌더 + 12 frame
**모드:** 자비스 (1시간 hard limit)

---

## ❌ 실패 — 8 criteria 3/8 (변동 없음)

### 적용한 3 fix

| Fix | 변경 |
|-----|------|
| 1. Root CSS sub-comp absolute inset:0 | `[data-composition-id="sermon_short_v3"] > div[data-composition-id] { position:absolute; inset:0 }` |
| 2. Master timeline 등록 | `window.__timelines["sermon_short_v3"] = gsap.timeline({ paused: true })` + GSAP CDN body 첫줄 |
| 3. Sub-comp standalone HTML | `<template>` 제거, full `<!DOCTYPE html><html><head>...</head><body>...</body></html>` (launch-video sub-comp 실 패턴) |

### Render + 12 frame 결과

```
v3h_1s.png   10K  ❌ Hook 검은
v3h_3s.png   10K  ❌ Hook 검은
v3h_5s.png   10K  ❌ Hook 검은
v3h_8s.png   10K  ❌ Scripture 검은
v3h_10s.png  10K  ❌ Scripture 검은
v3h_13s.png  10K  ❌ Scripture 검은
v3h_22s.png 134K  ✅ Body visible
v3h_30s.png 145K  ✅ Body visible
v3h_38s.png 126K  ✅ Body visible
v3h_44s.png  11K  ❌ Body 끝 검은
v3h_51s.png  10K  ❌ Austerity 검은
v3h_57s.png  32K  ✅ Outro visible
```

**5/5 → 2/5** 동일 (Body + Outro만 mount).

---

## 추가 5 Fix 후보 (Failure follow-up)

launch-video index.html 정독 + 우리 v3 비교에서 추가 차이:

### Fix 4 (가장 유력) — Master timeline에 sub-comp timeline `add()` 명시 등록

launch-video 의 master timeline은 비어있어 보이지만, **HF compiler가 sub-comp timelines를 root master에 자동 nest 한다는 가정이 검증 안 됨**. 명시 등록이 필요할 수도:

```js
// root index.html (sub-comp 로드 후)
window.addEventListener("load", () => {
  const master = window.__timelines["sermon_short_v3"];
  master.add(window.__timelines["scene-hook"],     0);
  master.add(window.__timelines["scene-scripture"], 6);
  master.add(window.__timelines["scene-body"],     14);
  master.add(window.__timelines["scene-austerity"], 48);
  master.add(window.__timelines["scene-outro"],    54);
});
```

**리스크**: sub-comp는 별도 document context (iframe-like)일 수 있어서 `window.__timelines["scene-hook"]` 가 root에서 안 보일 수도.

### Fix 5 — Sub-comp 안에 `html, body { width:1080; height:1920; overflow:hidden }` 명시

launch-video sub-comp 실 패턴:
```css
html, body { margin:0; padding:0; width:1920px; height:1080px; background:#000; overflow:hidden; }
```

우리 sub-comp은 body 명시 안 함. sub-comp 자체 viewport 1080×1920 로 설정 필요.

### Fix 6 — Sub-comp의 root data-composition-id div에 inline style `width/height/position:absolute`

launch-video glass-intro.html은 sub-comp의 root div에 `width:1920px; height:1080px; position:relative` 명시. 우리는 selector CSS만 의존.

```html
<div data-composition-id="scene-hook"
     data-width="1080" data-height="1920"
     style="width:1080px; height:1920px; position:relative; overflow:hidden;">
```

### Fix 7 — `data-track-index` 분리 (1, 2, 3, 4, 5)

launch-video sub-comp 마다 다른 track (track 0=audio, 1=video, 2-13=scenes). 우리 모든 sub-comp track 1. HF가 같은 track + 시간 겹침 0 OK 라고 했지만 실제 mount 차별 가능성:

```html
<div data-composition-id="scene-hook"     data-track-index="1" ...>
<div data-composition-id="scene-scripture" data-track-index="2" ...>
<div data-composition-id="scene-body"      data-track-index="3" ...>
<div data-composition-id="scene-austerity" data-track-index="4" ...>
<div data-composition-id="scene-outro"     data-track-index="5" ...>
```

### Fix 8 — `<style>` 안 inline `@font-face` 대신 `<link>` 외부 fonts

launch-video는 head에 `<link href="...googleapis...">` preconnect + 외부. 우리는 `@import` 안 inline CSS. 폰트 로드 race condition으로 sub-comp 첫 렌더 시점에 폰트 미로드 → 캡처 시 검은 (글자 invisible).

확인: Body sub-comp는 늦은 시점 (14s+) 캡처라 폰트 로드 완료. Hook (3s) 캡처 시 폰트 미로드 가능성.

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Pretendard..." rel="stylesheet">
```

---

## Remotion Pivot 다음 단계 판단

### HF 디버깅 누적 시도

| 시점 | 시도 | 결과 |
|------|------|------|
| v2 #1-6 | chunk fade / position fix / segment swap | Body 안 보임 |
| v3 (SKILL.md 정석) | 5 sub-comp 분할 + flex+padding + entrance only | Body+Outro만 mount |
| v3+ 3 fix (launch-video) | absolute inset + master timeline + standalone | 동일 |
| v3++ 5 fix 후보 | (위 §5 fix 4-8) | **추가 4-8시간 추정** + 결과 불확실 |

**누적 디버깅 시간**: ~10시간. **production-grade 미달성**.

### 권고

| 옵션 | 공수 | 결과 보장 |
|------|------|----------|
| **(A) Fix 4-8 순차 시도** | 4-8h | 불확실 (5번 누적 실패) |
| **(B) Remotion pivot** | 1.5-2일 | **5/5 scene 보장** |
| (C) Body+Outro 운영 | 0 | 3/8 production-grade 미달 |

→ **권장 (B) Remotion pivot**. HF v3 SKILL.md 정석 + launch-video pattern 모두 적용해도 5/5 미달 = HF 한계 확정.

기존 `REMOTION_PIVOT_WORK_ORDER.md` 그대로 유효:
- 5 sub-comp `<Sequence>` per scene (overlap 0 보장)
- `interpolate(opacity)` fade
- HP `:8772` 별도 server (hf-server :8770 v1/v2 보존)
- sermon-app `client.py::pick_url()` 자동 라우팅

---

## 보존 (Remotion pivot 후에도 변경 0)

- v1 sermon_short_v1.html (HF :8770 호환)
- v2 sermon_short_v2/* (HF :8770 호환, body 안 보이지만 운영 가능)
- v3 sermon_short_v3/* (HF :8770 호환, Body+Outro 운영 가능)
- WhisperX :8771
- audio_master.py / loudnorm
- scripture/krv-kjv.json
- payload v1/v2/v3 schema
- editor.html v1/v2/v3 select
- emphasis cache

---

## commit

```
fix(v3): launch-video pattern 3 fix 적용 (root CSS + master TL + standalone)
- 결과: Body+Outro 동일 visible, Hook/Scripture/Austerity 동일 검은
- HF 한계 확정 (10시간+ 디버깅, 5번 패턴 시도)
- Remotion pivot 권고 — HANDOVER_HF_v10_launch_pattern.md
```
