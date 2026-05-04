# sermon_reel_v1

2-3분 설교 요약 reel. 7 sub-comp, 180s, 1080×1920 (9:16).

## 사용법

```python
from app.render.payload import build_reel_payload_v1
from pathlib import Path

payload = build_reel_payload_v1(
    job_id="my_job",
    clip={"start_sec": 0.0, "end_sec": 180.0, "id": "my_job"},
    jobs_dir=Path("/tmp/sermon-app/jobs"),
)
payload["audio_url"] = "http://100.116.4.84:9876/my_audio.mp3"
# POST to http://192.168.1.111:8770/render
```

## Chapter 자동 분할
`app/render/reel_chapter.py` — Gemma 4 (gemma4:26b) 호출.
실패 시 균등 분할 fallback.

## 디렉토리
```
sermon_reel_v1/
  index.html              # root 180s
  hyperframes.json        # deps + template_vars defaults
  DESIGN.md
  README.md
  silent_180.mp3          # 180s silent placeholder
  compositions/
    intro.html            # 10s  — vendor: 01-problem-type
    chapter-1.html        # 40s  — vendor: 02-card-to-logo
    chapter-2.html        # 40s  — vendor: 04-benefits-flowchart
    highlight-quote.html  # 8s   — vendor: 03-brand-reveal
    chapter-3.html        # 40s  — vendor: 05-product-surfaces
    scripture-card.html   # 22s  — vendor: 06-wheel-pillars
    outro.html            # 20s  — vendor: 08-cta-outro
    components/           # v5/v6 공유 컴포넌트
```
