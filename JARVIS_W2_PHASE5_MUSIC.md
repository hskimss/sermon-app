# JARVIS_W2_PHASE5_MUSIC

작성: 2026-05-04 / 우선순위: P0 (A 첫 번째)
대상: linux-quant `claude` CLI (tmux: jarvis-w2)
모드: 선각자 (창작 0% / 1:1 모방 100%)
출력 규칙: 절대 최단 명령. thinking 5분 초과 시 step 분할.

---

## 0. 컨텍스트 (앞 단계 결과)

- v5_PADFIX.mp4 = 현재 production base. 사용자 OK 받음.
- audio (sermon 0-60s) + 자막 동기화 OK. 진짜 transcript words 적용됨.
- 이번 작업 = **음악 베드 5 mood 추가**로 톤 폭발적 향상.
- v6 또는 v5 위에 patch — 상위 호환 유지.

## 1. 통신 매핑 (외우지 말고 이거만 봄)

| 노드 | LAN | Tailscale | 진입 |
|---|---|---|---|
| linux-quant (자기) | 100.116.4.84 | — | (here) |
| HP-Z2-LLM render server :8770 | **192.168.1.111** | 100.104.121.7 (Tailscale auth 막힘) | `~/.ssh/id_ed25519` |
| Mac (sermon mp3 + jobs source) | — | 100.89.99.106 | `~/.ssh/id_ed25519` |

HP-Z2-LLM SSH (LAN으로):
```bash
ssh -i ~/.ssh/id_ed25519 quant@192.168.1.111
```

HP-Z2-LLM composition 자체 사본 위치:
```
/home/quant/hyperframes-render/compositions/sermon_short_v5/
```

Gitea repo: `ssh://git@localhost:2222/quant/sermon-app.git`

## 2. 산출물 (이거 정확히)

### 2.1 5 mood royalty-free mp3 (선각자 — 라이선스 검증된 곳에서)

위치: `/home/quant/sermon-app/app/render/music_beds/`

```
music_beds/
  ├── reverent.mp3      # 60s loop, 잔잔한 piano + sub bass
  ├── hope.mp3          # 60s, 부드러운 strings + light pad
  ├── conviction.mp3    # 60s, minor chord deep pad
  ├── joy.mp3           # 60s, 짧은 chime + warm pad
  └── silent.mp3        # 60s, ambient room tone (거의 무음)
```

각 mp3 사양: 44.1kHz / stereo / 96-128kbps / 60s+ seamless loop / Peak ≤ −18 dBFS

**선각자 모드 — 1:1 검증된 출처만**:
- HF student-kit assets/warm-pad.mp3 등 — student-kit/aisoc-* 의 audio assets 재활용 가능 시 우선 (Apache 2.0)
- pixabay.com/music — CC0 royalty-free
- bensound.com — CC BY 가능
- incompetech.com — Kevin MacLeod CC BY

검색 키워드: "ambient pad cinematic loop royalty-free 60 seconds"
**조건**: 라이선스 문서 첨부 가능한 것만. 의심나면 배제.

각 파일 다운로드 후 `ffmpeg`로 60s/96kbps/stereo로 재인코딩:
```bash
for src in <download>; do
  ffmpeg -y -i "$src" -t 60 -ar 44100 -ac 2 -c:a libmp3lame -b:a 96k music_beds/<mood>.mp3
done
```

ffmpeg `volumedetect` 으로 peak 검증 → −18 dBFS 초과 시 `volume=-3dB` 적용.

### 2.2 audio_master.py에 sidechain ducking 함수 추가

`/home/quant/sermon-app/app/render/audio_master.py`:

```python
def apply_music_bed(
    sermon_mp3: Path,
    mood: str,
    output: Path,
    music_beds_dir: Path = Path("app/render/music_beds"),
    duck_db: float = -12.0,
    target_lufs: float = -16.0,
) -> Path:
    """sermon vocal에 mood 배경음악 깔기 + sidechain ducking + LUFS -16 final.

    1. bed mp3를 -12dB로 attenuate
    2. sidechaincompress: vocal 있을 때 bed -12dB 추가 ducking
    3. amix
    4. loudnorm I=-16:LRA=11:TP=-1.5
    """
    bed = music_beds_dir / f"{mood}.mp3"
    if not bed.exists():
        raise FileNotFoundError(f"music bed: {bed}")
    cmd = [
        "ffmpeg", "-y",
        "-i", str(sermon_mp3),
        "-i", str(bed),
        "-filter_complex",
        f"[1:a]volume={duck_db}dB[bed_attn];"
        "[bed_attn][0:a]sidechaincompress=threshold=0.05:ratio=8:attack=20:release=200[bed_ducked];"
        "[0:a][bed_ducked]amix=inputs=2:duration=first:dropout_transition=0[mixed];"
        f"[mixed]loudnorm=I={target_lufs}:LRA=11:TP=-1.5",
        "-c:a", "libmp3lame", "-b:a", "192k",
        str(output),
    ]
    import subprocess
    subprocess.run(cmd, check=True, capture_output=True)
    return output
```

### 2.3 payload + music_bed_url 활용 검증

build_short_payload_v4 는 이미 `music_bed_url` 인자 받음. mood 선택 시 sermon-app server (또는 직접 이 스크립트)에서:

1. 사용자가 mood 선택 (예: "reverent")
2. server: `mixed_path = apply_music_bed(sermon_mp3, "reverent", output)` → mixed mp3 생성
3. mixed mp3를 :9876에 expose
4. payload audio_url = mixed mp3 URL

= server는 mood 변경 안하고 audio_url만 갈아끼우면 됨. 음악 베드는 audio mux 단계에서 합성.

### 2.4 5 mood × 동일 sermon clip → 5 mp4 비교

`/tmp/sermon-app/renders/v6_<mood>.mp4` 5개 출력.

```bash
SERMON=/tmp/sermon_real.mp3
CLIP_S=0; CLIP_E=60

for mood in reverent hope conviction joy silent; do
  # mix bed
  python3 -c "
from app.render.audio_master import apply_music_bed
from pathlib import Path
apply_music_bed(
  sermon_mp3=Path('/tmp/sermon-app/jobs/v4_test/trimmed_clip_0_60.mp3'),
  mood='$mood',
  output=Path('/tmp/sermon-app/renders/audio_$mood.mp3'),
)
"
  # render
  python3 -c "
import json, requests, time
p = json.load(open('/tmp/v5_payload.json'))
p['composition'] = 'sermon_short_v5'
p['audio_url'] = 'http://100.116.4.84:9876/audio_$mood.mp3'
p['music_bed_mood'] = '$mood'
r = requests.post('http://100.104.121.7:8770/render', json=p, timeout=30)
rid = r.json()['render_id']
for _ in range(40):
    time.sleep(3)
    s = requests.get(f'http://100.104.121.7:8770/render/{rid}/status').json()
    if s.get('status') == 'ready': break
import urllib.request as u
u.urlretrieve(f'http://100.104.121.7:8770/output/{rid}.mp4', '/tmp/sermon-app/renders/v6_$mood.mp4')
print('OK $mood')
"
done

ls -lh /tmp/sermon-app/renders/v6_*.mp4
```

먼저 sermon mp3 60s 클립 만들기:
```bash
ffmpeg -y -i /tmp/sermon_real.mp3 -ss 0 -t 60 -c:a libmp3lame -b:a 96k /tmp/sermon-app/jobs/v4_test/trimmed_clip_0_60.mp3
```

## 3. 6 step 작업

### Step 1 — sermon-app pull + music_beds/ 디렉토리 준비

```bash
cd /home/quant/sermon-app && git pull origin main
mkdir -p app/render/music_beds
```

### Step 2 — 5 mood mp3 다운로드 (선각자 — 라이선스 검증)

자동화 안 되면 (라이선스 동의 필요한 사이트는 skip), 다음 우선순위:

1. student-kit/aisoc-app-release/assets/* 또는 다른 student-kit 프로젝트의 audio asset 재활용 (Apache 2.0)
2. Kevin MacLeod incompetech (CC BY) — wget 가능한 직접 mp3 link
3. pixabay.com/music — robots/API 검토

대안: 자체 합성 (5 분 안). Tone.js/Sox로 simple ambient pad 5종 generation. 단, 사용자에게 "임시 자체 합성" 명시.

Sox로 quick 5 mood (FALLBACK ONLY):
```bash
# reverent — slow C# minor sine + low pad
sox -n music_beds/reverent.mp3 synth 60 sine 138.6 sine 277.2 sine 415.3 vol 0.15 reverb 50
# hope — major C + G triad
sox -n music_beds/hope.mp3 synth 60 sine 261.6 sine 392.0 sine 523.3 vol 0.18 reverb 40
# conviction — minor pad with sub
sox -n music_beds/conviction.mp3 synth 60 sine 130.8 sine 196.0 sine 311.1 vol 0.16 reverb 60
# joy — bell triad
sox -n music_beds/joy.mp3 synth 60 sine 392.0 sine 523.3 sine 659.3 vol 0.17 reverb 35
# silent — pink noise -40dB
sox -n music_beds/silent.mp3 synth 60 pinknoise vol 0.02
```
(Sox 결과 후 mp3 재인코딩 ffmpeg `-c:a libmp3lame -b:a 96k`)

검증:
```bash
for f in app/render/music_beds/*.mp3; do
  echo "=== $f ==="
  ffmpeg -i "$f" -af volumedetect -vn -f null - 2>&1 | grep -E "Duration|mean|max"
done
```

### Step 3 — audio_master.py 패치

위 2.2의 `apply_music_bed` 함수 추가. `_audio_master_test.py` 같은 pytest 파일 1개만 작성:

```python
from app.render.audio_master import apply_music_bed
from pathlib import Path

def test_reverent():
    out = apply_music_bed(
        Path("/tmp/sermon-app/jobs/v4_test/trimmed_clip_0_60.mp3"),
        "reverent",
        Path("/tmp/test_reverent.mp3"),
    )
    assert out.exists()
    # ffmpeg loudnorm 결과 LUFS -16 ±1 검증
```

### Step 4 — sermon mp3 clip + 5 mood mix

위 2.4 스크립트 그대로.

### Step 5 — 5 mp4 출력 + git commit

```bash
git add -A
git -c user.email=jacob.kim@achurch.net -c user.name=jacob commit -m "feat(w2): Phase 5 음악 베드 5 mood + sidechain ducking"
git push origin main
```

### Step 6 — HANDOVER 작성 + 사용자 보고

`~/sermon-app/HANDOVER_W2_phase5.md`:

```markdown
# W2 Phase 5 — Music Beds Complete

## 5 mood mp3 (출처 명시)
| mood | source | license | size | mean dBFS |
|---|---|---|---|---|
| reverent | <URL> | <CC0/CC BY/Apache> | <X>KB | <Y> |
| hope | ... | ... | ... | ... |
| conviction | ... | ... | ... | ... |
| joy | ... | ... | ... | ... |
| silent | sox-generated pinknoise | self | ... | ... |

## 5 mp4 비교 URL
- http://100.116.4.84:9876/v6_reverent.mp4
- http://100.116.4.84:9876/v6_hope.mp4
- http://100.116.4.84:9876/v6_conviction.mp4
- http://100.116.4.84:9876/v6_joy.mp4
- http://100.116.4.84:9876/v6_silent.mp4

## 검증 결과
- LUFS −16 ±1: 5/5 PASS / FAIL
- vocal sidechain ducking 작동: ✅/❌
- bed peak ≤ −18 dBFS: ✅/❌

## git
<commit hash>

## 다음
사용자 5 mp4 시청 → mood 1-2개 OK 판정 → C 단계 (디테일) 진입.
```

## 4. 정책 (절대 위반 금지)

1. **선각자 모드 강제** — 라이선스 검증 안 된 음악 절대 다운로드 금지. 의심나면 sox 자체 합성.
2. **v5 회귀 금지** — sermon_short_v5 composition 손대지 말 것. audio mux 단계만 변경.
3. **HP-Z2-LLM 통신** — Tailscale 100.104.121.7 SSH 시도 금지. 무조건 LAN 192.168.1.111.
4. **render server 응답 audio_mux_warning** 발생 시 audio_url 도달 가능성 먼저 확인 (curl :9876).
5. **검증 실패 시** — 추가 패치 시도 금지. HANDOVER에 정확히 어디서 막혔는지 1줄로 보고.

## 5. 시작

`/tmp/sermon-app` 에서 git pull origin main 후 6 step 정확히 실행. 완료시 HANDOVER_W2_phase5.md 작성하고 종료.
