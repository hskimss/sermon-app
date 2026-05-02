import os, sys, time
from pathlib import Path
import imageio_ffmpeg
ff = imageio_ffmpeg.get_ffmpeg_exe()
ROOT = Path(__file__).resolve().parent
os.environ["PATH"] = str(ROOT / ".venv" / "bin") + os.pathsep + os.environ.get("PATH", "")

import mlx_whisper
src = sys.argv[1]
print(f"Starting transcribe of {src}...", flush=True)
t0 = time.time()
result = mlx_whisper.transcribe(src, path_or_hf_repo="mlx-community/whisper-large-v3-mlx",
                                 word_timestamps=True, language="ko", verbose=True)
elapsed = time.time() - t0
n = len(result.get("segments", []))
print(f"\nDone in {elapsed:.1f}s — {n} segments")
if n:
    print("First:", result["segments"][0].get("text", "")[:80])
