# P6 — editor.html HF 시각화 토글 인계

**완료일:** 2026-05-03 (P3 직후)
**모드:** 자비스 (Proposer→Critic→Synthesizer)
**작업의뢰서:** `P6_WORK_ORDER.md`

---

## 변경 파일 (line delta)

| 파일 | 변동 | 핵심 변경 |
|------|------|----------|
| `app/render/client.py` | +13 | `stream_output()` 메소드 — Flask가 generator로 받을 수 있는 streaming response |
| `app/server.py` | +56 | `GET /api/render/<id>/mp4` (안전 ID 검증 + Mac 캐시 + send_file conditional/Range) + `/api/render/health` 에 `host` 필드 |
| `app/static/editor.html` | +185 | 체크박스 행 + status pill + IIFE 격리 JS (capture-phase 가로채기 + localStorage 추적 + 5분 timeout fallback) |
| `tests/test_render_routes.py` | NEW (102) | 7개 단위 테스트 (health/mp4 reject/409 not-ready/502 unreachable/cache stream/status passthrough) |
| `HANDOVER_HF_v4_P6.md` | NEW | 본 문서 |

기존 `/api/job/<id>/llm-bulk-export`, `/api/job/<id>/llm-highlight-reel` **무변경**. 회귀 위험 0.

---

## Gate 결과

| # | 항목 | 결과 |
|---|------|------|
| **A** | `/api/render/health` 정상 시 `{"ok":true,...}` | ✅ `/tmp/p6_verify/health_up.json` |
| **B** | HP `systemctl stop hf-server` → `ok:false` | ✅ `/tmp/p6_verify/health_down.json` |
| **C** | restart → `ok:true` 즉시 복구 | ✅ `/tmp/p6_verify/health_restored.json` |
| **D** | `/api/render/<id>/mp4` 캐시 적중 시 send_file (HP 미호출) | ✅ pytest `test_mp4_streams_cached_file` PASS |
| **E** | invalid render_id reject | ✅ pytest `test_mp4_rejects_invalid_render_id` PASS |
| pytest | `test_render_routes.py` | ✅ 7/7 PASS |
| 회귀 | 기존 두 endpoint 무변경 | ✅ git diff 확인 |

`tests/test_static_js.py` 가 collection 단계에서 PEP 604 union syntax 에러 (Python 3.9 호환 미흡) — **본 P6 작업 외 기존 결함**. 별도 추후 수정 필요.

---

## UI 동작 (사용자 시점 — Flask reload 후)

1. **페이지 로드** → 상단 우측 pill `🟢 사용 가능` (HP up) 또는 `🔴 HP 다운 — FFmpeg 모드만` (down).
2. **체크박스 OFF (default)** — 기존 `📦 5개 모두 export` / `🎞 합쳐서 reel` 100% 그대로.
3. **체크박스 ON**:
   - reel 버튼 자동 disabled + tooltip "P4 reel composition 대기"
   - `📦 5개 모두 export` 클릭 → 5개 클립 순차 렌더, 각 줄 실시간 갱신
     - `⏳ clip 1/5 (질문/8) — rendering 12s`
     - `✓ clip 1/5 — 32s — 📥 1.3MB` (직접 download 링크)
   - 모든 시도 실패 시 자동 FFmpeg fallback + 사용자 토스트
4. **HP 다운 시 페이지 새로고침** → pill 빨강 + 체크박스 disabled (회귀 0)

---

## 자비스 모드 — Critic 사전 반영

| 발견 | 반영 |
|------|------|
| 회귀 위험 (기존 click handler 수정) | **capture phase + stopImmediatePropagation**. OFF 상태에서 가로채지 않음 |
| HP 단일 머신 OOM (5개 병렬) | **순차 렌더** (`for...await`) |
| 렌더 5분+ 인내심 | 5초 polling, 첫 mp4 받자마자 download 링크 노출 |
| 페이지 닫힘 시 추적 끊김 | `localStorage` (`LS_KEY = sermon-app:p6:active-renders:<jobId>`) — 다음 방문 시 복원 가능 |
| 디렉토리 traversal 위험 | `_safe_render_id()` `[A-Za-z0-9_\-]{4,64}` 화이트리스트 |
| 큰 mp4 Tailscale 느림 | `send_file(conditional=True)` Range 지원 + Mac `~/.cache/sermon-app/render/` 영구 캐시 |
| editor.html 큰 파일 부피 | **새 IIFE 블록**으로 격리 (`<script>` 별도). 기존 IIFE 손대지 않음 |
| reel composition 미구현 (P4 대기) | 체크박스 ON 시 reel 버튼 disabled + tooltip |
| Flask 재시작 안 하면 새 endpoint 미활성 | handover에 명시 (사용자가 `pkill flask && .venv/bin/python -m flask --app app.server run --port 5001`) |

---

## 환경

| Key | Default | 메모 |
|-----|---------|------|
| `HF_RENDER_URL` | `http://100.104.121.7:8770` | 변경 금지 |
| `SERMON_APP_BASE_URL` | `http://100.89.99.106:5001` | Mac Tailscale IP |
| Mac 캐시 dir | `~/.cache/sermon-app/render/` | mp4 영구 캐시 (수동 삭제 가능) |

---

## 다음 액션

1. **사용자 측 검증** (자비스 자율 불가):
   - Flask 재시작 (`pkill -f flask; cd sermon-app; .venv/bin/python -m flask --app app.server run --port 5001`)
   - Editor 페이지 열고 체크박스 OFF 상태로 1회 export → mp3 정상 받기 (회귀 baseline)
   - 체크박스 ON → 1개 클립이라도 렌더 진행되는지 확인 → mp4 download
2. **권장 다음 Phase**: HF_PHASE_PLAN_v2 §3 순서대로 **P4 (sermon_reel_v1)** — 2일 공수. P6의 reel 버튼 P4 대기 처리 자동 해제.

---

## commit

```
feat(P6): editor.html HF 시각화 토글 (default OFF + fallback)

- editor.html: 체크박스 + status pill + capture-phase 가로채기
  + 순차 렌더 + localStorage 추적 + 5분 timeout fallback
- server.py: GET /api/render/<id>/mp4 (안전 ID + Mac 캐시 + Range)
  + /api/render/health에 host 필드
- client.py: stream_output() — generator-style streaming
- tests/test_render_routes.py 7/7 PASS
```
