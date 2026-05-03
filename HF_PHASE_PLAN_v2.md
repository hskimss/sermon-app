# HyperFrames P3–P8 순차 진행 설계서 v2

> 작성일: 2026-05-03 (P0+P1 완료 직후)
> 기반: HYPERFRAMES_DESIGN.md v1.0 + P0/P1 실측 결과 반영
> 목적: 남은 6개 Phase의 의존성 / 검증 / 일정 / 위험 정리

---

## 0. 현재 상태 스냅샷

| 컴포넌트 | 상태 | 위치 |
|---|---|---|
| HP HyperFrames v0.4.42 | ✅ active | hp-z2-llm `:8770` (systemd) |
| Pretendard / Noto Serif KR | ✅ 폰트 시스템 설치 | hp-z2-llm |
| sermon_short_v1 composition | ✅ 시각 검증 통과 | render8_frame.png 확인 |
| Mac sermon-app 렌더 endpoint | ✅ `/api/render/health` ok | port 5001 |
| Gemma 4 emphasis 캐시 | ✅ 골드 강조 작동 | per-job `llm_emphasis.json` |
| 성구 인용 regex | ✅ 66권 검출 | scripture.py |
| 성구 본문 표시 | ❌ 미구현 (regex만 + 카드 비어있음) | 미구현 |
| Highlight reel composition | ❌ 미구현 | 미구현 |
| 음악 베드 mixing | ❌ 단일 트랙만 | 미구현 |
| editor.html → HF 토글 버튼 | ❌ 수동 curl만 | 미구현 |
| Longform composition | ❌ 미구현 | — |
| B-roll 자동 매칭 | ❌ 미구현 | — |

---

## 1. 의존성 그래프

```
P3 (성구 카드)  ──┬─→ P4 (reel)  ──┐
                 │                  │
P5 (음악 베드)   ─┴────────────────┼─→ P6 (editor 통합 토글)
                                    │       ↓
                                    │   사용자 UX 완성 ✅
                                    │
                                    └─→ P7 (longform)  ──→ P8 (B-roll)
```

핵심 — **P6는 P3+P4+P5가 안정된 후**에 묶어서 UI 통합. 그 전엔 curl로 충분.

P7/P8은 별도 트랙으로, P6 끝나고 사용자 1주 운영 데이터 본 뒤 진입.

---

## 2. Phase별 설계

### **P3 — 성구 자동 카드** (highest theological value)

**산출물**:
1. `app/render/bible/` — 개역개정 본문 라이브러리 (자체 JSON, 약 4MB)
2. `app/render/scripture.py` 확장 — `lookup_verse(book, chapter, verse_start, verse_end) → text`
3. `app/render/payload.py` 확장 — `scripture_refs[i]` 에 `text`, `appears_at_sec` 채움 (현재 빈 배열)
4. composition `sermon_short_v1.html` — 카드 fade-in 0.6s + hold (read_time + 1.5s) + fade-out 0.4s 검증

**서브 단계**:
- P3a: 개역개정 본문 JSON 빌드 (1일)
  - 소스: `crosswire.org/wiki/Module:Korean_RVAUTH` (PD) 또는 `bibleapi.io/v1/bibles` 공개 데이터 수집 후 JSON 변환
  - 형식: `bible/krv.json` → `{books: {요한복음: {chapters: {3: {verses: {16: "하나님이 세상을…"}}}}}}` (2MB압축 가능)
  - 라이센스 확인 — 개역개정은 대한성서공회 저작권 → **공유 금지**, 자체 사용은 허용. **README에 "내부 비공개" 명시.**
- P3b: lookup 함수 + payload 확장 (반나절)
- P3c: 카드 등장 타이밍 — 인용된 verse가 transcript에 나타난 시점 ± 0.5초 → fade-in (반나절)

**Gate (검증 통과)**:
- [ ] regex로 "요한복음 3:16" 검출되는 transcript에서 실제 본문 카드 등장
- [ ] 카드 hold 시간 = 본문 read_time × 0.25초/글자 + 1.5s silence
- [ ] 카드 등장과 동시에 자막 word 강조 일시 정지 (페르소나 #3 §3)
- [ ] 음악 (P5 도입 시) 1.5s drop
- [ ] 시각 검증: render mp4에서 verse text 카드 보임

**위험**:
- 개역개정 저작권 — 공개 시 문제. 자체 사용/내부 콘텐츠 출처 표시로 우회.
- regex가 약식 인용 ("성경에 보면…") 못 잡음 — Gemma 4 보강은 P3 v2에 별도 추가
- Whisper transcript에서 "요한복음 3장 16절"이 "요한복음 삼 장 십육절" 같은 발음 그대로 전사된 경우 — 한자/숫자 정규화 필요

**예상 공수**: **3일**

---

### **P6 — editor.html → HF 시각화 토글** (UX 완성)

**산출물**:
1. editor.html `📦 5개 export` / `🎞 reel` 버튼 옆에 `[ ] HF 시각화` 체크박스
2. 체크 시: `/api/job/<id>/render` 호출, polling 후 mp4 미리보기
3. 진행 상태 표시 — "렌더 중... NN초 남음"
4. 실패 시 fallback — bare FFmpeg export 자동 진행 + 경고 표시

**Gate**:
- [ ] 체크박스 ON → 단일 클릭으로 HF mp4 받음
- [ ] 체크박스 OFF → 기존 FFmpeg export 그대로 동작
- [ ] HP 다운 시 자동 fallback + 사용자 알림
- [ ] 시각 검증: 사용자가 30초 안에 mp4 본다

**위험**:
- HP unreachable 시 처리 — 이미 P2에서 502 응답 정의됨, UI에 surfacing만 필요
- 렌더 시간 polling 패턴 — 5초 간격 표준

**예상 공수**: **1일**

**의존**: P3 완료 (단순 short만 시각화는 P3 없이도 가능, 단 이미 작동 중이니 묶어서 출시 권장)

---

### **P4 — sermon_reel_v1 (멀티클립 highlight reel)**

**산출물**:
1. `app/render/compositions/sermon_reel_v1.html` (16:9, 1920×1080)
2. composition 구조:
   - Intro 카드 (3초): 설교 제목 + 날짜 (Sandoll 명조)
   - 클립 1 (60s): short composition 재사용 + 가로 비율 적응
   - Austerity transition (1.5s): 검은 화면 + 흰 명조 한 줄 + silence (페르소나 #3 §3)
   - 클립 2-N: 반복
   - Outro (3초): A Church London 로고
3. payload 빌더 확장 — `clips: [{...}]` array, narrative arc로 정렬됨 (Gemma 4 rearrange_for_arc 활용)
4. Mac `/api/job/<id>/llm-highlight-reel` 에 `render_engine: hyperframes` 옵션

**Gate**:
- [ ] 5개 클립 reel 1개 mp4 생성 (≤ 5분)
- [ ] austerity transition 클립 사이마다 작동
- [ ] cuts/min ≤ 10 (페르소나 #3 §5)
- [ ] 시각 검증: 흐름 자연스러움 확인

**위험**:
- 가로 비율(16:9) vs 세로(9:16) 자막 위치 재조정 필요
- HP 단일 머신에서 5클립 ×60s = 5분 영상 렌더 시간 측정 (예상: 8-12분, 분산 미지원)
- 오디오 concat — 클립 사이 silence 정확히 1.5s

**예상 공수**: **2일**

---

### **P5 — 음악 베드 + sidechain ducking**

**산출물**:
1. `app/render/audio/beds/` — 5곡 큐레이트 (Epidemic Sound personal license 또는 PD 대체)
   - felt piano 2곡, low pad 2곡, 가야금/대금 1곡 (페르소나 #3 §A)
2. composition `<audio data-track-index="2">` 추가 — bed 트랙
3. hf-server FFmpeg 단계에 `sidechaincompress` filter 삽입:
   ```
   ffmpeg ... -filter_complex "[1:a][0:a]sidechaincompress=threshold=0.05:ratio=8:attack=30:release=400[bed];[0:a][bed]amix=inputs=2:weights=1.0 0.6"
   ```
4. 성구 카드 등장 시 음악 1.5s drop — composition JS에서 GSAP timeline에 `gsap.to(bedAudio, {volume:0, duration:0.3}, scriptureStart - 0.3)` 추가

**Gate**:
- [ ] LUFS 측정: voice -16, bed -22 (page #2 §3)
- [ ] sidechain ratio 8:1, 12-18dB ducking 작동
- [ ] 성구 카드 시 silence 명확
- [ ] 청취 검증 (사람) — 베드 들리지만 음성 또렷

**위험**:
- 라이센스 — Epidemic Sound 월 €15. 또는 Pixabay/Uppbeat 무료 (퀄리티 낮음).
- HyperFrames `<audio>` 트랙 sync 정확도 — 1프레임 오차 가능

**예상 공수**: **1.5일** (큐레이션 0.5일 + 통합 1일)

---

### **P7 — sermon_longform_v1 (풀 설교 lyric video)**

**산출물**:
1. `app/render/compositions/sermon_longform_v1.html` (16:9, 30-45분)
2. 구성 (페르소나 #3 §3):
   - 25%: 성구 텍스트 + 천천한 Ken Burns 배경
   - 40%: 추후 P8 이전엔 정적 backdrop 흐름
   - 20%: kinetic typography (추상 신학 개념 — Gemma 4가 "covenant", "grace" 같은 키워드 추출)
   - 15%: 정지 이미지 parallax (Tissot PD)
3. austerity 1순간 자동 삽입 — 영상 중반 무작위 위치, 검은 화면 + 흰 명조 + 6초 silence

**Gate**:
- [ ] 45분 sermon 1개 풀 렌더 → mp4 (≤ 20분 렌더 시간)
- [ ] cuts/min ≤ 8 (페르소나 #3 §5)
- [ ] LUFS -16, austerity 1회 명확
- [ ] 시각 검증: 30분 시청 — 지루하지 않고 신학 무게 유지

**위험**:
- 89분 sermon 통째로 렌더 시 메모리 압박 (Chromium 4GB+ 사용, 중간 OOM 가능)
- Whisper transcript 시간 정확도 한계 — 긴 영상에서 단어 강조 sync 누적 오차

**예상 공수**: **3-4일**

---

### **P8 — B-roll 자동 매칭**

**산출물**:
1. Pexels API 연동 + 자체 stock 라이브러리 (1차: 100개 영상 큐레이트)
2. Tissot Brooklyn Museum 350+ 마스터 페인팅 다운로드 + bge-m3 임베딩
3. `app/render/broll.py` — transcript chunk → CLIP 또는 bge-m3 매칭 → 영상/이미지 후보
4. composition `<video>` / `<img>` 트랙 추가

**Gate**:
- [ ] 1시간 sermon 자동으로 30개 b-roll 클립 매칭
- [ ] 매칭 정확도 사람 검토 ≥ 70% (subjective)
- [ ] AI 예수 얼굴 절대 금지 (페르소나 #3 §6) — 필터 작동

**위험**:
- Pexels API quota
- 매칭 quality — 페르소나 #3 가이드 ("shepherd 발화 시 양 사진 = 아마추어. 신학 무게 작업 = 마스터 페인팅") — 휴리스틱 + LLM 검증 필요
- 영상 크기 (5-30MB/clip × 30 = 1GB/sermon)

**예상 공수**: **3-5일**

---

## 3. 추천 진행 순서

| 순서 | Phase | 공수 | 누적 | 핵심 가치 |
|---|---|---|---|---|
| 1 | **P3** (성구 카드) | 3일 | 3일 | 신학 무게 ↑ — 가장 큰 시각 변화 |
| 2 | **P6** (editor 토글) | 1일 | 4일 | 사용자 매일 사용 가능 진입점 |
| 3 | **P4** (reel) | 2일 | 6일 | 멀티 클립 워크플로 완성 |
| 4 | **P5** (음악 베드) | 1.5일 | 7.5일 | 청각 품질 ↑ |
| ─ | (1주 운영 + 피드백) | — | — | 실 사용 데이터 수집 |
| 5 | **P7** (longform) | 3-4일 | 11일 | 풀 설교 자동화 |
| 6 | **P8** (B-roll) | 3-5일 | 16일 | 시각 깊이 |

**critical path = P3 → P6**: 이 두 개가 첫 7일 안 진입.

---

## 4. 의사결정 4건 (각 Phase 진입 전 결정 필요)

| Phase | 결정 사항 | 권장 |
|---|---|---|
| P3a | 개역개정 본문 — 자체 JSON / bibleapi.io / SWORD module | **자체 JSON** (privacy + offline) |
| P3a | 라이선스 표시 — "내부 비공개" / Creative Commons / 출처 명시 | **내부 비공개** + 영상 끝 출처 |
| P5 | 음악 라이선스 — Epidemic Sound (€15/월) / Pixabay (무료) / 자체 작곡 | **Epidemic Sound personal** ($15/월 = 약 £12/월) |
| P8 | B-roll 소스 — Pexels API / Storyblocks 구독 / 자체 촬영 | **Pexels + Tissot PD** (1차) |

---

## 5. KPI / 측정

각 Phase 종료 시 측정:

- **렌더 시간**: 60초 short = 30초 이내 / 5분 reel = 8분 이내 / 45분 longform = 20분 이내
- **시각 품질**: 페르소나 #3 가이드 "절대 안 함 16개" 위반 0건
- **사용자 워크플로 시간**: 새 sermon 업로드 → 5개 short publish 완료까지 30분 이내 (P6 완료 후)
- **신학적 정확도**: 성구 인용 본문 정확 100%, 잘못된 verse 표시 0건

---

## 6. 위험 통합 모니터링

| 리스크 | 관찰 시점 | 대응 |
|---|---|---|
| HP 단일 머신 OOM (Chromium + Whisper + Gemma 동시) | P7 진입 시 | Whisper unload during render, Gemma queue |
| 개역개정 저작권 노출 | P3a 진행 시 | 영상 출처 표시 + 비공개 채널만 사용 |
| HyperFrames v0.4 미숙으로 자막 sync 깨짐 | 모든 Phase | Remotion fallback 코드 P0에 미리 깔아둠 (HYPERFRAMES_DESIGN.md §8) |
| 사용자가 자비스 모드 위임 후 결과 검증 안 함 | 모든 Phase | 매 commit 후 시각 frame 검증 obligatory (P0/P1처럼) |

---

## 7. 즉시 다음 액션 (P3 진입)

1. 개역개정 본문 데이터 소스 결정 (위 §4 의사결정 1번)
2. `app/render/bible/krv.json` 빌드 — 66권 약 31100 verse, 압축 후 ~2MB
3. `app/render/scripture.py` 에 `lookup_verse()` 추가
4. `app/render/payload.py` 에서 detect_scripture_refs() 결과에 본문 + appears_at_sec 채움
5. 시각 검증: 클립 0-30초에 "요한복음 3:16" 인용 있는 sermon으로 mp4 생성 → 카드 보임 확인

---

## 8. 변경 이력

| 버전 | 일자 | 변경 |
|---|---|---|
| v1.0 | 2026-05-03 | HYPERFRAMES_DESIGN.md (Phase 정의) |
| **v2.0** | **2026-05-03** | **P0+P1 완료 후 남은 Phase 순차 설계** |
