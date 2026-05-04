from __future__ import annotations
"""파이프라인 — yt-dlp → ffmpeg trim → mlx-whisper (inline + progress thread) → done."""
import imageio_ffmpeg
_FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
import os as _os
from pathlib import Path as _PathTmp
_os.environ["PATH"] = str(_PathTmp(__file__).resolve().parent.parent / ".venv" / "bin") + _os.pathsep + str(_PathTmp(_FFMPEG).parent) + _os.pathsep + _os.environ.get("PATH", "")

import json
import re
import subprocess
import threading
import time
from pathlib import Path
from app.jobs import JOBS_DIR


def _update_phase(job_id: str, phase: str, **extra) -> None:
    p = JOBS_DIR / job_id / "meta.json"
    meta = json.loads(p.read_text())
    meta["phase"] = phase
    for k, v in extra.items():
        meta[k] = v
    p.write_text(json.dumps(meta, ensure_ascii=False, indent=2))


def download_youtube(youtube_url: str, out_path: Path, audio_only: bool = False) -> None:
    if out_path.exists() and out_path.stat().st_size > 0:
        return
    yt = str(Path(__file__).resolve().parent.parent / ".venv" / "bin" / "yt-dlp")
    audio_args = ["-x", "--audio-format", "mp3", "--audio-quality", "0"] if audio_only else []
    strategies = [
        [yt] + audio_args + ["--extractor-args", "youtube:player_client=android", "-o", str(out_path), youtube_url],
        [yt] + audio_args + ["--cookies-from-browser", "chrome", "-o", str(out_path), youtube_url],
        [yt] + audio_args + ["--extractor-args", "youtube:player_client=tv_simply", "-o", str(out_path), youtube_url],
        [yt] + audio_args + ["--extractor-args", "youtube:player_client=web", "-o", str(out_path), youtube_url],
    ]
    last_err = None
    for cmd in strategies:
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=600)
            return
        except subprocess.CalledProcessError as e:
            last_err = e
            continue
    if last_err:
        raise last_err


def trim_video(src: Path, dst: Path, start_sec: int, end_sec: int, audio_only: bool = False) -> None:
    if dst.exists() and dst.stat().st_size > 0:
        return
    duration = end_sec - start_sec
    if audio_only:
        cmd = [_FFMPEG, "-y", "-ss", str(start_sec), "-i", str(src),
               "-t", str(duration), "-vn", "-c:a", "copy", str(dst)]
    else:
        cmd = [_FFMPEG, "-y", "-ss", str(start_sec), "-i", str(src),
               "-t", str(duration), "-c", "copy", str(dst)]
    subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)


def _probe_duration_sec(src: Path) -> float:
    try:
        r = subprocess.run([_FFMPEG, "-i", str(src), "-f", "null", "-"],
                           capture_output=True, text=True, timeout=30)
        m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", r.stderr)
        if m:
            h, mm, ss = m.groups()
            return int(h) * 3600 + int(mm) * 60 + float(ss)
    except Exception:
        pass
    return 0.0


def transcribe(src: Path, dst: Path, model_size: str = "mlx-community/whisper-large-v3-mlx", job_id: str = None) -> None:
    """Inline mlx-whisper. Background thread reports elapsed + estimated remaining every 2s."""
    if dst.exists() and dst.stat().st_size > 0:
        return
    
    audio_dur_sec = _probe_duration_sec(src)
    # M-series Mac large-v3 ~ 1.25x realtime
    estimated_total_sec = max(60.0, audio_dur_sec * 1.25)
    
    stop_flag = {"done": False}
    start_time = time.time()
    
    def update_loop():
        while not stop_flag["done"]:
            elapsed = time.time() - start_time
            pct = min(99.0, (elapsed / estimated_total_sec) * 100)
            remaining_sec = max(0.0, estimated_total_sec - elapsed)
            try:
                if job_id:
                    _update_phase(job_id, "transcribing",
                                  progress_pct=round(pct, 1),
                                  elapsed_sec=int(elapsed),
                                  estimated_total_sec=int(estimated_total_sec),
                                  remaining_sec=int(remaining_sec),
                                  audio_dur_sec=int(audio_dur_sec))
            except Exception:
                pass
            time.sleep(2)
    
    if job_id:
        threading.Thread(target=update_loop, daemon=True).start()
    
    try:
        import mlx_whisper
        result = mlx_whisper.transcribe(
            str(src),
            path_or_hf_repo=model_size,
            word_timestamps=True,
            language="ko",
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
            "duration": int(audio_dur_sec),
            "segments": segments,
        }
        dst.write_text(json.dumps(out, ensure_ascii=False, indent=2))
        if job_id:
            _update_phase(job_id, "transcribing", progress_pct=100.0)

        # Phase C — WhisperX align (선택, ±50ms 정확도)
        # 환경변수 WHISPERX_ALIGN=0 으로 비활성. 실패 시 fallback 그대로.
        if _os.environ.get("WHISPERX_ALIGN", "1") != "0":
            try:
                import requests as _req
                url = _os.environ.get(
                    "WHISPERX_URL", "http://100.104.121.7:8771"
                )
                r = _req.post(
                    f"{url.rstrip('/')}/align",
                    json={"audio_path": str(src),
                          "transcript_segments": segments},
                    timeout=180,
                )
                if r.status_code == 200:
                    aligned = r.json()
                    # 사전 백업
                    bak = dst.with_suffix(".pre_align.json")
                    bak.write_text(dst.read_text())
                    aligned["duration"] = int(audio_dur_sec)
                    dst.write_text(json.dumps(aligned, ensure_ascii=False, indent=2))
                    if job_id:
                        _update_phase(job_id, "transcribing",
                                      progress_pct=100.0, aligned=True)
            except Exception as _ex:
                # silent fallback — pre-align transcript 그대로 유지
                if job_id:
                    _update_phase(job_id, "transcribing",
                                  progress_pct=100.0,
                                  align_skipped=str(_ex)[:200])
    finally:
        stop_flag["done"] = True


def _llm_postprocess(job_id: str) -> None:
    """Best-effort: cache LLM emphasis + clip candidates so UI is instant."""
    try:
        import json as _json
        from app import llm
        if not llm.health():
            return
        job_dir = JOBS_DIR / job_id
        tp = job_dir / "transcript.json"
        if not tp.exists():
            return
        segs = _json.loads(tp.read_text()).get("segments", [])
        # Emphasis (chunk_size=5)
        ep = job_dir / "llm_emphasis.json"
        if not ep.exists() and segs:
            ids = []
            for i in range(0, len(segs), 5):
                grp = segs[i:i+5]
                txt = " ".join(s.get("text", "") for s in grp)
                if not txt.strip():
                    continue
                try:
                    emp = llm.emphasis_words(txt)
                except Exception:
                    continue
                for ew in emp:
                    ew = ew.strip()
                    if not ew:
                        continue
                    found = False
                    for sj, seg in enumerate(grp):
                        for wj, w in enumerate(seg.get("words", []) or []):
                            wt = (w.get("word") or "").strip()
                            if wt and (ew == wt or ew in wt or wt in ew):
                                ids.append(f"s{i+sj}w{wj}")
                                found = True
                                break
                        if found:
                            break
            ep.write_text(_json.dumps({"emphasis_ids": list(dict.fromkeys(ids))}, ensure_ascii=False, indent=2))
        # Clips (n=5, no reasoning for speed)
        cp = job_dir / "llm_clips_n5_r0.json"
        if not cp.exists() and segs:
            try:
                clips = llm.clip_candidates(segs, n_clips=5, use_reasoning=False)
                cp.write_text(_json.dumps({"clips": clips}, ensure_ascii=False, indent=2))
            except Exception:
                pass
    except Exception:
        pass


def run_pipeline(job_id: str) -> None:
    job_dir = JOBS_DIR / job_id
    meta = json.loads((job_dir / "meta.json").read_text())
    audio_only = (meta.get("media_type") == "audio")
    src_ext = "mp3" if audio_only else "mp4"
    src = job_dir / f"source.{src_ext}"
    trimmed = job_dir / f"trimmed.{src_ext}"
    transcript = job_dir / "transcript.json"
    try:
        _update_phase(job_id, "downloading")
        download_youtube(meta["youtube_url"], src, audio_only=audio_only)
        _update_phase(job_id, "trimming")
        trim_video(src, trimmed, meta["start_sec"], meta["end_sec"], audio_only=audio_only)
        _update_phase(job_id, "transcribing")
        transcribe(trimmed, transcript, job_id=job_id)
        _update_phase(job_id, "ready")
        # Background: kick off LLM emphasis + clip suggestions (non-blocking, best-effort)
        threading.Thread(target=_llm_postprocess, args=(job_id,), daemon=True).start()
    except subprocess.CalledProcessError as e:
        _update_phase(job_id, "failed", error=f"subprocess: {e.stderr[:500] if e.stderr else str(e)}")
    except Exception as e:
        _update_phase(job_id, "failed", error=f"{type(e).__name__}: {str(e)[:500]}")


def start_pipeline_async(job_id: str) -> None:
    t = threading.Thread(target=run_pipeline, args=(job_id,), daemon=True)
    t.start()
