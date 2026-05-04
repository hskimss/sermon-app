# Remotion Pivot 작업지시서 — sermon_short_v2 마이그레이션

**작성:** 2026-05-04 (HF v0.4.42 5번 시도 실패 후 결정)
**위임:** 자비스 모드 또는 Claude Code 신규 세션
**예상 공수:** 1.5–2일
**최종 결과:** 동일 5-scene composition을 Remotion (React TSX) 으로 재구현, Body scene 정상 작동 보장

---

## 0. 전환 결정 근거

### HF v0.4.42 5번 시도 결과 (모두 부분 실패)

| 시도 | 패턴 | 결과 |
|------|------|------|
| 1 | chunk fade (6 word) + top:1080 | Body window 38s+ 만 등장 |
| 2 | bottom:380 + overflow:hidden | 동일 |
| 3 | position: fixed viewport | 동일 |
| 4 | `#root { position:relative; w:1080; h:1920 }` | 동일 |
| 5 | **segment-by-segment swap** (current) | 모든 frame 검은 화면 |

### 근본 원인 추정

- `npx hyperframes info compositions/sermon_short_v2` → `Duration 5.0s` (raw + 치환된 tmp 모두 동일)
- mp4는 60s 만들어지지만 HF compiler가 timeline duration을 5s로 인식
- frame 캡처 시 timeline.seek(t) 매핑이 무엇인지 불투명 (devtools 접근 어려움)
- **HF v0.4 멀티 scene + GSAP timeline 결합 시 progression broken** — public docs 부족

### Remotion 선택 이유

- React 컴포넌트 + 결정적 frame 함수 (`(frame, fps) => element`)
- composition.tsx 의 `durationInFrames` 명시 = 정확한 frame 매핑 보장
- 한국어 폰트, GSAP 스타일 애니메이션 모두 지원 (CSS transition + interpolate)
- HP에서 Lambda 또는 local render 가능
- HF 한계 우회 + 동일 design brief 만족

### 보존 원칙 — sermon-app 인터페이스 변경 금지

- `app/render/payload.py::build_short_payload_v2()` 출력 schema **그대로**
- `/api/job/<id>/render` endpoint 응답 schema **그대로**
- WhisperX align (`WHISPERX_ALIGN=1`), audio_master, scripture lookup **변경 0**
- editor.html v1/v2 select **그대로**
- v1 (sermon_short_v1.html) **그대로 유지** (HF + Studio 호환)

---

## 1. 환경 (Phase R0)

### Mac 측 — Remotion 프로젝트 생성

```bash
cd "/Users/hwasungkim/Library/CloudStorage/.../sermon-app/app/render"
npx create-video@latest remotion-v2 \
  --template blank --no-git --no-install
cd remotion-v2
npm install
# 한국어 폰트
npm install @remotion/google-fonts
```

### HP 측 — Remotion render 의존성

```bash
ssh quant@100.104.121.7
cd ~/hyperframes-render   # 기존 폴더 재사용
mkdir -p remotion-v2-server
cd remotion-v2-server
npm init -y
npm install --save-dev @remotion/cli @remotion/renderer
# Chromium 이미 설치됨 (HF 가 사용 중)
```

### 검증

```bash
# Mac
cd remotion-v2 && npx remotion preview src/Root.tsx
# 브라우저 http://localhost:3000 → blank composition 보임

# HP
npx remotion render --help | head -10
```

---

## 2. Phase R1 — Composition v2 재구현 (Remotion TSX)

### 2.1 src/SermonShortV2.tsx 구조

```tsx
import { AbsoluteFill, Audio, Sequence, useVideoConfig, useCurrentFrame,
         interpolate, spring } from 'remotion';

export const SermonShortV2: React.FC<{
  hookText: string;
  hookArchetype: string;
  austerityPhrase: string;
  segments: { start: number; end: number; text: string;
              words: { word: string; start: number; end: number; is_emphasis: boolean }[] }[];
  scriptureRefs: { book: string; chapter: number; verse_start: number;
                   verse_end?: number; text: string; translation: string;
                   appears_at_sec: number }[];
  audioUrl: string;
  musicBedUrl?: string;
  totalSec: number;
}> = (props) => {
  const { fps } = useVideoConfig();
  const HOOK_DUR = 6, SCRIPT_DUR = 8, AUSTERITY_DUR = 6, OUTRO_DUR = 6;
  const haveScripture = props.scriptureRefs.length > 0;
  // 시간축 동일 (HF 코드와 동일 계산)
  let t = 0;
  const T = { hook: { in: 0, out: HOOK_DUR } }; t = HOOK_DUR;
  if (haveScripture) { T.scripture = { in: t, out: t + SCRIPT_DUR }; t += SCRIPT_DUR; }
  T.body = { in: t, out: props.totalSec - AUSTERITY_DUR - OUTRO_DUR };
  t = props.totalSec - AUSTERITY_DUR - OUTRO_DUR;
  T.austerity = { in: t, out: t + AUSTERITY_DUR }; t += AUSTERITY_DUR;
  T.outro = { in: t, out: props.totalSec };

  return (
    <AbsoluteFill style={{ background: '#0E1116', overflow: 'hidden' }}>
      <Audio src={props.audioUrl} />
      {props.musicBedUrl ? <Audio src={props.musicBedUrl} volume={0.4} /> : null}

      <Sequence from={Math.round(T.hook.in * fps)} durationInFrames={Math.round((T.hook.out - T.hook.in) * fps)}>
        <HookScene text={props.hookText} />
      </Sequence>

      {haveScripture && (
        <Sequence from={Math.round(T.scripture.in * fps)} durationInFrames={Math.round(SCRIPT_DUR * fps)}>
          <ScriptureScene ref={props.scriptureRefs[0]} />
        </Sequence>
      )}

      {/* Body — segment-by-segment Sequence (hard ordering, overlap 0) */}
      {props.segments.map((s, i) => {
        const start = T.body.in + Math.max(0, s.start);
        const dur = Math.max(0.5, s.end - s.start);
        if (start >= T.body.out) return null;
        const safeDur = Math.min(dur, T.body.out - start);
        return (
          <Sequence key={i} from={Math.round(start * fps)}
                    durationInFrames={Math.round(safeDur * fps)}>
            <BodyLine seg={s} emphasisWords={collectEmphasisWords(props.segments)} />
          </Sequence>
        );
      })}

      <Sequence from={Math.round(T.austerity.in * fps)} durationInFrames={Math.round(AUSTERITY_DUR * fps)}>
        <AusterityScene phrase={props.austerityPhrase} />
      </Sequence>

      <Sequence from={Math.round(T.outro.in * fps)} durationInFrames={Math.round(OUTRO_DUR * fps)}>
        <OutroScene archetype={props.hookArchetype} />
      </Sequence>

      <ProgressBar totalSec={props.totalSec} />
    </AbsoluteFill>
  );
};
```

### 2.2 BodyLine.tsx — segment-by-segment swap

```tsx
const BodyLine: React.FC<{ seg: any; emphasisWords: Set<string> }> = ({ seg, emphasisWords }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const elapsed = frame / fps;
  // fade-in 0.4s, hold, fade-out 0.2s
  const dur = seg.end - seg.start;
  const opacity = elapsed < 0.4 ? interpolate(elapsed, [0, 0.4], [0, 1])
                : elapsed > dur - 0.2 ? interpolate(elapsed, [dur - 0.2, dur], [1, 0])
                : 1;
  return (
    <AbsoluteFill style={{
      top: '56%',         /* 1080/1920 = 56.25% — lower-third */
      height: '28%',      /* 540/1920 */
      paddingLeft: 64, paddingRight: 64,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      fontFamily: 'Pretendard Variable', fontWeight: 800,
      fontSize: 72, lineHeight: 1.32,
      wordBreak: 'keep-all', textAlign: 'center',
      color: '#FFFFFF',
      textShadow: '−3px −3px 0 #000, 3px −3px 0 #000, −3px 3px 0 #000, 3px 3px 0 #000, −3px 0 0 #000, 3px 0 0 #000, 0 −3px 0 #000, 0 3px 0 #000',
      opacity,
    }}>
      {renderEmphasis(seg.text, emphasisWords)}
    </AbsoluteFill>
  );
};

function renderEmphasis(text: string, emphasis: Set<string>) {
  return text.split(/(\s+)/).map((tok, i) => {
    const t = tok.trim();
    if (t && emphasis.has(t)) {
      return <span key={i} style={{ color: '#D4AF37' }}>{tok}</span>;
    }
    return <span key={i}>{tok}</span>;
  });
}
```

### 2.3 다른 4 scenes — interpolate 기반

(Hook / Scripture / Austerity / Outro — design brief §3.1–§3.5 그대로 React 로 변환)

### 2.4 src/Root.tsx 등록

```tsx
export const RemotionRoot: React.FC = () => (
  <Composition
    id="sermon_short_v2"
    component={SermonShortV2}
    durationInFrames={60 * 30}
    fps={30}
    width={1080}
    height={1920}
    defaultProps={...}  // local preview용
  />
);
```

---

## 3. Phase R2 — HP render server (port 8772)

### 3.1 server/remotion_server.py

기존 hf_server.py 패턴 그대로:
- `POST /render { composition, hook_text, ..., segments, scripture_refs }` → render_id
- `GET /render/<id>/status`
- `GET /output/<id>.mp4`

내부:
1. `_build_props_json()` — payload → Remotion `defaultProps` 형식
2. `subprocess npx remotion render src/Root.tsx sermon_short_v2 out.mp4 --props=props.json --concurrency 4`
3. audio mux (기존 동일)

### 3.2 systemd `remotion-server.service`

```ini
[Unit]
Description=Remotion sermon render server :8772
After=network.target

[Service]
User=quant
WorkingDirectory=/home/quant/hyperframes-render/remotion-v2-server
Environment=PATH=/home/quant/.nvm/versions/node/v22.22.2/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=/usr/bin/python3 /home/quant/hyperframes-render/server/remotion_server.py
Restart=on-failure
[Install]
WantedBy=multi-user.target
```

### 3.3 Mac 측 — `app/render/client.py` 보강

`HyperFramesClient.submit()` 가 `composition` parameter 따라 :8770 (HF) 또는 :8772 (Remotion) 자동 라우팅. 또는 `RemotionClient` 별도 + `composition_engine` 환경변수.

---

## 4. Phase R3 — sermon-app 통합 변경 최소

`app/render/client.py` (변경):
```python
HF_RENDER_URL = "http://100.104.121.7:8770"
REMOTION_RENDER_URL = "http://100.104.121.7:8772"

def pick_url(composition: str) -> str:
    if composition.endswith("_v2"):
        return REMOTION_RENDER_URL
    return HF_RENDER_URL
```

`app/server.py::api_render()` — composition 분기 그대로, client URL만 자동 선택. response schema 동일.

---

## 5. Gate (단계별 통과 기준)

| Gate | 조건 |
|------|------|
| **R0** | `npx remotion preview` 가 Mac 에서 blank composition render |
| **R1** | Mac preview 에서 60s sermon_short_v2 5 scenes 모두 시각 확인 + body 모든 시점 자막 표시 |
| **R2** | HP `:8772/health` 200 + `/render` POST 60s mp4 ≤ 30s 에 ready |
| **R3** | sermon-app `/api/job/<id>/render` (composition=v2) → Remotion mp4 받아옴, 회귀 v1 (HF) 정상 |
| **E** | 8 quality criteria 7/8 충족 (Body 정상 + 기존 6 + LUFS 또는 sync 중 1) |

---

## 6. 위험 + 대응

| 위험 | 대응 |
|------|------|
| Remotion render 시간 (60s mp4 = 30-60s 처리) | concurrency 4, GPU 인코딩 (h264_nvenc 외부 ffmpeg post-step) |
| Pretendard 폰트 webfont — Remotion build 시점 fetch 안 함 | `@remotion/google-fonts` 또는 `staticFile()` 로컬 ttf 번들 |
| WhisperX, scripture, emphasis 데이터 변형 안 함 보장 | client.py `pick_url` 만 변경, payload 그대로 forwarding |
| 기존 hf-server 충돌 | 같은 컴포지션 이름 v1 → :8770, v2 → :8772 라우팅 보장 |

---

## 7. 보존 항목 (Remotion pivot 후에도 변경 0)

- v1 sermon_short_v1.html (HF 그대로)
- WhisperX align infrastructure (:8771)
- audio_master.py / loudnorm
- scripture.py / lookup_verse / krv.json / kjv.json
- editor.html v1/v2 select (URL 자동 라우팅으로 unaware)
- payload schema (`build_short_payload_v2`)
- emphasis cache (`llm_emphasis.json`)

---

## 8. 즉시 다음 액션

1. `app/render/remotion-v2/` 디렉토리 생성 + `npx create-video@latest --template blank`
2. `src/SermonShortV2.tsx` + 5 scene 컴포넌트 작성
3. Mac local preview 확인 (Body 모든 시점 자막 visible)
4. HP `remotion-v2-server/` 동기화 + `:8772` server.py 작성
5. systemd unit 등록 + 8 quality criteria 측정
6. `app/render/client.py::pick_url()` 추가 후 회귀 테스트

---

## 9. 환경 변수

| Key | Default |
|-----|---------|
| `REMOTION_RENDER_URL` | `http://100.104.121.7:8772` |
| `HF_RENDER_URL` | `http://100.104.121.7:8770` (v1 fallback) |
| 기존 변수 | 변경 없음 |

---

## 변경 이력

| 버전 | 일자 | 변경 |
|------|------|------|
| v1.0 | 2026-05-04 | 최초 — HF 5번 실패 후 pivot 결정 |
