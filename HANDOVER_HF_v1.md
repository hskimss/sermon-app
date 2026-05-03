# HyperFrames 통합 — sermon-app 측 P1·P2·P3prelim 인계 보고

**완료일:** 2026-05-03
**기반:** `HYPERFRAMES_DESIGN.md` v1.0
**실행자:** Mac Claude (Jarvis Mode — Proposer→Critic→Synthesizer)

---

## Phase 진행률

| Phase | 영역 | 상태 |
|-------|------|------|
| **P0** | HP-Z2-LLM HyperFrames 설치 + smoke + hf-server :8766 | 🟡 작업지시서 발행 → Anti 실행 대기 |
| **P1** | sermon_short_v1 컴포지션 (HTML+CSS+GSAP) | ✅ 완료 |
| **P2** | sermon-app payload 빌더 + /api/job/<id>/render endpoint | ✅ 완료 |
| **P3 prelim** | 성구 인용 검출 (regex 1차, 66권) | ✅ 완료 |
| P3 본 | Gemma 4 약식 인용 보강 + 개역개정 라이브러리 | ⏸ 대기 |
| P4–P8 | reel_v1 / longform / 음악베드 / B-roll | ⏸ 대기 |

---

## 변경 파일

| 파일 | 상태 | 역할 |
|------|------|------|
| `app/render/__init__.py` | 신규 | 패키지 export |
| `app/render/scripture.py` | 신규 | 66권 매핑 + 2종 regex (콜론/한글) |
| `app/render/payload.py` | 신규 | transcript+emphasis → HP 요청 body |
| `app/render/client.py` | 신규 | HF_RENDER_URL 클라이언트 (submit/status/health) |
| `app/render/compositions/sermon_short_v1.html` | 신규 | 1080×1920, 9:16, GSAP, house style |
| `app/server.py` | 수정 | 3개 엔드포인트 추가 (/render, /render/<id>/status, /render/health) |
| `test_render_payload.py` | 신규 | 스모크 테스트 (regex/payload/lint) |
| `P0_WORK_ORDER_HP.md` | 신규 | Anti(HP) 복붙용 P0 작업지시서 |

---

## 검증 결과

```
[OK] 6개 신규 .py syntax 통과
[OK] sermon_short_v1.html — placeholder 9개 모두 존재
[OK] HyperFrames lint 통과 (data-composition-id, __timelines, __hyperframes_ready)
[OK] detect_scripture_refs 3종 매칭 (요한복음 3:16 / 마태복음 5장 3절 / 롬 8:28)
[OK] 66권 supported_books 일치
[OK] payload 11키 모두 존재 — composition/format/quality/house_style/audio_url
     /audio_clip/clip_range/words/transcript_segments/scripture_refs/meta
[OK] 60초 클립 → 115 words, 24 segments, clip-local 시각 [0, 60s] 정합
```

테스트 대상 job: `20260428_070532_u7DodpeoTzg`

---

## 자비스 모드 적용 (Critic 발견 → Synthesizer 반영)

| 발견 | 반영 |
|------|------|
| `mac-tailscale` 호스트가 등록 안 돼 있을 수 있음 | `SERMON_APP_BASE_URL` env로 override |
| `verse_end` 미지정시 fallback 필요 | `verse_start = verse_end` 자동 |
| 약칭 ("롬 8:28") 처리 누락 | 66권 약칭 사전 + 긴 이름 우선 매칭 |
| `composition_id` 가 JS template literal에 들어감 | hf-server 측 placeholder 치환 (P0 작업지시서) |
| `dry_run=true` 옵션이 없으면 HP 미가동 시 디버그 어려움 | `/render`에 `dry_run` 분기 추가 |
| HP unreachable 시 사용자 혼란 | `502 + hp_unreachable: true` 명시 |
| `audio_url` 인증/mux 누락 위험 | hf-server `_render_sync`에서 다운로드 → ffmpeg mux |

---

## 다음 액션 (사용자 → Anti)

```
1. 사용자 → Anti 켜기 (HP에 SSH)
2. P0_WORK_ORDER_HP.md §1~6 순차 복붙
3. §7 검증 체크리스트 8개 모두 ✓
4. composition sync — Mac에서:
   scp 'app/render/compositions/sermon_short_v1.html' \
       quant@100.104.121.7:~/hyperframes-render/compositions/
5. Mac sermon-app 재시작 후
   curl http://127.0.0.1:5001/api/render/health  → {"ok": true}
   curl -X POST .../api/job/<JOB_ID>/render -d '{"clip":{...},"dry_run":true}'
   → payload_preview 확인
   → dry_run 빼고 실 렌더 요청 → render_id 받음
   → polling 또는 callback으로 mp4_url 수령
```

---

## 환경 변수 (sermon-app)

| Key | Default | 용도 |
|-----|---------|------|
| `HF_RENDER_URL` | `http://100.104.121.7:8766` | HP hf-server base |
| `SERMON_APP_BASE_URL` | `http://mac-tailscale:5001` | HP가 audio fetch할 base |
| `HP_Z2_LLM` | `http://100.104.121.7:11434` | 기존 Ollama (변경 없음) |
| `SERMON_LLM_MODEL` | `gemma4:26b` | 기존 (변경 없음) |

---

## 위험 / 미해결

1. **HP IP 가정**: 설계서 `100.104.121.7`. 실 IP 다르면 client.py default 또는 env로 조정.
2. **HyperFrames CLI 인자 변동**: v0.x — Anti가 P0 §4에서 `npx hyperframes --help`로 확인 후 `_render_sync` cmd 보정.
3. **hf-server는 동기 단일 작업** (P0 골격). 동시 다중 렌더는 P2 본 단계에서 큐 + worker.
4. **개역개정 본문 라이브러리** 미연결 — `scripture_refs[].text`는 P3 본 단계에서 채움 (현재 비어있음).
5. **mac-tailscale hostname**: HP에서 audio fetch 가능하려면 등록 필요. 미등록이면 `SERMON_APP_BASE_URL=http://<Mac Tailscale IP>:5001` 명시.
