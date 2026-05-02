import os, sys, time, json
from pathlib import Path
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parent
ff = imageio_ffmpeg.get_ffmpeg_exe()
os.environ["PATH"] = str(ROOT / ".venv" / "bin") + os.pathsep + str(Path(ff).parent) + os.pathsep + os.environ.get("PATH", "")

import mlx_whisper

src = sys.argv[1]
out = sys.argv[2]
print("transcribe " + src + " ...", flush=True)
t = time.time()
result = mlx_whisper.transcribe(
    src,
    path_or_hf_repo="mlx-community/whisper-large-v3-mlx",
    word_timestamps=True,
    language="ko",
    verbose=False,
)
elapsed = time.time() - t
n = len(result.get("segments", []))
print("done {:.1f}s segs={}".format(elapsed, n), flush=True)

segs_out = []
for s in result.get("segments", []):
    words = []
    for w in (s.get("words") or []):
        words.append({
            "word": w.get("word", ""),
            "start": round(w.get("start", 0), 2),
            "end": round(w.get("end", 0), 2),
            "probability": round(w.get("probability", 1), 4),
        })
    segs_out.append({
        "start": round(s.get("start", 0), 2),
        "end": round(s.get("end", 0), 2),
        "text": s.get("text", "").strip(),
        "words": words,
    })

with open(out, "w", encoding="utf-8") as f:
    json.dump({"language": result.get("language", "ko"), "duration": 0, "segments": segs_out}, f, ensure_ascii=False, indent=2)

print("saved " + out)
