# Day 2+3 자비스 작업지시서 — composition v2 통합 + WhisperX + Auphonic

> 위임 대상: Claude Code (jarvis 모드, sermon-app 세션)
> 자체 완결 — 본 문서 + 사용자가 받아온 Claude Design ZIP 만으로 진행
> 예상 공수: **2일** (composition v2 wiring 0.5일 + WhisperX 0.5일 + Auphonic 0.5일 + 검증 0.5일)
> 결과: 5/10 → 8.5/10 도달 측정 가능

---

## 0. 시작 절차 (필수)

```bash
cd "/Users/hwasungkim/Library/CloudStorage/GoogleDrive-sharonkim71@gmail.com/내 드라이브/AI/교회 앱/sermon-app"

# 사용자가 미리 준비한 것 확인
ls app/render/compositions/sermon_short_v2/   # ZIP 풀어 놓은 폴더 — index.html, preview.html, README.md, DESIGN.md
ls -la /tmp/auphonic_credentials.json 2>/dev/null  # 사용자가 가입했으면 있음
ls /tmp/whisperx_test_audio.mp3 2>/dev/null         # 5분 테스트 audio (이미 있음)

# 정독
cat GIANT_MODE_v2_RESEARCH.md     # Tier 1 stack 정의
cat HF_PHASE_PLAN_v2.md            # P3 ~ P8 계획
cat HANDOVER_HF_v4_P6.md           # P6 결과
```

**중단 조건**:
- `app/render/compositions/sermon_short_v2/` 폴더가 없거나 `index.html` 누락 → 사용자에 ZIP 받았는지 확인 후 중단
- HP `:8770` `/health` ok=false → systemd hf-server 점검
- WhisperX import 실패 → pip 설치 단계 추가 (env 제약 보고)

---

## 1. Day 2 — composition v2 통합

### 1.1 sermon-app 측 — payload 빌더 v2 분기

새 함수 `app/render/payload.py::build_short_payload_v2(job_id, clip, jobs_dir)`:

기존 `build_short_payload` 와 거의 동일하되 추가 inject keys:

```python
{
  "composition": "sermon_short_v2",
  "audio_url": ...,
  "audio_clip": ...,
  "hook_text": clip.get("hook_text") or words[0:6 단어 join],
  "hook_archetype": clip.get("hook_archetype") or "질문",
  "words": [...],  # 기존
  "scripture_refs": [...],  # 기존 lookup=True 적용
  "austerity_phrase": clip.get("austerity_phrase") or "주님 앞에 잠잠하라",
  "house_style": "a_church_london_v1",
  "format": "9:16",
  "quality": "1080p",
}
```

### 1.2 HP hf-server — composition v2 등록

```bash
ssh quant@100.104.121.7
ls /home/quant/hyperframes-render/compositions/   # sermon_short_v1.html 옆에 v2 디렉토리/파일
```

ZIP을 사용자가 풀어놓은 v2 디렉토리 전체를 HP로 sync:
```bash
rsync -av "$SERMON/app/render/compositions/sermon_short_v2/" \
  quant@100.104.121.7:/home/quant/hyperframes-render/compositions/sermon_short_v2/
```

`hf_server.py` 의 `composition_lookup` 에 `sermon_short_v2` 추가 (이미 자동 detect 라면 skip).

### 1.3 server.py — 렌더 endpoint 옵션 추가

`/api/job/<id>/render` POST body 에 `composition` 키 받아서 v1/v2 분기:
```python
comp_id = body.get("composition", "sermon_short_v1")
if comp_id == "sermon_short_v2":
    payload = build_short_payload_v2(job_id, clip, jobs_dir)
else:
    payload = build_short_payload(job_id, clip, jobs_dir)
```

### 1.4 editor.html — v1/v2 토글

기존 `[ ] HF 시각화` 옆에 작은 select:
```html
<label>composition: 
  <select id="hf-comp-select">
    <option value="sermon_short_v1">v1 (단순)</option>
    <option value="sermon_short_v2" selected>v2 (multi-scene)</option>
  </select>
</label>
```

P6 IIFE 의 `doHFBulkExport()` 호출 시 `composition` 필드 포함.

### 1.5 검증 (Gate A)

- [ ] 5분 테스트 sermon `20260428_233109_u7DodpeoTzg_audio` 으로 첫 클립 v2 렌더 성공
- [ ] frame 캡처 5개 시점 (1s / 9s / 25s / 50s / 58s) — 각 scene 검증
- [ ] 자막 잘림 없음 (safe-bottom 270px 존중)
- [ ] 골드 강조 단어 visible
- [ ] 성구 카드 (있으면) scene 2에 등장
- [ ] austerity scene 4 검은 화면 + 흰 명조 + silence
- [ ] outro scene 5 brand mark visible

---

## 2. Day 2 — WhisperX Korean align 통합

### 2.1 HP 서버 측 — WhisperX 설치

```bash
ssh quant@100.104.121.7
pip3 install whisperx --user --break-system-packages 2>&1 | tail -5

# 한국어 wav2vec2 모델 사전 다운로드 (~1GB)
python3 -c "
from huggingface_hub import snapshot_download
snapshot_download('kresnik/wav2vec2-large-xlsr-korean')
print('OK')
"
```

### 2.2 hf-server 옆에 whisperx-server 신설

`/home/quant/hyperframes-render/server/whisperx_server.py` (port :8771):

```python
"""WhisperX align server — receives mp3 + initial transcript JSON,
returns aligned transcript JSON with ±50ms word timestamps.

POST /align
  body: {"audio_path": "/tmp/x.mp3", "transcript": {...whisper output...}}
  response: aligned transcript with words[].start/end ±50ms accuracy
"""
import whisperx, json, threading
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 8771
DEVICE = "cuda"
MODEL_KO = "kresnik/wav2vec2-large-xlsr-korean"

# 모델 1회 로드
print("Loading WhisperX align model (Korean wav2vec2)...", flush=True)
align_model, metadata = whisperx.load_align_model(language_code="ko", device=DEVICE)
print("OK", flush=True)

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/align":
            self._send(404, {"error": "not found"}); return
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        audio_path = body["audio_path"]
        transcript = body["transcript"]
        # Convert sermon-app transcript → WhisperX expected format
        segments = [{"start": s["start"], "end": s["end"], "text": s["text"]}
                    for s in transcript.get("segments", [])]
        result = whisperx.align(segments, align_model, metadata, audio_path, DEVICE,
                                return_char_alignments=False)
        # Convert back to sermon-app format
        out = {
            "language": "ko",
            "segments": [
                {"start": s["start"], "end": s["end"], "text": s["text"],
                 "words": [
                    {"word": w["word"], "start": w["start"], "end": w["end"],
                     "probability": w.get("score", 1.0)}
                    for w in (s.get("words") or [])
                 ]}
                for s in result["segments"]
            ]
        }
        self._send(200, out)
    
    def _send(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code); self.send_header("Content-Length", len(body))
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers(); self.wfile.write(body)
    
    def log_message(self, *args): pass

if __name__ == "__main__":
    print(f"WhisperX align server: http://0.0.0.0:{PORT}/align", flush=True)
    HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
```

systemd unit `whisperx-server.service` 생성 (hf-server 패턴 그대로). Start + enable.

### 2.3 sermon-app 파이프라인 통합

`app/pipeline.py` `transcribe()` 함수 끝에 align 옵션:

```python
def transcribe(src, dst, model_size, job_id=None, align=True):
    # ... 기존 mlx-whisper 또는 HP whisper-turbo 호출 ...
    initial = json.loads(dst.read_text())
    
    if align and os.getenv("WHISPERX_ALIGN", "1") == "1":
        try:
            r = requests.post("http://100.104.121.7:8771/align",
                json={"audio_path": str(src), "transcript": initial},
                timeout=180)
            if r.status_code == 200:
                aligned = r.json()
                # Backup old, write aligned
                dst.with_suffix(".pre_align.json").write_text(initial_text)
                dst.write_text(json.dumps(aligned, ensure_ascii=False, indent=2))
                _update_phase(job_id, "transcribing", aligned=True)
        except Exception as e:
            # WhisperX 실패하면 원본 그대로 — fallback graceful
            pass
```

### 2.4 검증 (Gate B)

- [ ] 5분 테스트 sermon 다시 transcribe → `transcript.json` `transcript.pre_align.json` 두 개 존재
- [ ] aligned 의 word timestamps 가 pre_align 보다 다름 (실제로 align 됨)
- [ ] 사람 청취 검증 — 자막 sync 가 mp3 재생과 ±50ms 안 일치 (3개 단어 random check)
- [ ] HP nvidia-smi 에서 align 진행 시 wav2vec2 GPU 사용 확인

---

## 3. Day 3 — Auphonic 음성 마스터링

### 3.1 사용자가 미리 가입 + API key 발급

사용자에게 요청:
1. https://auphonic.com 가입 ($11/월 Standard plan, 1시간 audio/month)
2. https://auphonic.com/account/integrations 에서 API token 발급
3. API token을 `/Users/hwasungkim/.config/sermon-app/auphonic.json` 에 저장:
   ```json
   {"api_token": "YOUR_TOKEN_HERE"}
   ```

토큰 없으면 Gate C skip + 스크립트만 작성 (사용자가 받아오면 활성화).

### 3.2 auphonic preset 설정

Auphonic 웹 UI 에서 sermon preset 1개 생성:
- Loudness target: -16 LUFS
- True peak: -1.5 dBTP
- Hum reduction: ON
- Noise reduction: medium
- Filtering: leveler ON
- Silence cutting: OFF (sermon은 의도적 silence 보존)

preset UUID 받아서 `app/render/audio_master.py` 에 hardcode.

### 3.3 sermon-app — master_audio skill

`app/render/audio_master.py`:
```python
def master_audio(input_mp3: Path, output_mp3: Path, preset_uuid: str = SERMON_PRESET) -> bool:
    """Send mp3 to Auphonic, wait for completion, download mastered version."""
    api_token = json.loads(Path("~/.config/sermon-app/auphonic.json").expanduser().read_text())["api_token"]
    headers = {"Authorization": f"Bearer {api_token}"}
    
    # 1. Create production
    r = requests.post("https://auphonic.com/api/productions.json",
        headers=headers,
        data={"preset": preset_uuid})
    prod_uuid = r.json()["data"]["uuid"]
    
    # 2. Upload mp3
    with input_mp3.open("rb") as f:
        requests.post(f"https://auphonic.com/api/production/{prod_uuid}/upload.json",
            headers=headers, files={"input_file": f})
    
    # 3. Start
    requests.post(f"https://auphonic.com/api/production/{prod_uuid}/start.json", headers=headers)
    
    # 4. Poll until done
    while True:
        s = requests.get(f"https://auphonic.com/api/production/{prod_uuid}.json", headers=headers).json()
        if s["data"]["status"] == 3:  # Done
            break
        time.sleep(5)
    
    # 5. Download
    out_url = s["data"]["output_files"][0]["download_url"]
    output_mp3.write_bytes(requests.get(out_url, headers=headers).content)
    return True
```

### 3.4 export_audio 단계에 master 통합

`app/editor.py::export_audio()` 마지막에:
```python
mastered_path = out_path.with_stem(out_path.stem + "_master")
try:
    if master_audio(out_path, mastered_path):
        out_path.unlink()
    mastered_path.rename(out_path)  # Replace with mastered version
except Exception:
    pass  # Fail silently, original mp3 그대로
```

### 3.5 검증 (Gate C)

- [ ] 5분 테스트 sermon 1 클립 export → audio LUFS 측정 (`ffmpeg -i out.mp3 -af loudnorm=print_format=json -f null /dev/null` 의 input_i 가 -16 ±0.5)
- [ ] 사람 청취 — 음량 평탄, hum 없음
- [ ] master 단계 실패 시 원본 mp3 정상 export (graceful fallback)

---

## 4. 종합 검증 (Gate D — 가장 중요)

### 4.1 v1 vs v2 quality 비교 mp4 2개

같은 clip (5분 테스트 sermon 의 첫 60초) 으로:
- `composition: sermon_short_v1` 렌더 → `compare_v1.mp4`
- `composition: sermon_short_v2` 렌더 → `compare_v2.mp4`
- WhisperX align 적용된 transcript 사용
- Auphonic master 적용된 audio 사용

### 4.2 frame 캡처 + 사용자 검증

`/tmp/p7_compare/` 에:
- `v1_5s.png` `v1_30s.png` `v1_55s.png`
- `v2_5s.png` `v2_30s.png` `v2_55s.png`

Mac 의 GDrive 폴더로 복사 → 사용자가 직접 열어서 비교.

### 4.3 quality score 자가 평가

이전 5/10 = single scene + 자막 only + LUFS 평탄 안 됨 + 자막 sync ±200ms.

목표 8.5/10 충족 조건:
- [ ] multi-scene (5 scenes 모두 visible)
- [ ] shader transition 2개 작동
- [ ] 자막 stroke + 잘림 없음
- [ ] 골드 강조 sparingly (3-5 단어 중 1)
- [ ] 성구 카드 fade + ESV/Crossway 활자 무게
- [ ] austerity moment 검은 화면 + silence
- [ ] LUFS -16 ±0.5
- [ ] 자막 sync ±50ms

8개 중 6개 이상 충족 → Gate D PASS.

---

## 5. 보고 + 커밋

### 5.1 HANDOVER_v5_DayN.md 작성

각 Day 별 산출:
- Day 2: composition v2 통합 + WhisperX → `HANDOVER_v5_Day2.md`
- Day 3: Auphonic + 종합 검증 → `HANDOVER_v5_Day3.md`

각 문서:
- 변경 파일 line count delta
- Gate 결과 + frame 경로
- 위험 + 대응
- 다음 Phase 진입 권장

### 5.2 git commit 단위

```
feat(day2-1): sermon_short_v2 composition wiring
feat(day2-2): WhisperX Korean align integration (whisperx-server :8771)
feat(day3-1): Auphonic audio mastering (master_audio skill)
feat(day3-2): 종합 검증 — compare_v1/v2 mp4 + LUFS + sync 측정
```

### 5.3 사용자 보고 메시지 형식

```
## ✅ Day N 완료
### Gate 결과
| 항목 | 결과 |
|---|---|
| ... | ✅/❌ ... |

### 시각/청각 검증 frame
- compare_v1.mp4 vs compare_v2.mp4 (Mac GDrive)
- LUFS 측정값
- sync 측정값

### 다음 Phase 진입 권장
...
```

---

## 6. 위험 + 대응

| 위험 | 대응 |
|---|---|
| Claude Design ZIP의 inject point 가 본 contract 와 다름 | DESIGN.md 읽고 매핑 layer 작성. 차이 크면 사용자에 보고 + 추가 brief |
| WhisperX HP 메모리 OOM (Whisper turbo + Gemma + WhisperX 동시) | systemd 우선순위 조정 (Whisper 끈 후 align, 또는 align 시 Gemma 일시 unload) |
| Auphonic API token 미발급 | Day 3 skip + 사용자에 가입 요청 + 스크립트만 작성 후 대기 |
| v2 composition 이 v1 보다 quality 떨어짐 | 사용자에 즉시 보고 + Claude Design 에 추가 brief 요청 |
| HF lint 실패 | Claude Design ZIP 의 README.md 따라 수정 + 사용자 보고 |

---

## 7. 환경 (변동 없음)

| 항목 | 값 |
|---|---|
| Mac sermon-app | `/Users/hwasungkim/Library/CloudStorage/GoogleDrive-sharonkim71@gmail.com/내 드라이브/AI/교회 앱/sermon-app` |
| HP hf-server | http://100.104.121.7:8770 |
| HP whisperx-server (신규) | http://100.104.121.7:8771 |
| HP whisper-turbo | http://100.104.121.7:8765 |
| Gemma 4 + bge-m3 | http://100.104.121.7:11434 |
| Gitea | http://100.116.4.84:3000/quant/sermon-app |
| Mac Tailscale | 100.89.99.106 |

---

## 8. 즉시 다음 액션

1. **사용자가 Claude Design ZIP 받음 → `app/render/compositions/sermon_short_v2/` 에 풀어둠**
2. **사용자가 Auphonic 가입 + API token 저장** (Day 3 위함)
3. § 0 시작 절차 실행 → ZIP 존재 확인
4. § 1.1 ~ 1.5 composition v2 wiring (Gate A)
5. § 2.1 ~ 2.4 WhisperX 통합 (Gate B)
6. § 3.1 ~ 3.5 Auphonic 통합 (Gate C, token 있을 때만)
7. § 4 종합 검증 (Gate D)
8. § 5 commit + HANDOVER + 사용자 보고

---

## 변경 이력

| 버전 | 일자 | 변경 |
|---|---|---|
| v1.0 | 2026-05-03 | 최초 — GIANT_MODE_v2 Tier 1 stack 기반 |
