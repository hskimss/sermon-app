# P3 — 성구 자동 카드 인프라 완료

**완료일:** 2026-05-03 19:56 BST
**기반:** HF_PHASE_PLAN_v2.md §2 P3
**모드:** 자비스 (Proposer→Critic→Synthesizer)

---

## 산출

| 파일 | 역할 |
|------|------|
| `app/render/bible/__init__.py` | 패키지 export |
| `app/render/bible/loader.py` | `BibleStore` + `BookNameMapper` (66권 한↔영) + LRU 캐시 |
| `app/render/bible/krv.json` | **빈 placeholder** (라이선스 안내 포함, 사용자 직접 채움) |
| `app/render/bible/kjv.json` | KJV PD 시드 데이터 (요한복음 1·3·14, 마태 5·28, 롬 8, 빌 4, 시 23) |
| `app/render/scripture.py` | `lookup_verse()` 신규 + `detect_scripture_refs(lookup=True)` 확장 |
| `app/render/payload.py` | `refs[].text/translation` 자동 채움 |
| `app/render/__init__.py` | export 보강 |

---

## 검증

```
[OK] 5개 신규/수정 .py syntax 통과
[OK] lookup_verse('요한복음', 3, 16) → KJV 폴백 (krv 비어있어 자동 전환)
[OK] verse range (마태복음 5:3-4) 정상 결합 출력
[OK] 존재하지 않는 verse (나훔 1:7) → (None, None) 안전 반환
[OK] krv 비었음 / kjv 충전됨 — is_empty() 정확
[OK] HP /render → 15.3s 렌더 → 613KB mp4
[OK] 시각: 5s/8s 프레임에서 카드(요한복음 3:16 골드 헤더 + KJV 본문 + "kjv" 라벨) + 자막 + 브랜드 마크 동시 표시
```

샘플 프레임: `/tmp/p0_verify/p3_t5s.png`, `p3_t8s.png` (시각 검증 완료)

---

## 라이선스 처리

| 번역 | 상태 | 비고 |
|------|------|------|
| 개역개정 (신표준) | ❌ 자체 입력 금지 | 대한성서공회 © — 외부 공유 금지 |
| 개역한글 (1961) | ⚠ 확인 필요 | PD 가능성 있으나 명시 미확정 |
| KJV (1611) | ✅ Public Domain | 인프라 검증/데모 |

`krv.json` 안에 라이선스 경고 + 스키마 예시 동봉 — 사용자가 직접 채운 본문이 없으면 KJV 영문 자동 폴백.

---

## 자비스 모드 (Critic 발견 → 사전 반영)

| 발견 | 반영 |
|------|------|
| 한국어 본문 자체 입력은 저작권 위험 | krv.json 빈 placeholder + KJV 영문 폴백 동시 빌드 |
| `lookup_verse` 호출자가 매번 store 인스턴스 만들면 IO 폭증 | `@lru_cache(4)` `get_default_store()` |
| 책명 표기 차이 (`요한복음` vs `John`) | `BookNameMapper.to_english/to_korean` 양방향 + lookup 시도 시 자동 폴백 |
| `verse_end` 미지정 | `verse_end = verse_start` 정규화 후 range 처리 |
| `appears_at_sec`이 transcript의 절대 시각 — 클립으로 잘랐을 때 미스매치 | `detect_scripture_refs`가 `clip` 받아 clip-local 시각으로 자동 변환 |
| `lookup=True` 옵션 잊으면 카드 비어있음 | `payload.build_short_payload`에서 항상 `lookup=True` 강제 |

---

## 알려진 미해결 (다음 단계)

1. **약식 인용** (`성경에 보면…`, `예수님께서 말씀하시기를…`) — regex로 못 잡음 → P3 v2: Gemma 4 보강 단계
2. **한자/숫자 음역** (`요한복음 삼 장 십육 절` ← Whisper 발음 그대로) — 정규화 함수 추가 필요
3. **읽기 시간 정확도** — 현재 단순 `len/6 chars/sec`. 한글/영문/구두점 구분 + min/max clamp
4. **GSAP timeline 의 카드 fade 타이밍** — 현재 4s 등장에서 정확히 작동 (P3c 시각 통과)
5. **음악 1.5s drop** — P5 단계

---

## 다음 액션 옵션 (HF_PHASE_PLAN_v2 §3 우선순위)

| 옵션 | 공수 | 권장 시점 |
|------|------|----------|
| **P6** (editor.html 토글) | 1일 | 사용자가 매일 사용하는 UI 진입점 — P3 직후 권장 |
| **P4** (sermon_reel_v1) | 2일 | 멀티클립 워크플로 |
| **P5** (음악 베드) | 1.5일 | 청각 품질 |

`critical path = P3 → P6` (총 4일 안 진입). P3 완료 후 바로 **P6 진입 권장**.

---

## 환경 변수

| Key | Default | 용도 |
|-----|---------|------|
| `SERMON_BIBLE_TRANS` | `krv` | 기본 번역본 (없으면 KJV 폴백) |
| 기존: `HF_RENDER_URL`, `SERMON_APP_BASE_URL`, `HP_Z2_LLM` | 변경 없음 | |

---

## 사용자 옵션 — 한국어 본문 채우기

```bash
# krv.json 직접 편집 (저작권 확인 후)
edit app/render/bible/krv.json
# 또는 별도 번역 파일 추가
cp app/render/bible/krv.json app/render/bible/krv-1961.json
SERMON_BIBLE_TRANS=krv-1961 .venv/bin/python -m app.server
```

`books` 키 안에 한국어 책명 → chapters → verses 채우면 즉시 작동.
