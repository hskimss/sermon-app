# P0 작업지시서 — HP-Z2-LLM HyperFrames 렌더 서버 부팅

**대상 노드:** HP-Z2-LLM (`100.104.121.7`)
**실행자:** Anti (Linux Claude Code) — 사용자가 SSH 후 직접 켜고 운영
**상위 설계:** `HYPERFRAMES_DESIGN.md` §2.1 / §9
**검증:** P0 = 한국어 깨짐 없는 5초 검은 화면 mp4 + `/health` 200

---

## 0. 사전 확인

```bash
ssh quant@100.104.121.7
hostname && lsb_release -a 2>/dev/null | head -3
nvidia-smi | head -3
ffmpeg -version | head -1
```

GPU + ffmpeg 보이면 진행.

---

## 1. Node 22 + 작업 디렉토리

```bash
mkdir -p ~/hyperframes-render && cd ~/hyperframes-render

# Node 22 (없으면)
node --version 2>/dev/null | grep -q 'v22' || {
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
  export NVM_DIR="$HOME/.nvm"
  . "$NVM_DIR/nvm.sh"
  nvm install 22 && nvm use 22
}
node --version  # v22.x 이어야 함

# pnpm (옵션)
npm i -g pnpm 2>/dev/null || true
```

---

## 2. HyperFrames + 의존성

```bash
cd ~/hyperframes-render
[ -f package.json ] || npm init -y
npm install hyperframes @hyperframes/core @hyperframes/engine @hyperframes/producer
npm install --save-dev playwright
npx playwright install --with-deps chromium

# Python 측 (Flask + ffmpeg-python)
pip3 install --user flask requests ffmpeg-python
```

---

## 3. 한국어 폰트 (Pretendard + Noto Serif KR)

```bash
sudo apt-get update
sudo apt-get install -y fonts-noto-cjk fonts-noto-cjk-extra fontconfig

mkdir -p ~/.local/share/fonts
curl -L -o ~/.local/share/fonts/PretendardVariable.woff2 \
  "https://github.com/orioncactus/pretendard/raw/main/packages/pretendard/dist/web/variable/woff2/PretendardVariable.woff2"
curl -L -o ~/.local/share/fonts/PretendardVariable.ttf \
  "https://github.com/orioncactus/pretendard/raw/main/packages/pretendard/dist/public/variable/PretendardVariable.ttf"
fc-cache -fv

# 검증
fc-list | grep -i -E "pretendard|noto.*serif.*kr" | head -5
```

---

## 4. 한국어 smoke 컴포지션 (5초 mp4)

```bash
cat > ~/hyperframes-render/smoke.html <<'HTML'
<!DOCTYPE html><html><head><meta charset="UTF-8">
<style>
  @font-face { font-family: 'Pretendard';
    src: local('Pretendard Variable'), local('Pretendard'); }
  body { margin:0; background:#0E1116; color:#fff;
         font-family:'Pretendard','Noto Serif KR',sans-serif; }
  .stage { width:1080px; height:1920px; display:grid; place-items:center; }
  h1 { font-weight:800; font-size:84px; }
  .gold { color:#D4AF37; }
</style></head><body>
<div class="stage" data-composition-id="smoke" data-duration="5000" data-fps="30">
  <h1>안녕 <span class="gold">하나님</span></h1>
</div>
<script>
  window.__timelines = { smoke: { duration: 5 } };
  window.__hyperframes_ready = true;
</script>
</body></html>
HTML

# 렌더 (HyperFrames CLI)
npx hyperframes render smoke.html -o smoke.mp4 --duration 5 --fps 30 || \
  echo "[!] CLI 인자가 다르면 npx hyperframes --help 로 확인"

# 검증
ffprobe -v error -show_entries stream=width,height,codec_name,duration smoke.mp4
ls -lh smoke.mp4
```

**합격 기준:** `smoke.mp4` 가 1080×1920, ~5s, h264 — 그리고 한 프레임 추출해서 한국어가 □□ 아닌 글자로 보임:

```bash
ffmpeg -y -ss 2 -i smoke.mp4 -frames:v 1 smoke_frame.png && ls -lh smoke_frame.png
```

(검토는 사람 눈으로 한 프레임)

---

## 5. hf-server :8766 — 최소 골격 (sermon-app과 호환)

설계 §2.2의 `/render` `/render/<id>/status` `/health` 3개 엔드포인트만 우선 구현. 비동기 큐는 P2 본 단계.

```bash
mkdir -p ~/hyperframes-render/server ~/hyperframes-render/output ~/hyperframes-render/tmp

cat > ~/hyperframes-render/server/hf_server.py <<'PY'
"""HP HyperFrames 렌더 서버 — P0 골격 (동기 단일 작업).

- POST /render          → 즉시 큐잉 + 즉시 렌더 (배치 큐는 P2 본 단계)
- GET  /render/<id>/status
- GET  /health
- GET  /output/<file>   → 산출 mp4 다운로드
"""
import json, os, subprocess, threading, time, uuid
from pathlib import Path
from flask import Flask, jsonify, request, send_from_directory

ROOT = Path(__file__).resolve().parent.parent
COMPOSITIONS = ROOT / "compositions"   # 사용자 또는 sermon-app이 sync로 채움
TMP = ROOT / "tmp"
OUT = ROOT / "output"
COMPOSITIONS.mkdir(exist_ok=True)
TMP.mkdir(exist_ok=True); OUT.mkdir(exist_ok=True)

app = Flask(__name__)
JOBS = {}   # render_id → {status, mp4_path, error}

def _render_sync(render_id: str, payload: dict):
    """동기 렌더 — 단일 작업 처리. 큐는 P2."""
    JOBS[render_id] = {"status": "rendering", "started_at": time.time()}
    try:
        comp = payload.get("composition", "sermon_short_v1")
        tpl = COMPOSITIONS / f"{comp}.html"
        if not tpl.exists():
            raise FileNotFoundError(f"composition {comp}.html 없음")

        # placeholder 치환
        html = tpl.read_text()
        words = payload.get("words", [])
        refs  = payload.get("scripture_refs", [])
        duration = float(payload.get("audio_clip", {}).get("duration", 60))
        repl = {
            "{{COMPOSITION_ID}}": render_id,
            "{{DURATION_MS}}": str(int(duration * 1000)),
            "{{TOTAL_SEC}}": f"{duration:.2f}",
            "{{SCRIPTURE_REF}}": "", "{{SCRIPTURE_TEXT}}": "",
            "{{SCRIPTURE_TRANS}}": "", "{{CHANNEL}}": "A Church London",
            "{{WORDS_JSON}}": json.dumps(words, ensure_ascii=False),
            "{{SCRIPTURE_REFS_JSON}}": json.dumps(refs, ensure_ascii=False),
        }
        for k, v in repl.items():
            html = html.replace(k, v)

        work = TMP / render_id; work.mkdir(exist_ok=True)
        (work / "index.html").write_text(html)

        out_mp4 = OUT / f"{render_id}.mp4"
        # NVENC: -c:v h264_nvenc (가능 시), 폴백 libx264
        cmd = [
            "npx", "hyperframes", "render", str(work / "index.html"),
            "-o", str(out_mp4), "--duration", str(duration), "--fps", "30",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=900,
                              cwd=str(ROOT))
        if proc.returncode != 0 or not out_mp4.exists():
            raise RuntimeError(f"render 실패: {proc.stderr[-1500:]}")

        # audio mux (audio_url 다운로드 → ffmpeg merge)
        audio_url = payload.get("audio_url")
        audio_clip = payload.get("audio_clip") or {}
        if audio_url:
            import requests
            audio_path = work / "audio.bin"
            r = requests.get(audio_url, timeout=120, stream=True); r.raise_for_status()
            with open(audio_path, "wb") as f:
                for chunk in r.iter_content(1<<16): f.write(chunk)
            muxed = OUT / f"{render_id}.muxed.mp4"
            ss = float(audio_clip.get("start_sec", 0))
            dur = float(audio_clip.get("duration", duration))
            mux_cmd = [
                "ffmpeg", "-y", "-i", str(out_mp4),
                "-ss", f"{ss:.3f}", "-t", f"{dur:.3f}", "-i", str(audio_path),
                "-map", "0:v:0", "-map", "1:a:0",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                str(muxed),
            ]
            mp = subprocess.run(mux_cmd, capture_output=True, text=True, timeout=300)
            if mp.returncode == 0 and muxed.exists():
                out_mp4.unlink()
                muxed.rename(out_mp4)

        JOBS[render_id].update({
            "status": "ready",
            "mp4_path": str(out_mp4),
            "size_bytes": out_mp4.stat().st_size,
            "completed_at": time.time(),
        })

        # callback (옵션)
        cb = payload.get("callback_url")
        if cb:
            try:
                import requests
                requests.post(cb, json={
                    "render_id": render_id, "status": "ready",
                    "mp4_url": f"/output/{render_id}.mp4",
                    "duration": duration,
                    "size_bytes": out_mp4.stat().st_size,
                }, timeout=10)
            except Exception:
                pass
    except Exception as ex:
        JOBS[render_id] = {"status": "error", "error": str(ex)}


@app.get("/health")
def health():
    return jsonify({"status": "ok", "jobs": len(JOBS)})

@app.post("/render")
def render():
    payload = request.get_json(force=True) or {}
    rid = uuid.uuid4().hex[:12]
    JOBS[rid] = {"status": "queued"}
    threading.Thread(target=_render_sync, args=(rid, payload), daemon=True).start()
    return jsonify({"render_id": rid, "status": "queued", "estimated_sec": 180})

@app.get("/render/<rid>/status")
def status(rid):
    j = JOBS.get(rid)
    if not j: return jsonify({"error": "unknown render_id"}), 404
    return jsonify({"render_id": rid, **j})

@app.get("/output/<path:fn>")
def output(fn):
    return send_from_directory(str(OUT), fn)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8766, debug=False)
PY

# 컴포지션 sync (sermon-app 의 sermon_short_v1.html을 HP로 복사)
# (Mac에서 한 번만 실행 — Anti가 아니라 사용자가)
#   scp '~/Library/.../sermon-app/app/render/compositions/sermon_short_v1.html' \
#       quant@100.104.121.7:~/hyperframes-render/compositions/

# 실행
cd ~/hyperframes-render
python3 server/hf_server.py &
HF_PID=$!
sleep 2

# 검증
curl -s http://localhost:8766/health
echo
curl -s -X POST http://localhost:8766/render -H 'Content-Type: application/json' \
  -d '{"composition":"sermon_short_v1","audio_clip":{"start_sec":0,"duration":5},"words":[{"word":"테스트","start":0.5,"end":1.5,"is_emphasis":false}]}' \
  | tee /tmp/render_resp.json
echo

# 5분 정도 폴링
RID=$(python3 -c "import json,sys; print(json.load(open('/tmp/render_resp.json'))['render_id'])")
for i in 1 2 3 4 5 6 7 8 9 10 11 12; do
  sleep 10
  curl -s http://localhost:8766/render/$RID/status
  echo
done
```

---

## 6. systemd 등록 (영구화)

```bash
sudo tee /etc/systemd/system/hf-server.service > /dev/null <<UNIT
[Unit]
Description=HyperFrames render server
After=network.target

[Service]
User=quant
WorkingDirectory=/home/quant/hyperframes-render
ExecStart=/usr/bin/python3 /home/quant/hyperframes-render/server/hf_server.py
Restart=on-failure
Environment=PATH=/home/quant/.nvm/versions/node/v22.0.0/bin:/usr/bin:/bin

[Install]
WantedBy=multi-user.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable --now hf-server
sudo systemctl status hf-server --no-pager | head -10
```

---

## 7. 검증 체크리스트

```
[ ] node --version → v22.x
[ ] fc-list | grep -i pretendard 결과 1+ 줄
[ ] smoke.mp4 ffprobe 통과 (1080×1920, 5s, h264)
[ ] smoke_frame.png에서 "안녕 하나님" 깨짐 없이 표시
[ ] curl /health 200
[ ] curl /render → render_id 반환
[ ] /render/<id>/status 가 queued → rendering → ready
[ ] systemctl is-active hf-server == active
```

---

## 8. Mac 측 검증 (P0 통과 후)

```bash
# Mac에서
cd "~/Library/CloudStorage/GoogleDrive-sharonkim71@gmail.com/내 드라이브/AI/교회 앱/sermon-app"
.venv/bin/python -m flask --app app.server run --port 5001 &

# render health
curl -s http://127.0.0.1:5001/api/render/health  # → {"ok": true}

# dry_run으로 payload만 점검
curl -s -X POST http://127.0.0.1:5001/api/job/20260428_070532_u7DodpeoTzg/render \
  -H 'Content-Type: application/json' \
  -d '{"clip":{"start_sec":0,"end_sec":60},"dry_run":true}' | jq '.payload_preview | keys'
```

`render_engine: hyperframes` + render_id 받으면 P0–P2 통합 OK.

---

## 메모

- HP IP `100.104.121.7` — 설계 문서 §2.1 기준. 실제 IP가 다르면 sermon-app `app/render/client.py`의 `HF_RENDER_URL` 환경변수 또는 default 수정.
- HyperFrames CLI 옵션이 v0.x 변동 가능 → `npx hyperframes --help` 1회 점검 후 `_render_sync`의 cmd 인자 조정.
- P0은 동기 단일 렌더. 동시 작업 / queue / NVENC 명시 인코더는 P2 본 단계.
