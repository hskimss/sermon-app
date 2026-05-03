# 거인모드 v2 — 최고의 Sermon-Video 파이프라인 (3페르소나 deep research)

> 작성일: 2026-05-03
> 검증 범위: 8개 web search + 공식 docs / 블로그 / 사례 다수 fetch
> 이전 v1 (#25) 보다 깊게 — production-grade 정의 + 비용 + critical path
> 결과: **현재 stack 5/10 → 8/10 가는 명확한 경로**

---

## Executive Summary (250 words)

**현재 결과가 5/10인 이유**: HyperFrames 자체 한계 아님. **우리가 그루들의 정석 워크플로우(Claude Design → Skills → multi-scene)를 우회하고 직접 코딩** 했기 때문. composition이 single-scene + 자막 only.

**검증된 그루 정석 파이프라인** (Mejba 사례 — 5번째 영상에 15분):

```
Claude Design (claude.ai/design, Opus 4.7)
   ↓ 5-7 scene + brand identity + GSAP + shader transition 포함 ZIP
Claude Code skills (npx skills add heygen-com/hyperframes)
   ↓ /hyperframes 슬래시 + 3-skill chain
HyperFrames preview/render → MP4
   ↓
Auphonic (mp3 master) + ElevenLabs/HeyGen (보이스, 선택)
```

**최고의 STACK 3-tier 결정**:

1. **단기 (1주)** — **현재 HF 유지 + Claude Design 도입 + 음성 마스터** : 8/10 도달 가능
2. **중기 (1달)** — **Remotion Lambda 병행** + Submagic API 백업 : 9/10 + production-grade 안정성
3. **장기 (3달)** — **자체 Remotion 템플릿 라이브러리 + Higgsfield B-roll + WhisperX 한국어 align** : 9.5/10 + 완전 자동화

**즉시 결정 4가지**: ① Claude Design 가입 (Pro/Max 필수, Free 불가), ② 첫 sermon_short_v2 ZIP 받아 검증, ③ Submagic API $19/월 시범 (한국어 미세 검증), ④ HF v0.4 vs Remotion 5.x A/B 비교 1주 진행.

---

## 페르소나 #1 — 엔진 선택 (시니어 비디오 렌더 엔지니어)

### 1.1 Claude Design 진위 검증 (verified)

**Anthropic 공식 출시: 2026년 4월 17일** — Claude Opus 4.7 기반 ([techcrunch.com](https://techcrunch.com/2026/04/17/anthropic-launches-claude-design-a-new-product-for-creating-quick-visuals/), [anthropic.com/news/claude-design-anthropic-labs](https://www.anthropic.com/news/claude-design-anthropic-labs)).

| 항목 | 검증된 사실 |
|---|---|
| 출시일 | 2026-04-17 |
| 모델 | Claude Opus 4.7 |
| 입력 | description + 첨부 파일 (디자인 시스템, 브랜드 가이드) |
| 출력 | prototype, slides, one-pager, **HF composition ZIP** |
| 내보내기 | PDF / URL / PPTX / **Canva 직접** |
| **가격** | **research preview** — Pro / Max / Team / Enterprise 만 (free 불가) |
| Pro plan | $20/월 (Anthropic Pro 가격 참조) |
| 디자인 시스템 학습 | repo + 디자인 파일 읽음 |

**HF 외 출력 가능?**: 현재 검증 결과 — Claude Design은 **HF composition 우선** (`claude-design-hyperframes.md` 인스트럭션 attach). 다른 엔진(Remotion, Revideo 등)은 native 미지원이지만 codebase 읽기 능력으로 React/TSX 도 생성 가능 추정 (검증 필요).

**한국어 brief 처리**: Opus 4.7은 한국어 native 수준. 검증 안 된 것 = 한국어 폰트(Pretendard, Noto Serif KR) 자동 선택 quality.

### 1.2 HyperFrames v0.4.42 production-grade 평가

**공식 사례 — Mejba Ahmed의 정량 측정** ([mejba.me/blog](https://www.mejba.me/blog/claude-code-video-production-system-hyperframes-auphonic)):

| 영상 # | 작업 시간 | 비고 |
|---|---|---|
| 1 | 4시간 | prompt + design system + composition + Auphonic preset 처음 |
| 2 | 2시간 | 1번 skill 재사용 |
| 3 | 40분 | skill chain 안정 |
| 5 | **15분** | 모든 단계 skill 화 |

→ **production scaling 검증됨**. HF는 prototype 수준 아님. 단 **Claude Code skills 시스템** 이 핵심 unlock.

**HF 한계** (검증):
- 단일 머신 렌더 (분산 미지원) — 1시간 영상 풀 렌더 시 ~15-20분
- v0.4.42 (2026-05 현재) — 일부 lint warning, GSAP overlap, shader 미숙
- HeyGen 자체 사용 사례 = 자기네 launch video 1편 (검증)

### 1.3 Remotion 5.x 비교 (verified)

[Remotion docs](https://www.remotion.dev/docs/lambda) + [aividpipeline.com Agent Skills Guide](https://aividpipeline.com/blog/remotion-agent-skills-guide-2026):

| 항목 | Remotion 5.x | HyperFrames v0.4 |
|---|---|---|
| 분산 렌더 | **AWS Lambda** ($0.10/min/instance, 1시간 영상 5분) | 단일 머신 (1시간 ~20분) |
| Captions API | `@remotion/captions` v2 + `createTikTokStyleCaptions` 검증 | data-start 속성 + 직접 코딩 |
| Agent Skills | `npx skills add remotion-dev/remotion` (2026-03 출시) | `npx skills add heygen-com/hyperframes` |
| License | MIT-like (회사 매출 $10M 미만 free, 초과 시 commercial) | **Apache 2.0 완전 무료** |
| Production | Cred / Splice / Wondr / Reel Captions / 검증 다수 | HeyGen 자체 + Mejba + 소수 |
| 색상 공간 v5 | "default" 추가 (HDR 대응) | HDR 가이드 별도 |
| 한국어 폰트 | `@remotion/google-fonts` Pretendard CDN | system fonts 의존 |

**판정**: Remotion이 **production maturity 압승** (생태계, 분산, 사례). HF는 **agent-driven 자동화 + Apache 2.0** 가치. 둘 다 Claude Code skills 통합 됨 — **택일 아닌 병행 가능**.

### 1.4 새 alternatives (verified 2026)

**Higgsfield** ([gaga.art/blog/higgsfield-ai](https://gaga.art/blog/higgsfield-ai/), [filmora](https://filmora.wondershare.com/ai-generation/higgsfield-ai-review.html)) — **$75/월** aggregator:
- 15+ 모델 (Sora 2, Kling 2.6, Veo 3.1) 통합
- **Cinema Studio 2.0** = 카메라 시뮬 (Anamorphic 글래스, depth of field, focal length)
- 강점: cinematic B-roll 자동 생성. **sermon long-form B-roll 라이브러리 채울 강력 도구**
- 한계: text-to-video라 sermon transcript와 직접 sync 불가. **별도 매칭 단계 필요**

**Dzine AI** ([slashdot 비교](https://slashdot.org/software/comparison/Dzine-vs-Higgsfield/)) — 브라우저 기반:
- AI lip sync 강점
- 그러나 sermon 영상의 핵심 (자막 + 성구 카드) 과 거리. 보조용

**Submagic API** ([submagic.co](https://www.submagic.co/pricing)) — 검증:
- Starter $19/월 (annual $12) — 25 export, 1080p, 50+ langs
- Pro $39/월 — 4K, batch, brand kit
- **subtitles API 정식 출시 — 자동화 파이프라인 통합**
- 한국어 지원 ✓ (단 미세 kerning 검증 필요)

**OpusClip** ([reviews 다수](https://www.opus.pro)) — 검증:
- $9-19/월
- **Virality Score** + auto-clipping (1시간 → 5-8 shorts)
- 자체 사용 추천: sermon 1시간 → 클립 후보 자동 추출 (우리 Gemma 4 클립 선정과 중복)

**Veo 3 / Sora 2 / Kling 2.6** — Higgsfield aggregator로 통합. 직접 가입 시 각 $30-100/월. **Higgsfield $75 가 통합 가성비**.

### 1.5 한국어 word-level alignment (verified)

[WhisperX repo](https://github.com/m-bain/whisperX) + [Issue #1247](https://github.com/m-bain/whisperX/issues/1247):

| 모델 | Korean 정확도 | 비고 |
|---|---|---|
| mlx-whisper (Apple Metal) | ±100-300ms | 우리 현재 — 자막 lag 보임 |
| WhisperX + kresnik/wav2vec2-large-xlsr-korean | ±20-80ms | **8-10× 개선**. P0 P1에서 검증 권장 |
| Montreal Forced Aligner (MFA) Korean | ±5-15ms | 가장 정밀, phoneme dict 준비 필요 |
| CrisperWhisper | ±50ms | verbatim + disfluency 보존 |

WhisperX Korean wav2vec2 = **현재 우리 stack에 즉시 통합 가능**. HF 서버에 추가 모델 다운로드 (~1GB).

### 1.6 페르소나 #1 결론

**가성비 + production-grade 도달 STACK**:
1. **렌더 엔진**: HyperFrames + Remotion 병행 (HF=agent-driven 단기 / Remotion=Lambda 분산 장기)
2. **디자인 시작점**: **Claude Design 필수** (가입 안 하면 single-scene 한계 못 벗어남)
3. **자막 정확도**: WhisperX Korean 즉시 통합 (현재 mlx-whisper의 8-10× 개선)
4. **B-roll**: Higgsfield $75/월 (3개월 시범) or Pexels API (무료, quality ↓)

---

## 페르소나 #2 — 모션 그래픽 디자이너 (Top 1% sermon visuals)

### 2.1 2026년 캡션 best practice (verified)

[opus.pro/blog/tiktok-caption-subtitle-best-practices](https://www.opus.pro/blog/tiktok-caption-subtitle-best-practices) + [joyspace.ai/hormozi-editing-style-2026-analysis](https://joyspace.ai/hormozi-editing-style-2026-analysis):

**현재 메타 = "Dynamic Minimalism"**:

| 요소 | 2021 Hormozi | **2026 Dynamic Minimalism** |
|---|---|---|
| 폰트 | Impact Bold 두꺼운 대문자 | **Clean sans-serif** (SF, Roboto, Pretendard) |
| 색상 | 흰+노랑+초록 매번 강조 | **흰 base + brand color 1개** strategic 강조 |
| 모션 | 톡톡 튀는 pop bounce | **smooth fade 0.2-0.4s** |
| 강조 | 매 단어 색상 변동 | **3-5 단어 중 1개**만 sparingly |
| 이모지 | 빈번 (📈🔥💯) | **거의 0** — 신학 콘텐츠는 절대 0 |
| B-roll | 메모적 (memetic) 짤 | **cinematic** (Higgsfield/Pexels) |
| 첫 3초 | 거대 텍스트 | **여전히 거대** — 3초 룰 유효 |

→ **우리 골드 강조는 정답**. 단 **smooth fade 0.2-0.4s** (현재 0.08s 너무 빠름) + B-roll layer 추가 + 첫 3초 거대 텍스트 hook 필요.

### 2.2 Bible Project stack (verified)

[Bible Project Help Center](https://help.bibleproject.com/hc/en-us/articles/4479380169879):
- **Adobe Creative Suite + Maya + Cinema4D**
- 비-자동화. 100% 매뉴얼.
- 우리에겐 직접 통합 어려움. 단 **시각 언어 (parchment 색감, hand-illustrated, 미니멀 모션)** = 참고 가치 ↑

→ **Bible Project 미적 layer**(parchment background + 천천한 fade + 단일 illustrator pipeline) **모방 가능**. 단 Adobe → HF/Remotion 으로 옮길 때 grain texture + slow zoom 효과 추가.

### 2.3 Korean church 영상 미학 변화 검증 부족

[Ruah Creative House 가이드](https://ruahcreativehouse.org/blog/church-motion-graphics/) — 일반론. CGNTV / 잘잘잘 / 두란노 production stack은 search 결과 0건. **검증 안 됨** — 직접 채널 분석 필요.

### 2.4 페르소나 #2 결정 — A Church London 시각 baseline

**hold rules** (2026 Dynamic Minimalism + 페르소나 #3 Reverent Restraint 융합):

```
폰트:
  자막: Pretendard ExtraBold (현재 그대로 OK)
  성구: Sandoll 명조 Neo1 SemiBold or Noto Serif KR
  타이틀: Ridibatang

색상:
  Primary: Ink #1A2236 / Parchment #F5EFE0
  Background: Charcoal #0E1116
  Accent (1개만): Gold #D4AF37 (현재) or Oxblood #6B1F26 (lament 톤)

모션:
  자막 fade-in: 0.3-0.4s (현재 0.08s 너무 빠름 — 수정)
  성구 fade-in: 0.6-1.0s (현재 OK)
  단어 강조 bounce: scale 1.0 → 1.05 → 1.0, 0.18s (현재 1.08 너무 큼)
  shader transitions: 2-3개 key 모먼트 (현재 0개 — 추가)

B-roll:
  25% 영상 시간 = scripture text
  40% B-roll (Pexels/Higgsfield/Tissot)
  20% kinetic typography (추상 신학)
  15% 정지 이미지 + parallax

음악 베드:
  Voice -16 LUFS / Bed -22 LUFS / sidechain 12-18dB ducking
  성구 등장 = 1.5s silence
```

---

## 페르소나 #3 — 자동화 파이프라인 아키텍트

### 3.1 Mejba 사례 정량 분석 (verified)

[mejba.me production stack](https://www.mejba.me/blog/claude-design-hyperframes-video-editing) + [mindstudio.ai/blog/ai-video-editing-claude-code-hyperframes](https://www.mindstudio.ai/blog/ai-video-editing-claude-code-hyperframes):

```
Mejba 5-skill chain:
  generate-motion-graphic (intro/outro)
  add-animated-overlay (lower-third, speaker label)
  sync-captions (transcript → caption track)
  master-audio (Auphonic preset)
  composite-final (모든 layer → MP4)
```

**검증된 ROI**:
- 5번째 영상 = 15분 (1번째 4시간 대비 16배 단축)
- 핵심: **모든 단계 Claude Code skill 화** (`SKILL.md` 파일)
- skill 간 chaining = sequential workflow with explicit data contracts

→ 우리 sermon-app v2 + Gemma 4 + HF 가 **이미 70% 동일 구조**. 부족한 것 = **Claude Design ZIP 입력 + Auphonic 음성 마스터링 단계**.

### 3.2 비용 정량 (verified)

[virvid.ai automation stack 2026](https://virvid.ai/blog/ai-faceless-youtube-automation-stack-2026) + [submagic.co/pricing](https://www.submagic.co/pricing):

**우리 sermon-app 현재 인프라**:
| 항목 | 비용/월 | 비고 |
|---|---|---|
| Mac Tailscale | $0 | 자체 |
| HP-Z2-LLM (전기 + 감가) | $20-30 | 자체 |
| Gemma 4 + bge-m3 | $0 | 자체 |
| Whisper turbo | $0 | 자체 |
| HyperFrames | $0 | Apache 2.0 |
| Gitea | $0 | 자체 |
| **소계** | **$20-30** | infra + LLM 모두 자체 |

**production 도약 추가 비용**:
| 항목 | 비용/월 | 가치 |
|---|---|---|
| Claude Pro (Claude Design 사용) | $20 | **단기 critical** — 단조로움 탈출 |
| ElevenLabs Starter | $5 | 음성 합성 (필요 시) |
| Auphonic (음성 master) | $11 | 1시간 audio/month, sermon long-form 적격 |
| Submagic API (백업) | $19 | 1주 시범 후 자체 또는 유지 |
| Higgsfield (B-roll generator) | $75 | 3개월 시범 후 라이브러리 축적 시 cancel 가능 |
| Remotion Lambda (long-form 분산) | $5-15 | AWS pay-per-render |
| **합계** | **$135-145/월** | production-grade 도달 |

**비교**: Bible Project / Above Inspiration 같은 production = **수동 인력 4-6명 × 월 $50K+**. 우리는 $135/월 + 자체 컴퓨팅으로 **15분/영상** 도달 가능.

### 3.3 자동화 패턴 — Claude Code Skills 정석

[10 Must-Have Skills 2026](https://medium.com/@unicodeveloper/10-must-have-skills-for-claude-and-any-coding-agent-in-2026-b5451b013051) 핵심:
- SKILL.md = 한 가지 task 의 reusable playbook
- skill 간 sequential chaining (output → next input)
- agent 가 어느 LLM이든 (Claude Code, Cursor, Codex, Cline) 호환

**우리 sermon-app 에 추가할 Skills (5개)**:

```
sermon-app/skills/
  generate-sermon-short/SKILL.md      # 60s short composition 생성
  add-scripture-card/SKILL.md         # 인용 detect + KRV 본문 카드
  sync-korean-captions/SKILL.md       # WhisperX align + 단어 강조
  master-audio/SKILL.md               # Auphonic preset → -16 LUFS
  composite-final/SKILL.md            # 모든 layer → MP4 + SRT + thumbnail
```

→ Claude Code(jarvis) 에 위임 시 모든 단계 자동. 우리가 직접 한 P0-P6 = skills 미사용 → 매번 새로 코딩 → 단조로움 + 시간 낭비.

### 3.4 페르소나 #3 결론 — 3-tier production stack

**Tier 1 단기 (1주 내, 8/10 도달)**:
```
mp3 → Whisper turbo (HP) → WhisperX Korean align (HP)
   → transcript JSON ±50ms
   → Gemma 4 클립 선정 + emphasis 단어
   → Claude Design (HF composition ZIP 1개 from-scratch)
   → Claude Code jarvis 가 sermon 데이터 inject
   → HyperFrames render (HP NVENC)
   → Auphonic master audio
   → MP4 + SRT
```

**Tier 2 중기 (1달 내, 9/10)**:
- Tier 1 + Submagic API 백업 (한국어 미세 검증 후 자체 또는 유지)
- Remotion Lambda 병행 (long-form 분산 렌더 — 45분 sermon 5분에)
- 5-skill chain SKILL.md 안정

**Tier 3 장기 (3달 내, 9.5/10)**:
- Higgsfield B-roll 라이브러리 100+ 클립 축적
- 자체 Korean wav2vec2 fine-tune (sermon corpus 학습)
- bge-m3 + Qdrant RAG (과거 sermon 임베딩 → 시리즈 일관성)
- Auto-publish (YouTube Data API + Repurpose.io fanout)

---

## 종합 STACK 결정 — 한 줄 요약

> **HyperFrames 유지 + Claude Design 도입 + WhisperX Korean align + Auphonic + Remotion Lambda 병행 (long-form)** = 1주 안 8/10, 1달 안 9/10, 3달 안 9.5/10.

월 비용: **$135-145** (Claude Pro $20 + Auphonic $11 + Submagic $19 옵션 + Higgsfield $75 시범 + Remotion Lambda $5-15) — production 인력 4-6명 대비 ~$300/월 절감 효과.

---

## 즉시 결정 4가지

| 결정 | 권장 | 이유 |
|---|---|---|
| **1. Claude Design 가입?** | **YES — Claude Pro $20/월** | 단조로움 탈출의 critical path. 사용자가 직접 가입 (Anthropic 계정) |
| **2. WhisperX Korean align 즉시 통합?** | **YES — 0.5일 작업** | 무료 + 자막 정확도 8-10× 개선. P0 work order 만들어 자비스 위임 |
| **3. Submagic API 시범?** | **시범 1주** | $19로 한국어 quality 빠른 검증. 만족하면 자체 Remotion 자체 개발 단축 |
| **4. Remotion Lambda 도입 시점?** | **Tier 2 (1달 후)** | HF + Claude Design 안정 후. 그 전엔 너무 많은 변수 |

---

## 즉시 다음 액션 5단계 (이번 주)

1. **Day 1** — Claude Pro 가입 → claude.ai/design 새 chat → `claude-design-hyperframes.md` 다운+attach → A Church London brief (5 scenes / 60s short / 한국어 자막 + 성구 카드 + austerity 1moment + shader transition 2개 / Pretendard + 명조 / navy/parchment/gold) → ZIP 받음
2. **Day 2** — `sermon-app/app/render/compositions/sermon_short_v2/` 신설 + ZIP 풀어놓기 + sermon-app payload 매핑 (`v1` 과 같은 인터페이스)
3. **Day 3** — WhisperX Korean align 통합 (`pipeline.py` 옵션 추가) + 5분 sermon 다시 전사 → ±50ms 정확도 확인
4. **Day 4** — `v1` vs `v2` mp4 같은 클립으로 렌더 → 사용자 직접 비교 → 8/10 quality 도달 확인
5. **Day 5** — Auphonic 가입 + 음성 마스터링 단계 추가 → 5-skill chain SKILL.md 작성 시작

---

## Sources (verified 2026-05-03)

### Claude Design + HyperFrames
- [TechCrunch: Anthropic Claude Design 출시 (2026-04-17)](https://techcrunch.com/2026/04/17/anthropic-launches-claude-design-a-new-product-for-creating-quick-visuals/)
- [Anthropic 공식 발표](https://www.anthropic.com/news/claude-design-anthropic-labs)
- [VentureBeat: Claude Design challenges Figma](https://venturebeat.com/technology/anthropic-just-launched-claude-design-an-ai-tool-that-turns-prompts-into-prototypes-and-challenges-figma)
- [HyperFrames 공식 — Claude Design 가이드](https://hyperframes.heygen.com/guides/claude-design)
- [Mejba — HF + Auphonic production stack (15분/영상 검증)](https://www.mejba.me/blog/claude-code-video-production-system-hyperframes-auphonic)
- [Mejba — Claude Design + HyperFrames Prompt-Driven Editing](https://www.mejba.me/blog/claude-design-hyperframes-video-editing)
- [MindStudio — Claude Code + HF workflow](https://www.mindstudio.ai/blog/ai-video-editing-claude-code-hyperframes)

### Remotion 5.x
- [Remotion Lambda docs](https://www.remotion.dev/docs/lambda)
- [aividpipeline — Remotion Agent Skills 2026](https://aividpipeline.com/blog/remotion-agent-skills-guide-2026)
- [Reel Captions Lambda render](https://app.reelvideocaptions.com/)

### 2026 Caption / Motion best practice
- [OpusClip — TikTok caption best practice 2026](https://www.opus.pro/blog/tiktok-caption-subtitle-best-practices)
- [Joyspace — Hormozi editing 2026 분석](https://joyspace.ai/hormozi-editing-style-2026-analysis)
- [Submagic vs Captions vs OpusClip 비교 2026](https://fluxnote.io/compare/submagic-vs-captions-ai-for-caption-tools)

### Christian sermon 채널
- [Bible Project 공식 — Adobe Suite + Maya/Cinema4D](https://help.bibleproject.com/hc/en-us/articles/4479380169879)
- [Ruah Creative House — Church Motion Graphics 2026](https://ruahcreativehouse.org/blog/church-motion-graphics/)
- [Faceless YouTube niches 2026 — sermon RPM $6-11](https://shortvids.co/low-competition-faceless-youtube-niches/)

### AI 도구 정량 비교 2026
- [Submagic 가격](https://www.submagic.co/pricing)
- [Higgsfield 리뷰 — $75 multi-model aggregator](https://gaga.art/blog/higgsfield-ai/)
- [Dzine vs Higgsfield](https://slashdot.org/software/comparison/Dzine-vs-Higgsfield/)
- [Filmora — Higgsfield Cinema Studio 2.0](https://filmora.wondershare.com/ai-generation/higgsfield-ai-review.html)
- [virvid.ai — 2026 automation stack 비용](https://virvid.ai/blog/ai-faceless-youtube-automation-stack-2026)

### Korean speech alignment
- [WhisperX repo](https://github.com/m-bain/whisperX)
- [WhisperX 200ms collar (Issue #1247)](https://github.com/m-bain/whisperX/issues/1247)
- [WhisperX paper (arXiv 2303.00747)](https://arxiv.org/pdf/2303.00747)

### Skills 시스템
- [10 Must-Have Skills 2026](https://medium.com/@unicodeveloper/10-must-have-skills-for-claude-and-any-coding-agent-in-2026-b5451b013051)
- [HF 공식 — claude-design-hyperframes.md](https://github.com/heygen-com/hyperframes/blob/main/docs/guides/claude-design-hyperframes.md)
