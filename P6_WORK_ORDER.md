# P6 작업지시서 — editor.html HF 시각화 토글

> 작성: 2026-05-03 (P3 통과 후)
> 위임 대상: 자비스 모드 (Claude Code via sermon-app session)
> 자체 완결형 — 본 문서만 읽으면 컨텍스트 복원 가능
> 예상 공수: **1일** (HF_PHASE_PLAN_v2 §2 P6 기준)

---

## 0. 시작 절차 (필수)

```bash
# 1. 작업 디렉토리
cd "/Users/hwasungkim/Library/CloudStorage/GoogleDrive-sharonkim71@gmail.com/내 드라이브/AI/교회 앱/sermon-app"

# 2. 정독 (이 순서)
cat HF_PHASE_PLAN_v2.md             # 전체 Phase 계획 + P6 §2 정의
cat HANDOVER_HF_v3_P3.md            # P3 결과 + 현재 상태
cat HANDOVER_HF_v2_P0.md            # P0 hf-server :8770 정보

# 3. 현재 동작 확인
curl -s http://localhost:5001/api/render/health     # {"ok":true} 기대
curl -s http://localhost:5001/api/render/health | grep -q '"ok":true' || echo "❌ Flask + HF 점검 필요"

# 4. 기존 endpoint 동작 검증 (이미 dry_run + status + health 있음)
grep -n "render\|llm-bulk-export\|llm-highlight-reel" app/server.py | head -10
```

**중단 조건**: `/api/render/health` 가 `{"ok":true}` 가 아니면 즉시 중단하고 사용자 보고. Mac Flask 또는 HP hf-server 문제 의심.

---

## 1. 목표

기존 editor.html 의 두 버튼 (`📦 5개 모두 export`, `🎞 합쳐서 reel`) 옆에 **`[ ] HF 시각화`** 체크박스를 추가. 체크 시 HyperFrames 시각화 mp4를 받음. 미체크 시 기존 FFmpeg 빠른 export 그대로 작동 (회귀 0).

**핵심 원칙**:
1. **회귀 금지** — 기존 FFmpeg 워크플로 100% 유지. 체크박스 OFF 시 코드 경로 변동 없음.
2. **fallback 안전망** — HP unreachable / 렌더 실패 시 자동으로 FFmpeg 워크플로로 재시도 + 사용자 알림.
3. **사용자 시각 즉시** — 토글 ON → 클릭 → 30초 안에 mp4 또는 진행 상태 보임.

---

## 2. 가드레일 (절대 규칙)

1. **Gitea 전용** — 모든 commit/push는 `quant/sermon-app` 한 곳. GitHub 금지. 신규 repo 생성 금지.
2. **기존 endpoint 변경 금지** — `/api/job/<id>/llm-bulk-export`, `/api/job/<id>/llm-highlight-reel`, `/api/job/<id>/render` 응답 schema 그대로. 기능 추가만.
3. **단일 파일 변경 최소화** — UI 작업이라 `app/static/editor.html` + 옵션으로 `app/server.py` 보강만. 다른 파일 손대지 말 것.
4. **검증 시각 frame 필수** — git commit 전에 토글 ON/OFF 두 케이스 모두 사용자 시점에서 mp4를 받아본 frame 캡처. trust-but-verify.
5. **HF_RENDER_URL env 변경 금지** — 이미 `100.104.121.7:8770` 으로 고정. 손대지 말 것.
6. **회귀 테스트** — 체크박스 OFF 상태로 기존 두 버튼 두 개 모두 mp3 받아오기 정상 작동 확인. 그 다음 ON 상태 검증.

---

## 3. UI 사양

### 3.1 체크박스 위치

`app/static/editor.html` 의 `#ai-clip-panel` 안. 현재 panel-header 아래 두 버튼 (`btn-bulk-export`, `btn-highlight-reel`) 행이 있음. 그 **위에** 체크박스 행 추가:

```html
<div style="margin-bottom:10px; padding:8px; background:#0a0d1f; border-radius:4px;
             font-size:12px; display:flex; align-items:center; gap:8px;">
  <label style="display:flex; align-items:center; gap:6px; cursor:pointer;">
    <input type="checkbox" id="chk-hf-render">
    <span>✨ <strong>HF 시각화</strong> — Pretendard 자막 + 골드 강조 + 성구 카드</span>
  </label>
  <span id="hf-status-pill" style="margin-left:auto; font-size:11px; color:#888;">확인 중...</span>
</div>
```

### 3.2 상태 표시 룰

`#hf-status-pill` 우측에 1초 안에 실측 색깔/문자 채우기:

| HF 서버 상태 | 표시 | 체크박스 |
|---|---|---|
| `/api/render/health` ok=true | `🟢 사용 가능` (`color:#81c784`) | enabled |
| ok=false 또는 timeout | `🔴 HP 다운 — FFmpeg 모드만` (`color:#ef5350`) | **disabled, force OFF** |

페이지 로딩 직후 한 번만 fetch. 캐시 OK.

### 3.3 토글 ON 시 동작 변경

체크박스 ON 상태에서:

- **`📦 5개 모두 export`** 클릭 → 5개 클립 각각을 `/api/job/<id>/render` 로 순차 호출 (병렬 호출 금지 — HP 단일 머신 OOM 위험). 각 render_id 받아서 `/api/render/<id>/status` 30초마다 polling. 완료 시 mp4 다운로드 링크 제공.
- **`🎞 합쳐서 reel`** 클릭 → 현재는 reel composition 미구현 (P4)이므로 **disabled + tooltip "P4 reel composition 대기"**. 회귀 방지를 위해 OFF 상태에선 기존대로 동작.

체크박스 OFF 상태 → 기존 동작 100% 유지. 어떤 코드 경로 변동도 없어야 함.

### 3.4 진행 상태 표시

각 클립 render_id 마다 `#ai-bulk-result` 영역 (이미 있는 div) 에 줄 한 개씩 동적 갱신:

```
✓ clip 1/5 (질문/8) — 32s — 📥 download
⏳ clip 2/5 (간증/9) — 렌더 중 12s
⏳ clip 3/5 (대조/7) — queued
⏳ clip 4/5 (도전/6) — queued
⏳ clip 5/5 (수사/8) — queued
```

failed 시 빨간색 `❌` + 사용자 알림 + (옵션) FFmpeg fallback 자동 시도.

### 3.5 fallback 룰

HF render 호출 시 다음 중 하나면 FFmpeg 워크플로로 자동 fallback:

- HTTP 502 (`/api/job/<id>/render` 가 hp_unreachable 응답)
- 5분 동안 status가 `ready` 안 됨 (timeout)
- HTTP 500 또는 네트워크 에러

fallback 시 `❌ HF 실패 — FFmpeg 모드로 자동 전환` 토스트 + 기존 `/api/job/<id>/llm-bulk-export` 호출.

---

## 4. API contract (이미 존재 — 변경 금지)

### `POST /api/job/<id>/render`
- body: `{"clip":{"start_sec":F,"end_sec":F}, "dry_run":false}`
- response 201: `{"render_id":"...", "status":"queued", "estimated_sec":60}`
- response 502: `{"error":"hp_unreachable"}`

### `GET /api/render/<render_id>/status`
- response: `{"status":"queued|rendering|ready|failed", "elapsed_sec":N, "size_bytes":N, "mp4_path":"..."}`

### `GET /api/render/<render_id>/mp4` (NEW — 작업 항목 1)
- 현재 미구현. 다음 endpoint 추가 필요:
  - HP에서 mp4 fetch (이미 `client.fetch_output()` 있음)
  - Mac에 cache + 사용자에게 send_file
  - 응답: mp4 stream

### `GET /api/render/health`
- response: `{"ok":true|false, "host":"http://100.104.121.7:8770"}`

---

## 5. 산출물 5개

| # | 파일 | 변경 내용 |
|---|---|---|
| 1 | `app/static/editor.html` | 체크박스 행 + status pill + JS 로직 (HF route override) |
| 2 | `app/server.py` | `GET /api/render/<id>/mp4` 추가 (HP에서 fetch + Mac cache + send_file) |
| 3 | `app/render/client.py` | `fetch_output(render_id) → bytes` 메소드 (HP 에서 mp4 가져옴) |
| 4 | `tests/test_render_routes.py` (신규) | mp4 endpoint + render id polling 단위 테스트 |
| 5 | `HANDOVER_HF_v4_P6.md` | 검증 결과 + 시각 frame 경로 + 변경 요약 |

---

## 6. 검증 (Gate — 통과 시 commit)

각 항목 사용자 시점 직접 확인 + frame/log 캡처:

1. **체크박스 OFF 회귀**:
   - [ ] 5개 모두 export → 5개 mp3 + SRT + transcript.json 정상 생성 (기존 동작)
   - [ ] reel → 합쳐진 mp3 1개 정상 생성

2. **체크박스 ON 동작**:
   - [ ] 페이지 로딩 시 1초 안에 `🟢 사용 가능` pill 표시
   - [ ] 5개 모두 export → 5개 mp4 순차 렌더 (각 ~30초), 진행 상태 실시간 표시
   - [ ] 첫 mp4 다운로드 → ffprobe로 1080×1920 + duration 확인
   - [ ] 자막 + 골드 강조 + 성구 카드 (있으면) 시각 검증 (frame 캡처)

3. **HP 다운 시뮬레이션**:
   - [ ] hf-server 임시 stop (`sudo systemctl stop hf-server`) → 페이지 새로고침 → `🔴 HP 다운` pill + 체크박스 disabled 확인
   - [ ] 다시 start (`sudo systemctl start hf-server`) → 새로고침 → 정상

4. **fallback**:
   - [ ] 일부러 빠른 timeout 설정 (test mode) 으로 5분 자동 fallback 테스트
   - [ ] FFmpeg 결과로 자동 전환 + 사용자 알림 토스트

5. **회귀 테스트**:
   - [ ] `cd sermon-app && .venv/bin/python -m pytest tests/ -v` 100% pass
   - [ ] 기존 `test_render_payload.py` 6/6 pass

검증 frame 저장 위치: `/tmp/p6_verify/{ffmpeg_off,hf_on_clip1,hf_on_clip5,hp_down,fallback}_frame.png` 5개.

---

## 7. 위험 + 대응

| 위험 | 대응 |
|---|---|
| HF 5개 순차 렌더에 5분+ 소요 → 사용자 인내심 한계 | 진행 상태 polling 30초 → 5초 빠르게. 1번째 mp4 받자마자 미리보기 자동 재생. |
| Mac → HP mp4 fetch 시 큰 파일 (1-5MB) Tailscale 느림 | streaming send_file (Range 지원). Mac 캐시 디렉토리 `~/.cache/sermon-app/render/` 만들어 재사용. |
| 사용자가 체크박스 ON 한 채 페이지 닫음 → 백엔드 진행 추적 끊김 | render_id를 localStorage 보존. 다음 페이지 방문 시 자동 polling 재개. |
| HP hf-server 메모리 누수 (Chromium 장시간 가동) | 본 작업 범위 외. 별도 systemd watchdog (P0 already done). |
| 체크박스 default state 결정 — ON / OFF? | **default OFF**. 사용자 명시적 opt-in. 회귀 위험 0. |
| editor.html 이 이미 큰 파일 (37KB) → 추가 코드 부피 | 새 코드는 `<script>` 끝에 분리된 IIFE 블록으로 격리. 기존 코드 건드리지 말 것. |

---

## 8. 보고 프로토콜

- **진입 시**: 본 문서 §0 시작 절차 실행 결과 + Gate 5개 항목 한 줄씩 출력
- **종료 시**: HANDOVER_HF_v4_P6.md 작성:
  - 변경된 파일 목록 (line count delta)
  - 검증 frame 5개 경로 (Mac local path)
  - 회귀 테스트 결과 (`pytest -v` tail)
  - 위험 §7 중 실제 발생한 항목 + 대응 결과
  - 다음 Phase 진입 권장 (P4 reel? P5 음악?)
- **차단 시**: 즉시 중단하고 사용자에게 옵션 제시 (HP 다운 / 회귀 발생 / 시각 검증 실패 등)
- **commit 메시지**: `feat(P6): editor.html HF 시각화 토글 (default OFF + fallback)`
- **branch**: `main` 직접 push (단순 UI 작업)

---

## 9. 환경

| 항목 | 값 |
|---|---|
| Mac sermon-app | `/Users/hwasungkim/Library/CloudStorage/GoogleDrive-sharonkim71@gmail.com/내 드라이브/AI/교회 앱/sermon-app` |
| Mac Flask port | 5001 |
| Mac Tailscale | 100.89.99.106 |
| HP hf-server | http://100.104.121.7:8770 |
| HP systemd unit | `hf-server.service` |
| Gitea | http://100.116.4.84:3000/quant/sermon-app |
| Gitea SSH | `ssh://git@100.116.4.84:2222/quant/sermon-app.git` |
| Gemma 4 | http://100.104.121.7:11434 (`/api/llm/health` 통해 확인) |

---

## 10. 즉시 다음 액션

1. §0 시작 절차 실행 → `/api/render/health` ok=true 확인
2. 회귀 baseline — 체크박스 추가 전에 OFF 상태 동작 1회 확인 + frame 캡처
3. §3.1–3.5 UI 변경 적용 (체크박스 + status pill + JS)
4. §4 `/api/render/<id>/mp4` endpoint 추가
5. §6 Gate 5개 직접 시각 검증 + frame 5개 캡처
6. HANDOVER_HF_v4_P6.md 작성
7. git commit + push
8. 사용자에게 결과 보고

---

## 변경 이력

| 버전 | 일자 | 변경 |
|---|---|---|
| v1.0 | 2026-05-03 | 최초 작성 — P3 완료 후 critical path 마지막 |
