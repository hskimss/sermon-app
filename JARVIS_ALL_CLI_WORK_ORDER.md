# All-CLI 자비스 작업지시서 — composition v2 + WhisperX + ffmpeg loudnorm

> 위임: Claude Code CLI (linux-quant 또는 sermon-app 세션)
> **사용자 manual 0 — claude.ai/design 우회 (HF Skills slash command) + Auphonic 우회 (ffmpeg loudnorm sidechaincompress)**
> 자체 완결 — 본 문서만으로 진행, 외부 가입/설정 0
> 예상 공수: 4-6시간 (모두 CLI/jarvis)
> 결과: 5/10 → 8.5/10 측정

---

## 0. 시작 절차 (필수)

```bash
# Working dir
SERMON="/Users/hwasungkim/Library/CloudStorage/GoogleDrive-sharonkim71@gmail.com/내 드라이브/AI/교회 앱/sermon-app"
cd "$SERMON"

# 정독 (이 순서)
cat GIANT_MODE_v2_RESEARCH.md         # 8/10 가는 stack 정의
cat HF_PHASE_PLAN_v2.md                # 전체 Phase
cat CLAUDE_DESIGN_BRIEF.md             # composition v2 사양
cat HANDOVER_HF_v4_P6.md               # P6 결과

# Health 확인
curl -s http://localhost:5001/api/render/health      # {"ok":true}
ssh -o BatchMode=yes quant@100.104.121.7 'systemctl is-active hf-server'  # active
ssh -o BatchMode=yes quant@100.104.121.7 'curl -s http://localhost:8770/health | head -c 200'
```

**중단 조건**:
- HP `:8770` ok=false → systemd 점검
- Mac Flask 다운 → 재기동 후 진행
- Claude Code CLI 가 없거나 logged out → `claude login` 후 진행

---

## 1. 가드레일 (절대 규칙)

1. **Gitea 전용** — `quant/sermon-app`. GitHub 금지. 신규 repo 금지.
2. **사용자 manual 0** — 어떤 단계에서도 사용자에게 "가입하세요" / "토큰 받아주세요" / "웹사이트 들어가세요" 요청 금지. 모두 CLI 로 해결.
3. **claude.ai/design 우회** — HF Skills 시스템 (`npx skills add heygen-com/hyperframes` + `/hyperframes` slash command) 으로 composition v2 직접 생성. Web UI 안 거침.
4. **Auphonic 우회** — ffmpeg `loudnorm + sidechaincompress` 로 -16 LUFS 자체 마스터링. 외부 API 미사용.
5. **검증 frame obligatory** — Gate 통과 시점마다 frame 캡처 + 사용자에게 시각 보고.
6. **회귀 0** — sermon_short_v1 그대로 유지 (v2 default + v1 옵션 토글). 기존 endpoint 응답 schema 변경 금지.

---

## 2. Phase A — composition v2 생성 (Claude Code + HF Skills)

### 2.1 HF Skills 설치 (HP 서버)

```bash
ssh -o BatchMode=yes quant@100.104.121.7 'cd /home/quant/hyperframes-render && \
  source ~/.nvm/nvm.sh && nvm use 22 && \
  npx --yes skills add heygen-com/hyperframes && \
  ls .claude/skills/hyperframes/ 2>&1 | head -5'
```

Verify: `.claude/skills/hyperframes/SKILL.md` 존재 + skill 등록.

### 2.2 sermon_short_v2 composition 생성 — Claude Code subprocess

**중요**: Claude Code CLI 가 HP 에 설치되어 있다고 가정 (`claude --version`). 없으면:
```bash
ssh quant@100.104.121.7 'curl -fsSL https://claude.ai/install.sh | sh'
```

작업 디렉토리:
```bash
ssh -o BatchMode=yes quant@100.104.121.7 'mkdir -p ~/sermon-composition-v2 && cd ~/sermon-composition-v2 && \
  cp /Users/.../CLAUDE_DESIGN_BRIEF.md .'
```

**핵심: Claude Code 비대화형 호출** with HF skill:
```bash
ssh -o BatchMode=yes quant@100.104.121.7 << 'EOF'
cd ~/sermon-composition-v2
source ~/.nvm/nvm.sh && nvm use 22
claude --print --skill hyperframes --output-format json << PROMPT
Use the HyperFrames skill to generate a sermon_short_v2 composition.
Read the brief at ./CLAUDE_DESIGN_BRIEF.md and produce:
  - index.html (single-file composition with inline CSS/GSAP/shader)
  - preview.html (local preview wrapper)
  - README.md (inject contract + how sermon-app populates {{INJECT_POINTS}})
  - DESIGN.md (design choices)

Strict requirements:
1. 5 scenes: Hook(0-6s) / Scripture(6-14s) / Body lower-third captions(14-48s) / Austerity(48-54s) / Outro(54-60s)
2. data-duration in seconds, data-width=1080 data-height=1920
3. {{INJECT_POINTS}}: HOOK_TEXT, HOOK_ARCHETYPE, WORDS_JSON, SCRIPTURE_REFS_JSON, SCRIPTURE_TEXT, AUSTERITY_PHRASE, AUDIO_URL, MUSIC_BED_URL, TOTAL_SEC
4. text-shadow stack (NOT -webkit-text-stroke)
5. word-break: keep-all on all Korean text
6. Pretendard via CDN @import
7. Noto Serif KR for scripture
8. 8-direction text-shadow stroke
9. Word fade-in 0.3-0.4s power2.out, NO bouncy springs
10. 2 shader transitions (dissolve recommended) at scene 1->2 and 3->4
11. Graceful degradation: empty SCRIPTURE_REFS_JSON skips scene 2; empty WORDS_JSON skips scene 3
12. Final output passes 'npx hyperframes lint' with 0 errors

Save all 4 files in current directory.
PROMPT
EOF
```

If `--skill hyperframes` 옵션이 없거나 실패하면 fallback: `claude` 인터랙티브 모드에서 슬래시 `/hyperframes` 실행.

### 2.3 Lint 통과 검증

```bash
ssh -o BatchMode=yes quant@100.104.121.7 'cd ~/sermon-composition-v2 && \
  source ~/.nvm/nvm.sh && nvm use 22 && \
  npx hyperframes lint . 2>&1 | tail -10'
```

Lint 에러 0 이어야 다음 단계. 에러 있으면 Claude Code 에 다시 instruct.

### 2.4 sermon-app 으로 sync

```bash
COMP_DIR="/Users/hwasungkim/Library/CloudStorage/GoogleDrive-sharonkim71@gmail.com/내 드라이브/AI/교회 앱/sermon-app/app/render/compositions/sermon_short_v2"
mkdir -p "$COMP_DIR"
scp -o BatchMode=yes quant@100.104.121.7:~/sermon-composition-v2/{index.html,preview.html,README.md,DESIGN.md} "$COMP_DIR/"

# HP hf-server 의 compositions/ 디렉토리에도 sync
ssh -o BatchMode=yes quant@100.104.121.7 'cp -r ~/sermon-composition-v2 /home/quant/hyperframes-render/compositions/sermon_short_v2'
```

### 2.5 Gate A 통과 조건

- [ ] `app/render/compositions/sermon_short_v2/index.html` 존재 + `npx hyperframes lint` pass
- [ ] HP `/home/quant/hyperframes-render/compositions/sermon_short_v2/` 동기화
- [ ] DESIGN.md 가 5 scenes + 2 transitions + inject contract 명시

---

## 3. Phase B — payload v2 + server 분기

### 3.1 `app/render/payload.py::build_short_payload_v2()` 추가

기존 `build_short_payload` 와 동일 시그니처 + 새 inject keys:

```python
def build_short_payload_v2(job_id, clip, *, jobs_dir, ...):
    payload = build_short_payload(job_id, clip, jobs_dir=jobs_dir, composition="sermon_short_v2", ...)
    
    # v2 specific keys
    words = payload["transcript_segments"][0]["words"] if payload["transcript_segments"] else []
    hook_words = words[:8]  # 첫 8 단어
    payload["hook_text"] = " ".join(w["word"] for w in hook_words).strip()
    payload["hook_archetype"] = clip.get("hook_archetype") or "질문"
    payload["austerity_phrase"] = clip.get("austerity_phrase") or "주님 앞에 잠잠하라"
    payload["music_bed_url"] = ""  # 빈 placeholder, music bed 라이브러리는 추후
    return payload
```

DESIGN.md 의 inject contract 와 100% 일치하는지 검증.

### 3.2 `app/server.py::api_render` 분기

```python
@app.route("/api/job/<job_id>/render", methods=["POST"])
def api_render(job_id):
    body = request.get_json() or {}
    comp = body.get("composition", "sermon_short_v2")  # default v2
    if comp == "sermon_short_v2":
        payload = build_short_payload_v2(...)
    else:
        payload = build_short_payload(...)
    ...
```

### 3.3 editor.html 토글 추가

`<select id="hf-comp-select">` 에 v1/v2 옵션. default v2.

P6 IIFE 의 fetch body에 `composition: chk.checked ? document.getElementById("hf-comp-select").value : "sermon_short_v1"` 포함.

### 3.4 Gate B 통과 조건

- [ ] `dry_run=true` POST /api/job/<id>/render with composition=sermon_short_v2 → payload preview에 hook_text/austerity_phrase/scripture_refs 모두 채워짐
- [ ] editor.html 새로고침 시 v2 default 토글 visible
- [ ] 회귀: composition=sermon_short_v1 명시하면 기존 payload 그대로 (회귀 0)

---

## 4. Phase C — WhisperX Korean align

### 4.1 HP 서버에 WhisperX 설치

```bash
ssh -o BatchMode=yes quant@100.104.121.7 'pip3 install --user --break-system-packages whisperx==3.1.5 2>&1 | tail -5'

# 한국어 wav2vec2 사전 다운로드 (~1.2 GB)
ssh -o BatchMode=yes quant@100.104.121.7 'python3 -c "
from huggingface_hub import snapshot_download
snapshot_download(\"kresnik/wav2vec2-large-xlsr-korean\")
print(\"OK\")
"'
```

### 4.2 whisperx-server :8771

`/home/quant/hyperframes-render/server/whisperx_server.py` 작성:

```python
"""WhisperX align server. POST /align takes {audio_path, transcript_segments}
and returns word-level aligned segments with ±50ms accuracy (vs ±200ms input).
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import whisperx, json, threading

PORT = 8771
DEVICE = "cuda"
print("Loading WhisperX align model (Korean)...", flush=True)
align_model, metadata = whisperx.load_align_model(
    language_code="ko", device=DEVICE,
    model_name="kresnik/wav2vec2-large-xlsr-korean")
print("OK", flush=True)
_lock = threading.Lock()

class H(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/align":
            return self._j(404, {"error": "not found"})
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        audio = body["audio_path"]
        segs = [{"start": s["start"], "end": s["end"], "text": s["text"]}
                for s in body["transcript_segments"]]
        with _lock:
            r = whisperx.align(segs, align_model, metadata, audio, DEVICE,
                               return_char_alignments=False)
        out = {"language": "ko", "segments": [
            {"start": s["start"], "end": s["end"], "text": s["text"],
             "words": [{"word": w["word"], "start": w["start"], "end": w["end"],
                        "probability": w.get("score", 1.0)}
                       for w in (s.get("words") or [])]}
            for s in r["segments"]
        ]}
        return self._j(200, out)
    def _j(self, code, data):
        b = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code); self.send_header("Content-Length", len(b))
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers(); self.wfile.write(b)
    def log_message(self, *a): pass

if __name__ == "__main__":
    print(f"WhisperX align server :{PORT}", flush=True)
    HTTPServer(("0.0.0.0", PORT), H).serve_forever()
```

systemd unit `whisperx-server.service` (hf-server 패턴):
```ini
[Unit]
Description=WhisperX Korean align server
After=network.target

[Service]
Type=simple
User=quant
Environment=PATH=/home/quant/.nvm/versions/node/v22.22.2/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=/usr/bin/python3 /home/quant/hyperframes-render/server/whisperx_server.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable whisperx-server.service
sudo systemctl start whisperx-server.service
sleep 30  # 모델 로드 시간
curl -s http://localhost:8771/align -X POST -d '{"audio_path":"/tmp/x","transcript_segments":[]}' --max-time 5  # health
```

### 4.3 sermon-app pipeline 통합

`app/pipeline.py::transcribe()` 에 align step 추가:

```python
def transcribe(src, dst, ..., align=True):
    # 기존 mlx-whisper or HP whisper-turbo
    initial = json.loads(dst.read_text())
    
    if align and os.getenv("WHISPERX_ALIGN", "1") == "1":
        try:
            r = requests.post("http://100.104.121.7:8771/align",
                json={"audio_path": str(src),
                      "transcript_segments": initial.get("segments", [])},
                timeout=180)
            if r.status_code == 200:
                # Backup pre-align
                dst.with_suffix(".pre_align.json").write_text(dst.read_text())
                # Write aligned
                aligned = r.json()
                dst.write_text(json.dumps(aligned, ensure_ascii=False, indent=2))
                if job_id:
                    _update_phase(job_id, "transcribing", aligned=True)
        except Exception:
            pass  # Graceful fallback
```

### 4.4 Gate C 통과 조건

- [ ] HP `:8771/align` health 200
- [ ] 5분 sermon transcribe 시 `transcript.json` 과 `transcript.pre_align.json` 둘 다 존재
- [ ] aligned 의 word.start 가 pre_align 과 다름 (실제 align 됨)
- [ ] 임의 3 단어 sample 청취 검증 — mp3 재생 위치와 자막 단어 ±50ms 일치

---

## 5. Phase D — ffmpeg loudnorm + sidechaincompress (Auphonic 대체)

### 5.1 `app/render/audio_master.py` 신설

**Auphonic 우회 — 100% ffmpeg local. 외부 API 0.**

```python
"""Audio master via ffmpeg loudnorm + optional sidechain ducking.
Production-grade per EBU R128 / -16 LUFS YouTube spec.
"""
from __future__ import annotations
import subprocess, imageio_ffmpeg, json, re
from pathlib import Path

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

def measure_loudness(input_mp3: Path) -> dict:
    """Two-pass loudnorm — measure first."""
    r = subprocess.run([FFMPEG, "-i", str(input_mp3),
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=9:print_format=json",
        "-f", "null", "-"], capture_output=True, text=True)
    # Parse the JSON block from stderr
    m = re.search(r'\{[^{}]*"input_i"[^{}]*\}', r.stderr, re.DOTALL)
    return json.loads(m.group(0)) if m else {}


def master_audio(input_mp3: Path, output_mp3: Path, *,
                 target_lufs: float = -16.0, true_peak: float = -1.5,
                 lra: float = 9.0, music_bed_path: Path | None = None) -> bool:
    """Two-pass loudnorm. Optional sidechain ducking with music bed.
    
    Returns True on success, False on failure (caller falls back to original).
    """
    try:
        # Pass 1: measure
        m = measure_loudness(input_mp3)
        if not m:
            return False
        
        # Pass 2: apply with measured values
        cmd = [FFMPEG, "-y", "-i", str(input_mp3)]
        
        if music_bed_path and music_bed_path.exists():
            cmd += ["-i", str(music_bed_path),
                    "-filter_complex",
                    f"[1:a][0:a]sidechaincompress=threshold=0.05:ratio=8:attack=30:release=400[bed];"
                    f"[0:a][bed]amix=inputs=2:weights=1.0 0.4[mix];"
                    f"[mix]loudnorm=I={target_lufs}:TP={true_peak}:LRA={lra}:"
                    f"measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
                    f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:"
                    f"offset={m['target_offset']}:linear=true:print_format=summary[out]",
                    "-map", "[out]"]
        else:
            cmd += ["-af", f"loudnorm=I={target_lufs}:TP={true_peak}:LRA={lra}:"
                          f"measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
                          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:"
                          f"offset={m['target_offset']}:linear=true:print_format=summary"]
        
        cmd += ["-c:a", "libmp3lame", "-b:a", "192k", str(output_mp3)]
        
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if r.returncode != 0:
            return False
        
        # Verify output LUFS
        verify = measure_loudness(output_mp3)
        actual = float(verify.get("input_i", 0))
        if abs(actual - target_lufs) > 1.0:
            # Out of spec, abort
            return False
        return True
    except Exception:
        return False
```

### 5.2 `app/editor.py::export_audio()` 끝에 master 단계

```python
from app.render.audio_master import master_audio

# After existing export_audio render
mastered = out_path.with_stem(out_path.stem + "_master")
try:
    if master_audio(out_path, mastered):
        out_path.unlink()
        mastered.rename(out_path)
        print(f"[master] LUFS -16 applied to {out_path.name}")
except Exception:
    pass  # original mp3 그대로
```

### 5.3 Gate D 통과 조건

- [ ] 5분 sermon 1 클립 export → `ffmpeg -i out.mp3 -af loudnorm=print_format=json -f null /dev/null` 의 input_i ∈ [-16.5, -15.5]
- [ ] master 실패 시 원본 mp3 정상 export (graceful)
- [ ] sidechain music bed 옵션 working (테스트 시 pad/piano mp3 1개 임시 사용)

---

## 6. Phase E — 종합 검증 (Gate E — 최종)

### 6.1 v1 vs v2 mp4 2개 렌더

```bash
# 같은 클립 (5min sermon, 0-60s)
curl -s -X POST http://localhost:5001/api/job/20260428_233109_u7DodpeoTzg_audio/render \
  -H "Content-Type: application/json" \
  -d '{"clip":{"start_sec":0,"end_sec":60},"composition":"sermon_short_v1"}'
# render_id_v1 received → polling → mp4

curl -s -X POST http://localhost:5001/api/job/20260428_233109_u7DodpeoTzg_audio/render \
  -H "Content-Type: application/json" \
  -d '{"clip":{"start_sec":0,"end_sec":60},"composition":"sermon_short_v2"}'
# render_id_v2 → mp4
```

### 6.2 Frame 캡처 6개

```bash
SERMON_GD="/Users/hwasungkim/Library/CloudStorage/GoogleDrive-sharonkim71@gmail.com/내 드라이브/AI/교회 앱"
mkdir -p "$SERMON_GD/p7_compare"
for ts in 5 30 55; do
  for ver in v1 v2; do
    ssh quant@100.104.121.7 "ffmpeg -y -ss $ts -i /home/quant/hyperframes-render/output/${RID_$ver}.mp4 -frames:v 1 -update 1 /tmp/${ver}_${ts}s.png"
    scp -o BatchMode=yes quant@100.104.121.7:/tmp/${ver}_${ts}s.png "$SERMON_GD/p7_compare/"
  done
done
```

### 6.3 정량 측정

```bash
# LUFS 측정 (v2 mp4의 audio track)
ffmpeg -i v2.mp4 -af loudnorm=print_format=json -f null /dev/null 2>&1 | grep input_i

# 자막 sync 측정 (transcript.json vs render mp4 audio waveform 시작 시간)
python3 measure_sync.py v2.mp4 transcript.json   # 신규 헬퍼 — ±50ms 안 단어 비율
```

### 6.4 8개 quality criteria 측정

| 기준 | 측정 방법 | 통과 |
|---|---|---|
| Multi-scene visible | frame 6개에 다른 시각적 콘텐츠 | 5/6 ↑ |
| Shader transition | 9-13s 와 47-49s 사이 transition frame 비교 | 시각 확인 |
| 자막 stroke + 잘림 0 | 30s frame에 stroke visible + 자막 모두 보임 | binary |
| 골드 강조 sparingly | 자막 단어 중 emphasis 비율 < 25% | 측정 |
| 성구 카드 | 9-13s frame에 카드 + 명조 본문 | binary |
| Austerity moment | 50s frame 검은 화면 + 흰 명조 | binary |
| LUFS -16 ±0.5 | ffmpeg loudnorm measure | 정량 |
| Sync ±50ms | measure_sync.py | 정량 |

**목표**: 8 중 6 이상 → Gate E PASS → 5/10 → 8.5/10 도달.

### 6.5 사용자 보고

```markdown
## ✅ All-CLI 자율주행 완료 — 5/10 → ?/10
### 변경 7 파일 (line count delta)
- app/render/compositions/sermon_short_v2/{index.html, preview.html, README.md, DESIGN.md}
- app/render/payload.py (+build_short_payload_v2)
- app/render/audio_master.py (신규)
- app/server.py (+composition 분기)
- app/static/editor.html (+v1/v2 토글)
- app/pipeline.py (+WhisperX align)

### Gate 결과
| Gate | 결과 |
|---|---|
| A — composition v2 lint | ✅/❌ |
| B — payload + server 분기 | ✅/❌ |
| C — WhisperX align | ±NN ms |
| D — ffmpeg loudnorm | -NN.N LUFS |
| E — 종합 8 기준 | N/8 충족 |

### 시각 비교 frame
- p7_compare/v1_5s.png vs v2_5s.png (Hook scene)
- p7_compare/v1_30s.png vs v2_30s.png (Body scene)
- p7_compare/v1_55s.png vs v2_55s.png (Outro scene)

### Quality 자가 평가
- 5/10 → N/10 (사용자 검증 대기)

### 다음 Phase 권장
P5 (음악 베드 라이브러리 5곡 큐레이트) — 1.5일
or P4 (sermon_reel_v1) — 2일
```

---

## 7. 위험 + 대응

| 위험 | 대응 |
|---|---|
| Claude Code CLI HP에 미설치 | `curl -fsSL https://claude.ai/install.sh | sh` 자동 설치 후 진행 |
| `claude --skill hyperframes` 옵션 지원 안 됨 | fallback: interactive `claude` + `/hyperframes` slash 사용 (script + expect) |
| HF lint 0 erros 안 됨 | Claude Code 에 lint 에러 메시지 그대로 feed → 재시도 |
| WhisperX HP OOM | systemd Memory limit 설정 + Whisper turbo unload during align |
| ffmpeg loudnorm Pass2 실패 | Pass1만 적용 (빠르나 정확도 ↓), 또는 단순 -af loudnorm=I=-16 1-pass |
| HP `:8771` port 충돌 | `:8772` fallback, env 변수 |
| sermon_short_v2 가 v1 보다 quality 떨어짐 | Claude Code에 v1 frame + brief 차이 분석 instruct 후 재생성 |

---

## 8. 보고 프로토콜

각 Phase 종료 시:
- Gate 결과 + frame 캡처 GDrive 경로
- 변경 파일 line count
- 위험 발생 + 대응
- 다음 Phase 진입 준비

commit 메시지 prefix:
```
feat(A): sermon_short_v2 composition (Claude Code + HF Skills)
feat(B): payload v2 + composition 토글 + editor select
feat(C): WhisperX Korean align server :8771 + pipeline 통합
feat(D): ffmpeg loudnorm master_audio (Auphonic 우회)
feat(E): 종합 검증 — v1 vs v2 frame + LUFS + sync 측정
```

---

## 9. 환경

| 항목 | 값 |
|---|---|
| Mac sermon-app | `/Users/.../sermon-app` |
| HP hf-server | http://100.104.121.7:8770 |
| HP whisperx-server (신규) | http://100.104.121.7:8771 |
| HP whisper-turbo | http://100.104.121.7:8765 |
| HP ollama (Gemma 4) | http://100.104.121.7:11434 |
| Mac Tailscale | 100.89.99.106 |
| Gitea | http://100.116.4.84:3000/quant/sermon-app |
| Claude Code CLI | `~/strategies/...` 어디서든 |

---

## 10. 즉시 다음 액션 (자비스가 순서대로)

1. § 0 시작 절차 (5분)
2. § 2 Phase A — composition v2 생성 (1-2시간) → Gate A
3. § 3 Phase B — payload + server (45분) → Gate B
4. § 4 Phase C — WhisperX (1시간 + 모델 다운로드 시간) → Gate C
5. § 5 Phase D — ffmpeg loudnorm (30분) → Gate D
6. § 6 Phase E — 종합 검증 (1시간) → Gate E
7. § 8 commit + push + 사용자 보고

총 4-6시간. 사용자 manual 0.

---

## 변경 이력

| 버전 | 일자 | 변경 |
|---|---|---|
| v1.0 | 2026-05-03 | 최초 — Day 1+2+3 통합 + claude.ai/design 우회 + Auphonic 우회 |
