"""Subprocess worker that runs mlx_whisper.transcribe and prints PROGRESS lines parent can parse."""
import sys
import os
import json
from pathlib import Path

# Monkey-patch tqdm BEFORE importing mlx_whisper
import tqdm.std
_orig_update = tqdm.std.tqdm.update
_orig_init = tqdm.std.tqdm.__init__

def _patched_update(self, n=1):
    result = _orig_update(self, n)
    if getattr(self, "total", None):
        pct = (self.n / self.total) * 100 if self.total else 0
        print(f"PROGRESS:{pct:.1f}:{self.n}:{self.total}", flush=True)
    return result

tqdm.std.tqdm.update = _patched_update

# Now import and run
import imageio_ffmpeg
ROOT = Path(__file__).resolve().parent.parent if __name__ == "__main__" else Path.cwd()
ff = imageio_ffmpeg.get_ffmpeg_exe()
os.environ["PATH"] = str(Path(ff).parent) + os.pathsep + os.environ.get("PATH", "")

import mlx_whisper

src = sys.argv[1]
dst = sys.argv[2]
model = sys.argv[3] if len(sys.argv) > 3 else "mlx-community/whisper-large-v3-mlx"

print(f"START:{src}", flush=True)
result = mlx_whisper.transcribe(
    src,
    path_or_hf_repo=model,
    word_timestamps=True,
    language="ko",
    verbose=False,
)
segments = []
for seg in result.get("segments", []):
    words = []
    for w in (seg.get("words") or []):
        words.append({
            "word": w.get("word", ""),
            "start": round(w.get("start", 0), 2),
            "end": round(w.get("end", 0), 2),
            "probability": round(w.get("probability", 1.0), 4),
        })
    segments.append({
        "start": round(seg.get("start", 0), 2),
        "end": round(seg.get("end", 0), 2),
        "text": seg.get("text", "").strip(),
        "words": words,
    })
out = {
    "language": result.get("language", "ko"),
    "duration": 0,
    "segments": segments,
}
Path(dst).write_text(json.dumps(out, ensure_ascii=False, indent=2))
print(f"DONE:{len(segments)}", flush=True)
