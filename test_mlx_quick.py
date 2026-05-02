"""Quick mlx-whisper sanity test — 30s audio + tiny model."""
import os, sys, time, subprocess
from pathlib import Path
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parent
ff = imageio_ffmpeg.get_ffmpeg_exe()
ffmpeg_dir = str(Path(ff).parent)
os.environ["PATH"] = str(ROOT / ".venv" / "bin") + os.pathsep + ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

# Step 1: extract 30s clip with ffmpeg
src = sys.argv[1]
clip = "/tmp/_test_30s.mp4"
print(f"[1/3] Extracting 30s clip from {src}...", flush=True)
t = time.time()
subprocess.run([ff, "-y", "-ss", "0", "-t", "30", "-i", src, "-c", "copy", clip],
               check=True, capture_output=True)
print(f"  done {time.time()-t:.1f}s, size={Path(clip).stat().st_size/1024:.0f}KB", flush=True)

# Step 2: import + tiny model
print("[2/3] Loading mlx-whisper...", flush=True)
t = time.time()
import mlx_whisper
print(f"  done {time.time()-t:.1f}s", flush=True)

# Step 3: tiny model transcribe
print("[3/3] Transcribing with tiny model...", flush=True)
t = time.time()
result = mlx_whisper.transcribe(
    clip,
    path_or_hf_repo="mlx-community/whisper-tiny",
    word_timestamps=True,
    language="ko",
    verbose=False,
)
elapsed = time.time() - t
n = len(result.get("segments", []))
print(f"  done {elapsed:.1f}s — {n} segments", flush=True)
if n:
    print("  first text:", result["segments"][0].get("text", "")[:60])
print("OK")
