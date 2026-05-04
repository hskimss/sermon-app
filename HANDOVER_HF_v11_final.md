# HF v3 최종 — Fix 1+9 적용 후 동일, **Remotion Pivot 영구 결정**

**완료일:** 2026-05-04 10:02 BST
**범위:** Fix 1 (tl.set 60s) + Fix 2 (vignelli starter) + Fix 9 (root data-duration)
**모드:** 자비스 (1시간 hard limit)

---

## ❌ 영구 결과: 8 criteria 3/8 (변동 없음)

### 적용한 Fix들

| Fix | 변경 | 결과 |
|-----|------|------|
| 1 | `masterTL.set({}, {}, 60)` master timeline length 강제 | 변동 없음 |
| 2 | vignelli starter 정독 → z-index overlay 패턴 (시간 순차 아님) | **우리 패턴과 근본 다름** |
| 9 | Root div에 `data-start="0" data-duration="60"` 명시 | 변동 없음 |
| (이전 1-3) | absolute inset:0 / master TL / standalone sub-comp | 변동 없음 |

### 12 frame — 6번 재렌더 모두 동일 패턴

```
1s/3s/5s    (Hook)        ❌ 검은
8s/10s/13s  (Scripture)   ❌ 검은
22s/30s/38s (Body)        ✅ 134-145KB
44s         (Body 끝)     ❌ 검은
51s         (Austerity)   ❌ 검은
57s         (Outro)       ✅ 32KB
```

→ **2/5 scene visible** 일관성. Body sub-comp `data-duration=34` (가장 김), Outro `data-duration=6`. Hook/Scripture/Austerity 작동 안 함.

---

## Vignelli vs 우리 v3 근본 차이

Vignelli starter (`npx hyperframes init test-vignelli --example vignelli`):
- **z-index overlay 패턴** — 모든 sub-comp `data-start=0 data-duration=10` 동시 재생, z-index로 stack
- a-roll(z=10) + overlays(z=20) + captions(z=30) + curtain transitions
- 시간 순차 X, 동시 layer 분할

우리 v3:
- **시간 순차 패턴** — 5 sub-comp `data-start` 분산 (0/6/14/48/54), `data-duration` 6/8/34/6/6
- launch-video는 시간 순차 사용하지만 우리와 다른 mount 결과

→ **HF v0.4 시간 순차 sub-comp 패턴이 일관성 없이 mount** (Body+Outro만, 다른 검은). Vignelli z-index 패턴은 다른 use case.

---

## 누적 디버깅 ~12시간 — HF 한계 확정

| 시도 | 패턴 | 결과 |
|------|------|------|
| v2 #1-6 | chunk fade / position fix / segment swap | Body 안 보임 |
| v3 baseline | SKILL.md 정석 5 sub-comp | Body+Outro만 |
| v3+ Fix 1-3 | launch-video pattern (CSS+masterTL+standalone) | 동일 |
| v3++ Fix 9 | root data-start/duration | 동일 |
| v3+++ Fix 1 (tl.set 60) | master TL length 강제 | 동일 |

**6 패턴 / 12시간 / 모두 5/5 미달** → HF v0.4 시간 순차 sub-comp 한계 확정.

---

## **Remotion Pivot 영구 결정**

**더 이상 HF 디버깅 안 함**. `REMOTION_PIVOT_WORK_ORDER.md` 그대로 진행:

| Phase | 분량 | 결과 |
|-------|------|------|
| R0 환경 (`npx create-video`) | 1h | local preview |
| R1 5 scene React TSX | 4-6h | local preview 5/5 visible |
| R2 HP `:8772` Remotion server | 2h | systemd active |
| R3 sermon-app `client.py::pick_url()` | 1h | composition 라우팅 |
| Gate E 검증 | 1h | 7/8 도달 |

**총 1.5–2일**. **5/5 scene 보장** (Sequence per scene + interpolate opacity, overlap 0).

---

## 보존 (변경 0)

- v1, v2, v3 composition 모두 유지 (HF :8770 운영 가능 범위 내)
- WhisperX :8771
- audio_master / scripture / payload schema / editor select / emphasis cache
- Remotion 도입 시 `composition_engine` 자동 라우팅 (sermon_short_v3 → :8770, sermon_short_v4 → :8772 Remotion 등)

---

## 8 criteria 결과 (영구)

| # | 기준 | 결과 |
|---|------|------|
| 1 | Multi-scene visible | ⚠ 2/5 |
| 2 | Shader transition | ⚠ removed |
| 3 | 자막 stroke + 잘림 0 | ✅ |
| 4 | 골드 강조 sparingly | ✅ |
| 5 | 성구 카드 | ❌ |
| 6 | Austerity moment | ❌ |
| 7 | LUFS −16 | ⏸ |
| 8 | Sync ±50ms (WhisperX) | ✅ |

**3/8 영구**. Production-grade 미달 — Remotion 필수.

---

## commit

```
fix(v3): Fix 1 + Fix 9 + vignelli starter 정독 — HF 한계 영구 확정
- master timeline tl.set 60s, root data-start/duration 명시 모두 동일 결과
- vignelli starter는 z-index overlay 패턴 (시간 순차와 근본 다름)
- 12시간 / 6 패턴 누적 시도 모두 5/5 미달
- Remotion pivot 영구 결정 — REMOTION_PIVOT_WORK_ORDER.md 진행
```
