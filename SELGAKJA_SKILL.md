---
name: 선각자
description: 새 프로젝트/도구/프레임워크 도입 시 Github 완성품 우선 검색 + 5단계 정독 프로세스. From-scratch 창작 금지. 처음 만나는 도구에 무조건 발동.
triggers: ["새 프로젝트", "새 도구", "처음 도입", "first time", "framework", "new tool", "처음 만나는", "new library", "도구 시작", "신규 stack", "stack 결정", "엔진 결정", "기술 결정", "처음 쓰는", "선각자"]
---

# 선각자 (Pioneers' Wisdom)

> "대부분 깃허브에 완성품이 올라온다. From-scratch 창작은 7일 낭비의 정확한 원인."
> 
> — 사용자, 2026-05-04 (HF v0.4 7일 낭비 후)

새 도구/프레임워크/프로젝트를 처음 만날 때 **무조건 발동**. 코드 한 줄 작성 전에 통과 의무.

---

## 0. Github First — 코드 작성 전 최우선 (5분)

**완성품 검색이 모든 새 프로젝트의 1단계.** From-scratch는 last resort.

```bash
# 도구 + use case 키워드 조합으로 검색
gh search repos "<tool> <use-case>" --sort=stars --limit 20
gh search repos "<tool> <use-case-narrow>" --sort=updated --limit 10
gh search repos "<adjacent-tool> <use-case>" --sort=stars

# 예 — "HyperFrames로 sermon faceless 영상 자동화":
gh search repos "hyperframes sermon" --sort=stars
gh search repos "hyperframes captions korean"
gh search repos "hyperframes 1080 1920" --sort=stars
gh search repos "remotion sermon korean"
gh search repos "video-as-code captions production"
gh search repos "faceless youtube automation captions"
```

**판단 룰**: 가장 가까운 fit 5개 후보 추출. 각:
- ⭐ stars (경험적 신뢰)
- 📅 last commit (활성 maintained?)
- 📜 license (Apache 2.0 / MIT / BSD 안전)
- 📖 README (설치 + run 5분 안 가능?)
- 🎬 examples/ 디렉토리 존재
- 🧪 tests/ 또는 CI 통과 표시

**최적 fit 1개 → clone → render → working baseline 확보**. 이게 우리 base. **From-scratch 0%**.

**90% 케이스** — 이 단계로 끝남. 기존 작품 → 우리 데이터 inject → ship.

**10% 케이스** — fit 0이면 그제서야 from-scratch. 단 rare.

---

## 1. 새 도구 정독 5단계 (Github First 후 또는 동시)

도구 공식 docs에서 **이 4 페이지 무조건** (블로그/튜토리얼 X):

### 정독 순서 (이 순서가 ROI 순)

1. **Common Mistakes / Troubleshooting / FAQ** ⭐ 가장 ROI 높음
   - 남이 이미 빠진 함정이 압축됨
   - 우리 HF case 정확히 이 페이지에 답이 있었음 (timeline duration / class="clip")
   
2. **Examples / Starter Templates**
   - `npx <tool> init --example <name>` 같이 Working starter 받아서 즉시 render
   - 우리 use case와 가장 가까운 starter 찾음
   
3. **Quickstart**
   - hello world 5분 안 작동 확인
   
4. **Concepts / Architecture / Schema reference**
   - abstract rules — 위 3개 통과 후 정독

### 정독 시간
- Common Mistakes: 10분
- Examples: 10분  
- Quickstart: 10분
- Concepts: 30분
- **합 1시간** — 7일 낭비 vs 1시간 정독

---

## 2. Working starter → 작은 수정 룰

**from-scratch 절대 금지.**

```
✅ 정답: starter clone → render OK → 1 element 수정 → render → frame 확인 → 다음 1 element
❌ 함정: brief 작성 → from-scratch 5 scene 빌드 → render → 깨짐 → debug
```

**1회 실패 룰**: 같은 도구로 1번 실패 → STOP. 코드 더 파지 말고 docs 1차 정보 + Github examples 재검토.

---

## 3. 절대 금지 anti-pattern

| Anti-pattern | 신호 | 막는 룰 |
|---|---|---|
| **From-scratch 창작** | "내가 brief 잘 만들면 작동 보장" | Github 검색 5분 무조건 |
| **2차 정보 의존** | WebSearch 8개 블로그 요약 | 1차 정보 (repo + docs + code) 50% 이상 시간 |
| **거인모드 anchoring** | "이미 리서치 했다" 안주 | 1번 실패 = re-research trigger |
| **Forward momentum** | 4/5 작동 → 5번째 fix 시도 | 부분 실패 = foundation 의심 |
| **Tutorial-level만** | 추상 docs 만 정독 + production code 안 봄 | launch-video / student-kit 같은 worked example 정독 obligatory |
| **Reverse-engineer** | starter 무시하고 "더 잘 만든다" | working starter base + small mod 만 |

---

## 4. 우리 case 적용 (HF 7일 낭비 분석)

```
적용 안 했음 (실패):
  Day 1 — HF brief 작성 (from-scratch)
  Day 2 — composition v1 작성 (from-scratch)
  Day 3 — 단조로움 발견 → composition v2 작성 (from-scratch)
  Day 4-6 — Body 6번 fix 시도 (from-scratch debug)
  Day 7 — composition v3 작성 (from-scratch, SKILL.md 기반)
  Day 8 — Common Mistakes 페이지 발견 (timeline duration + class="clip")
  → 7일 + 자비스 ~10시간 낭비

적용했으면 (가설):
  5분: gh search repos "hyperframes sermon" "hyperframes 1080 1920"
        gh search repos "remotion korean captions"
  10분: heygen-com/hyperframes-launch-video clone + render → 17 sub-comp working
        nateherkai/hyperframes-student-kit clone → 12 finished projects
  10분: docs.hyperframes.heygen.com Common Mistakes + Examples 정독
  30분: launch-video index.html + 1 sub-comp 정독 + 우리 5 scene 패턴 매핑
  1시간: 우리 sermon-app 데이터 (transcript, audio_url, scripture) inject layer만 작성
  → 2시간 안 끝났을 것
```

---

## 5. Hard Rules (위반 시 자비스 STOP)

1. **새 도구 첫 만남 시 Github 검색 5분 미실행** → 코드 작성 금지
2. **Common Mistakes / FAQ 정독 안 함** → 코드 작성 금지
3. **Working starter render 검증 안 됨** → 수정 금지
4. **From-scratch 정당화 못 함** (Github fit 0 증명 X) → 작성 금지
5. **1회 실패 후 docs 재정독 안 함** → 2번째 시도 금지

---

## 6. 활성화 (auto-trigger)

다음 키워드 사용자 메시지에 등장 시 본 스킬 발동:

- "새 프로젝트", "처음 도입", "처음 만나는", "신규 stack", "엔진 결정"
- "first time", "new tool", "new library", "new framework"
- "선각자" (명시적 호출)
- 또는 새 npm package / pip module / SDK 이름이 conversation 처음 나옴

발동 시 자동 실행:
1. 첫 응답에 "선각자 모드 발동" 알림
2. § 0 Github First 검색 명령 5개 sample 제시
3. § 1 정독 4 페이지 list 제시 (도구 공식 docs URL 추정)
4. 사용자에게 "코드 작성 전 위 통과 후 진입"

---

## 7. 비활성화 조건

다음 시 본 스킬 skip:
- 사용자가 "그냥 from-scratch 가자" 명시
- 도구가 우리 자체 (sermon-app 같은 local code) — 외부 도구 아님
- 1줄짜리 fix (단순 typo 수정 등)
- Github 검색 결과 0건 + 도구 폐쇄 (rare)

---

## 8. 변경 이력

| 버전 | 일자 | 변경 |
|---|---|---|
| v1.0 | 2026-05-04 | 최초 — HF v0.4 7일 낭비 후 codify. Github First + 5단계 정독 |

---

## 9. 다음 새 도구 만날 때 (cheat sheet)

```bash
# Step 0 — Github First (5분)
gh search repos "<tool> <use-case>" --sort=stars --limit 20
gh repo clone <best-fit>
cd <repo> && npm install && npm run dev   # 또는 도구별 quickstart

# Step 1 — Common Mistakes / FAQ 정독 (10분)
curl -s https://docs.<tool>.com/troubleshooting > /tmp/<tool>_mistakes.md
curl -s https://docs.<tool>.com/common-mistakes >> /tmp/<tool>_mistakes.md
cat /tmp/<tool>_mistakes.md

# Step 2 — Examples + Starter Templates (10분)
curl -s https://docs.<tool>.com/examples > /tmp/<tool>_examples.md
npx <tool> init my-test --example <closest-fit>
cd my-test && npx <tool> render

# Step 3 — Quickstart (10분, 위 starter 와 비교)

# Step 4 — Concepts / Schema (30분, 깊은 이해 필요할 때만)

# Step 5 — 우리 use case 데이터 inject layer만 작성 (rest)
```

**한 줄로**: **"매 새 프로젝트 = Github 검색 5분 → clone 1개 → 우리 데이터 inject. From-scratch는 last resort."**
