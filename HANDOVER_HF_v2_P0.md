# P0 실행 완료 — HP HyperFrames 렌더 서버 가동

**완료일:** 2026-05-03 18:57 BST
**실행자:** Mac Claude (자비스 모드 자율주행 — SSH 직접 실행)
**HP 노드:** `100.104.121.7` (hp-z2-llm, Ubuntu 24.04, RTX 3060 ×2)

---

## §0–§7 단계별 결과

| § | 단계 | 결과 |
|---|------|------|
| 0 | ffmpeg/NVENC/Python/Disk | ✅ ffmpeg 6.1.1 + NVENC h264/hevc/av1, Python 3.12, 597GB |
| 1 | Node 22 (nvm) | ✅ v22.22.2 + npm v10.9.7 (default alias) |
| 2 | HyperFrames + Playwright + chromium | ✅ hyperframes v0.4.42 + Chrome Headless 147 + Flask/requests/ffmpeg-python |
| 3 | 한국어 폰트 | ✅ Pretendard Variable (woff2+ttf) + Noto Serif CJK KR (Bold/Medium) |
| 4 | smoke 5초 렌더 + ffprobe + 프레임 | ✅ 1080×1920, 5.0s, h264 / 시각: "안녕 **하나님**" 깨짐 없음 |
| 5 | hf-server :8770 + composition + /render | ✅ /health 200, /render→queued→ready 8s, 110KB mp4 |
| 6 | systemd 등록 | ✅ `hf-server.service` enabled+active (PID 1099923, 20MB RAM) |
| 7 | Mac→HP 통합 검증 | ✅ 실 transcript (21 words) → HP → 10.3s 만에 400KB mp4 → 자막 한국어 정상 |

---

## 발생/해결한 변동

| 의뢰서 | 실 환경 | 조정 |
|--------|---------|------|
| `:8766` 가정 | 이미 `/home/quant/video-pipeline/app.py`가 점유 | **`:8770`으로 이동**. `HF_PORT` env 노출 |
| `npx hyperframes render <html>` | v0.4.42는 **프로젝트 디렉토리** 받음 | hf_server.py가 매 요청마다 `tmp/<rid>/` 프로젝트 dir 생성 + `index.html` + `meta.json` + `hyperframes.json` 자동 생성 |
| body data-* | v0.4.42는 `<div id="root" data-composition-id ...>` 구조 | hf_server.py가 root div 자동 wrap (이미 있으면 skip) |
| `data-duration` ms | v0.4.42는 **초** | hf_server.py에서 둘 다 치환 (`{{DURATION_MS}}`, `{{TOTAL_SEC}}`) |
| nvm node 경로 | systemd 환경에 없음 | unit Environment에 PATH 명시 + 코드의 `NODE_BIN` 자동 탐지 |

`sermon-app/app/render/client.py` default URL을 **`http://100.104.121.7:8770`** 으로 갱신.

---

## 통합 호출 절차

```bash
# Mac sermon-app (이미 작동)
cd "교회 앱/sermon-app"
.venv/bin/python -m flask --app app.server run --port 5001

# Mac에서 HP 직접 호출 (sermon-app 거치지 않을 때)
.venv/bin/python -c "
import json, sys; sys.path.insert(0,'.')
from app.render import build_short_payload; from pathlib import Path
p = build_short_payload(job_id='<JOB_ID>', clip={'start_sec':0,'end_sec':60},
                        jobs_dir=Path('jobs'))
open('/tmp/payload.json','w').write(json.dumps(p, ensure_ascii=False))
"
curl -X POST http://100.104.121.7:8770/render -H 'Content-Type: application/json' \
  --data @/tmp/payload.json
```

상태 polling: `curl http://100.104.121.7:8770/render/<rid>/status`
mp4 다운로드: `curl http://100.104.121.7:8770/output/<rid>.mp4 -o out.mp4`

---

## P0에서 드러난 P1 후속 보정

1. **`-webkit-text-stroke` 효과 약함**: chromium이 word 별로는 잘 안 그림. text-shadow 다중 stack으로 대체 검토.
2. **단어 좌측 정렬**: `.captions` `text-align:center`가 word inline-block에서 의도대로 작동 안 함. flex wrap + justify-content:center로 보정.
3. **emphasis 골드** 단어 별 적용은 작동 (P0 dummy 5단어 검증). 실 데이터에 emphasis_ids 캐시 비어있어 골드 0개 — Gemma 호출로 채울 것.
4. **audio mux**: `mac-tailscale` 호스트가 HP에서 미해결. Mac Tailscale IP로 `SERMON_APP_BASE_URL` env 명시 필요.

---

## 시각 결과 샘플 (Mac /tmp/p0_verify/)

| 파일 | 출처 | 결과 |
|------|------|------|
| `ko_frame.png` | 한국어 smoke (안녕 하나님) | 깨짐 없음, 골드 강조 OK |
| `render1_frame.png` | dummy 5단어 (너는 **하나님을** 사랑하라) | 흰+골드 분리 OK |
| `integration_frame.png` | 실 transcript 21단어 | 두 줄 자동 줄바꿈, 한국어 정상 |

---

## 운영

- 자동 시작: `systemctl status hf-server` (재부팅 시 자동)
- 로그: `journalctl -u hf-server -f`
- 재시작: `sudo systemctl restart hf-server`
- 포트 변경: unit `Environment=HF_PORT=...` 또는 `HF_PORT=9999 python3 server/hf_server.py`
