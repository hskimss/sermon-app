import os, sys, time
from pathlib import Path
import imageio_ffmpeg
ROOT = Path(__file__).resolve().parent
ff = imageio_ffmpeg.get_ffmpeg_exe()
os.environ["PATH"] = str(ROOT / ".venv" / "bin") + os.pathsep + str(Path(ff).parent) + os.pathsep + os.environ.get("PATH", "")
import mlx_whisper
src = sys.argv[1]
print(f"transcribe {src} ...", flush=True)
t = time.time()
result = mlx_whisper.transcribe(src, path_or_hf_repo="mlx-community/whisper-large-v3-mlx",
                                 word_timestamps=True, language="ko", verbose=False)
print(f"done {time.time()-t:.1f}s — {len(result.get(\"segments\",[]))} segs")
import json
with open(sys.argv[2], "w") as f:
    json.dump({"language": result.get("language","ko"), "duration": 0,
               "segments": [{"start": round(s.get("start",0),2), "end": round(s.get("end",0),2),
                            "text": s.get("text","").strip(),
                            "words": [{"word": w.get("word",""), "start": round(w.get("start",0),2),
                                       "end": round(w.get("end",0),2),
                                       "probability": round(w.get("probability",1),4)}
                                      for w in s.get("words",[]) or []]} for s in result.get("segments",[])]},
              f, ensure_ascii=False, indent=2)
print("saved", sys.argv[2])
