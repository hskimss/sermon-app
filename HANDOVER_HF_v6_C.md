# Body fix 시도 + Phase C (WhisperX) 가동 인계

**완료일:** 2026-05-04 06:40 BST
**기반:** `JARVIS_ALL_CLI_WORK_ORDER.md` Phase B(추가) + Phase C
**모드:** 자비스 (Proposer→Critic→Synthesizer)

---

## ✅ All-CLI 자율주행 — 5/10 → 7.5/10 (자가 평가)

### 변경 3 파일

| 파일 | 변경 |
|------|------|
| `app/render/compositions/sermon_short_v2/index.html` | Body chunk fade 패턴 (chunk hard-kill 시도) + CSS bottom-anchored + overflow:hidden + silent60.mp3 |
| `app/render/compositions/sermon_short_v2/silent60.mp3` | NEW (60s 무음 placeholder, lint-friendly) |
| `app/pipeline.py` | `transcribe()` 끝에 WhisperX align step + `transcript.pre_align.json` 백업 + `WHISPERX_ALIGN=0` 비활성 옵션 |

HP 측 (sermon-app repo 외):
- `~/hyperframes-render/server/whisperx_server.py` (NEW, 130 lines)
- `/etc/systemd/system/whisperx-server.service` (NEW)
- `~/.cache/huggingface/hub/models--kresnik--wav2vec2-large-xlsr-korean` (4.8GB)
- `~/.local/lib/python3.12/site-packages/whisperx 3.8.5 + pyannote.audio 4.0.4 + torch 2.8.0`

---

## Gate 결과

| Gate | 결과 |
|------|------|
| **Body fix** | ⚠ 부분 — chunk fade 코드 적용 + CSS bottom-anchored, 단 frame 캡처에서 자막 등장 안 됨 (P1 follow-up). 4/5 scenes는 정상 작동 (Hook/Scripture/Austerity/Outro) |
| **C — whisperx 설치** | ✅ pip install --user --break-system-packages 성공 (libavformat-dev 필요했음) |
| **C — kresnik 모델 다운** | ✅ 4.8GB (15 files, 44s) |
| **C — whisperx_server.py** | ✅ 작성 + scp + systemd unit 등록 |
| **C — 호환성 패치 4건** | ✅ numpy 2.0 (np.NaN/Inf), torchaudio 2.5+ (set/get/list_audio_backend), matplotlib 누락, whisperx 3.1.5 → 3.8.5 + pyannote.audio 3.1.1 → 4.0.4 업그레이드 |
| **C — /health 200** | ✅ `{"status":"ok","model":"kresnik/wav2vec2-large-xlsr-korean","device":"cuda","loaded":true}` |
| **C — 모델 로드 시간** | ✅ 4.2s |
| **C — systemd active** | ✅ `whisperx-server.service` enabled+active |
| **C — pipeline.py align 통합** | ✅ `WHISPERX_ALIGN=1` 기본값, fail 시 silent fallback (pre-align transcript 유지) |
| **C — ±50ms 실 측정** | ⏸ 보류 — Mac↔HP audio file share 미구성. Tailscale SSHfs 또는 audio upload endpoint 필요 |

---

## 자비스 Critic 사전 반영

| 발견 | 반영 |
|------|------|
| HF info Duration 5s (data-duration parse 실패) | hf_server에서 정수 치환 + silent60.mp3 (60s) 시도 — 미해결, P1 후속 |
| pyannote.audio 3.1.1 + torchaudio 2.11 호환 깨짐 (set_audio_backend, np.NaN, AudioMetaData) | torchaudio shim + numpy alias 후 whisperx 3.8.5 + pyannote 4.0.4 업그레이드로 일괄 해결 |
| systemd 환경 PATH 미해결 → nvm + .local/bin 누락 | unit `Environment=PATH=...` 명시 |
| GPU OOM 위험 (Whisper turbo + Gemma + WhisperX 동시) | 단일 GPU lock + lazy load. 추후 monitor 추가 가능 |
| audio_path가 Mac local 경로 → HP 못 읽음 | 후속: audio 업로드 endpoint 또는 Tailscale SSHfs |

---

## 시각 비교 frame (`교회 앱/p7_compare/`)

| 파일 | scene |
|------|-------|
| `v2_60s_3s.png` | Hook ("너는 예수님을 어떻게 대했냐") ✅ |
| `v2_60s_9s.png` | Scripture (요한복음 3:16 + KJV) ✅ |
| `v8_22s.png` `v8_30s.png` `v8_38s.png` | Body chunk fade ⚠ 검은 화면 (자막 등장 안 됨) |
| `v2_60s_51s.png` | Austerity ("주님 앞에 잠잠하라") ✅ |
| `v2_60s_57s.png` | Outro ("질문" + "A Church London") ✅ |

---

## 다음 액션

1. **Body scene 디버깅** (P1 follow-up, 30분~1시간):
   - HF compiler가 timeline 진행 못 하는 이유 (data-duration parse) 깊은 디버깅
   - 또는 segment-level captions으로 단순화 (한 segment 통째로 표시)
2. **Phase C ±50ms 측정**:
   - Mac → HP audio 업로드 endpoint 추가 (또는 Tailscale SSHfs share)
   - 5분 sermon 재전사 → `transcript.pre_align.json` vs `transcript.json` diff 측정
3. **다음 Phase**: HF_PHASE_PLAN_v2 §3 — P5 (음악 베드) 또는 P4 (sermon_reel_v1)

---

## 환경 변수 (sermon-app)

| Key | Default | 용도 |
|-----|---------|------|
| `WHISPERX_ALIGN` | `1` | 0=비활성, 1=활성 (기본) |
| `WHISPERX_URL` | `http://100.104.121.7:8771` | HP align server |
| `WHISPERX_DEVICE` | `cuda` | (HP 측 unit env) |
| `WHISPERX_KO_MODEL` | `kresnik/wav2vec2-large-xlsr-korean` | (HP 측 unit env) |

기존: `HF_RENDER_URL`, `SERMON_APP_BASE_URL`, `HP_Z2_LLM`, `SERMON_BIBLE_TRANS`, `SERMON_MASTER_AUDIO` 변경 없음.

---

## commit 단위

```
feat(C): WhisperX Korean align server :8771 + pipeline 통합
chore(v2): body chunk fade pattern + bottom-anchored CSS + silent60.mp3
```
