from __future__ import annotations
"""Editor backend — transcript, recommendations, video stream, export, edits, jobs list."""
import imageio_ffmpeg
_FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

import os
import json
import re
import subprocess
import shutil
from datetime import datetime
from pathlib import Path

from flask import jsonify, request, send_file, Response

from app.jobs import JOBS_DIR


def read_transcript(job_id: str) -> dict | None:
    p = JOBS_DIR / job_id / "transcript.json"
    if not p.exists():
        return None
    t = json.loads(p.read_text(encoding="utf-8"))
    edits_p = JOBS_DIR / job_id / "transcript_edits.json"
    if edits_p.exists():
        edits = json.loads(edits_p.read_text(encoding="utf-8"))
        for seg_idx, seg in enumerate(t.get("segments", [])):
            for w_idx, w in enumerate(seg.get("words", [])):
                key = f"s{seg_idx}w{w_idx}"
                if key in edits:
                    w["word"] = edits[key]
                    w["edited"] = True
    return t


FILLER_PATTERNS = [r"음+", r"어+", r"그+", r"네 ", r"있고요"]
CLIMAX_KEYWORDS = ["사랑", "하나님", "예수님", "은혜", "감사", "기도", "축복", "할렐루야"]


def compute_recommendations(transcript: dict) -> dict:
    if not transcript or "segments" not in transcript:
        return {"by_segment_idx": []}
    segments = transcript["segments"]
    repetition_set = set()
    for i, seg in enumerate(segments):
        text = seg.get("text", "").strip()
        if len(text) < 10 and i > 0:
            prev_text = segments[i - 1].get("text", "").strip()
            if text and text == prev_text:
                repetition_set.add(i)
    by_segment = []
    for i, seg in enumerate(segments):
        text = seg.get("text", "")
        wc = len(seg.get("words", []))
        duration = seg.get("end", 0) - seg.get("start", 0)
        kind = "keep"
        score = 0.5
        reasons = []
        is_filler = False
        if wc <= 2 and any(re.search(p, text) for p in FILLER_PATTERNS):
            is_filler = True
            kind = "cut_suggested"
            score = 0.7
            reasons.append("filler")
        if i in repetition_set:
            kind = "cut_suggested"
            score = 0.8
            reasons.append("반복")
        if duration < 0.5 and wc <= 1:
            kind = "cut_suggested"
            score = 0.6
            reasons.append("짧은 끊김")
        if not is_filler and i not in repetition_set:
            kw_hits = sum(1 for kw in CLIMAX_KEYWORDS if kw in text)
            if kw_hits >= 2 and wc >= 8:
                kind = "climax"
                score = 0.6 + 0.1 * kw_hits
                reasons.append(f"핵심어 {kw_hits}개")
        if not is_filler and 3 <= duration <= 15 and any(kw in text for kw in CLIMAX_KEYWORDS):
            if kind != "climax":
                kind = "shorts"
                score = 0.75
                reasons.append("shorts 후보")
        by_segment.append({"idx": i, "kind": kind, "score": round(score, 2), "reason": ", ".join(reasons) if reasons else ""})
    return {"by_segment_idx": by_segment}


def stream_video(job_id: str, filename: str = "trimmed.mp4"):
    return stream_media(job_id, filename, "video/mp4")


def stream_media(job_id: str, filename: str = "trimmed.mp4", mimetype: str = "video/mp4"):
    path = JOBS_DIR / job_id / filename
    if not path.exists():
        return jsonify({"error": "media not found"}), 404
    range_hdr = request.headers.get("Range")
    file_size = path.stat().st_size
    if not range_hdr:
        return send_file(str(path), mimetype=mimetype)
    m = re.match(r"bytes=(\d+)-(\d*)", range_hdr)
    if not m:
        return send_file(str(path), mimetype=mimetype)
    start = int(m.group(1))
    end = int(m.group(2)) if m.group(2) else file_size - 1
    end = min(end, file_size - 1)
    length = end - start + 1
    def gen():
        with path.open("rb") as f:
            f.seek(start)
            remaining = length
            while remaining > 0:
                chunk = f.read(min(8192, remaining))
                if not chunk: break
                remaining -= len(chunk)
                yield chunk
    resp = Response(gen(), status=206, mimetype=mimetype)
    resp.headers["Content-Range"] = f"bytes {start}-{end}/{file_size}"
    resp.headers["Accept-Ranges"] = "bytes"
    resp.headers["Content-Length"] = str(length)
    return resp


def save_text_edits(job_id: str, edits: dict) -> bool:
    job_dir = JOBS_DIR / job_id
    if not job_dir.is_dir(): return False
    (job_dir / "transcript_edits.json").write_text(json.dumps(edits, ensure_ascii=False, indent=2))
    return True


def save_edit_plan(job_id: str, name: str, plan: dict) -> bool:
    job_dir = JOBS_DIR / job_id
    if not job_dir.is_dir(): return False
    plans_dir = job_dir / "edit_plans"
    plans_dir.mkdir(exist_ok=True)
    safe = re.sub(r"[^a-zA-Z0-9가-힣_-]", "_", name)[:60] or "untitled"
    p = plans_dir / f"{safe}.json"
    plan["_saved_at"] = datetime.now().isoformat()
    plan["_name"] = name
    p.write_text(json.dumps(plan, ensure_ascii=False, indent=2))
    return True


def list_edit_plans(job_id: str) -> list:
    plans_dir = JOBS_DIR / job_id / "edit_plans"
    if not plans_dir.is_dir(): return []
    out = []
    for p in plans_dir.glob("*.json"):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            out.append({"filename": p.stem, "name": d.get("_name", p.stem),
                        "saved_at": d.get("_saved_at", ""),
                        "decision_count": len(d.get("decisions", []))})
        except Exception: continue
    return sorted(out, key=lambda x: x["saved_at"], reverse=True)


def load_edit_plan(job_id: str, filename: str) -> dict | None:
    p = JOBS_DIR / job_id / "edit_plans" / f"{filename}.json"
    if not p.exists(): return None
    return json.loads(p.read_text(encoding="utf-8"))


def list_all_jobs() -> list:
    out = []
    for d in JOBS_DIR.iterdir():
        if not d.is_dir(): continue
        meta_p = d / "meta.json"
        if not meta_p.exists(): continue
        try: m = json.loads(meta_p.read_text(encoding="utf-8"))
        except Exception: continue
        title = m.get("title") or m.get("youtube_id") or m.get("job_id")
        out.append({
            "job_id": m.get("job_id", d.name), "title": title,
            "youtube_url": m.get("youtube_url", ""), "phase": m.get("phase", "unknown"),
            "error": m.get("error"), "start_sec": m.get("start_sec", 0), "end_sec": m.get("end_sec", 0),
            "duration_min": round((m.get("end_sec", 0) - m.get("start_sec", 0)) / 60, 1),
            "created_at": m.get("created_at", ""), "has_transcript": (d / "transcript.json").exists(),
            "media_type": m.get("media_type", "video"),
            "progress_pct": m.get("progress_pct"),
            "elapsed_sec": m.get("elapsed_sec"),
            "remaining_sec": m.get("remaining_sec"),
            "estimated_total_sec": m.get("estimated_total_sec"),
            "audio_dur_sec": m.get("audio_dur_sec"),
            "has_llm_emphasis": (d / "llm_emphasis.json").exists(),
            "has_llm_clips": any(p.name.startswith("llm_clips_") for p in d.glob("llm_clips_*.json")),
        })
    return sorted(out, key=lambda x: x["created_at"], reverse=True)



def export_audio(job_id: str, edit_plan: dict) -> Path | None:
    """Audio-only export: mp3 + SRT + transcript_final.json. No video processing."""
    job_dir = JOBS_DIR / job_id
    src = job_dir / "trimmed.mp3"
    if not src.exists():
        return None
    out_dir = job_dir / "output"
    out_dir.mkdir(exist_ok=True)
    
    name = edit_plan.get("_name", edit_plan.get("name", "edited"))
    safe = re.sub(r"[^a-zA-Z0-9가-힣_-]", "_", name)[:40]
    ts = datetime.now().strftime("%H%M%S")
    out_path = out_dir / f"{safe}_{ts}.mp3"
    
    raw_keeps = [d for d in edit_plan.get("decisions", []) if d.get("type") == "keep"]
    if not raw_keeps:
        return None
    
    # Merge close keeps
    GAP = 0.250
    keeps = []
    for d in raw_keeps:
        if keeps and float(d["in_sec"]) - keeps[-1]["out_sec"] < GAP:
            keeps[-1] = {"type": "keep", "in_sec": keeps[-1]["in_sec"], "out_sec": float(d["out_sec"])}
        else:
            keeps.append({"type": "keep", "in_sec": float(d["in_sec"]), "out_sec": float(d["out_sec"])})
    
    AFADE = 0.040
    
    # Build filter_complex: trim each, then acrossfade chain
    parts = []
    for i, d in enumerate(keeps):
        ins = float(d["in_sec"])
        outs = float(d["out_sec"])
        seg_dur = max(0.001, outs - ins)
        do_fade = seg_dur > AFADE * 2
        chain = f"[0:a]atrim=start={ins:.3f}:end={outs:.3f},asetpts=PTS-STARTPTS"
        if do_fade:
            fades = []
            if i > 0:
                fades.append(f"afade=t=in:st=0:d={AFADE:.4f}")
            if i < len(keeps) - 1:
                fades.append(f"afade=t=out:st={(seg_dur - AFADE):.4f}:d={AFADE:.4f}")
            if fades:
                chain += "," + ",".join(fades)
        chain += f"[a{i}]"
        parts.append(chain)
    
    if len(keeps) == 1:
        parts.append("[a0]anull[outa]")
    else:
        concat_inputs = "".join(f"[a{i}]" for i in range(len(keeps)))
        parts.append(f"{concat_inputs}concat=n={len(keeps)}:v=0:a=1[outa]")
    
    filter_str = ";".join(parts)
    cmd = [
        _FFMPEG, "-y",
        "-i", str(src),
        "-filter_complex", filter_str,
        "-map", "[outa]",
        "-c:a", "libmp3lame", "-b:a", "192k",
        str(out_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    if result.returncode != 0:
        (out_dir / f"_ffmpeg_audio_err_{ts}.log").write_text(result.stderr[-3000:])
        return None
    
    # SRT (with new timestamps after cuts)
    srt_path = out_path.with_suffix(".srt")
    write_srt(job_id, keeps, srt_path)

    # transcript_final.json
    transcript_final = build_final_transcript(job_id, keeps, name)
    final_json_path = out_path.with_suffix(".transcript.json")
    final_json_path.write_text(json.dumps(transcript_final, ensure_ascii=False, indent=2))

    # Phase D — ffmpeg loudnorm master (-16 LUFS YouTube spec, Auphonic 우회)
    # 환경변수 SERMON_MASTER_AUDIO=0 으로 비활성 가능
    if os.environ.get("SERMON_MASTER_AUDIO", "1") != "0":
        try:
            from app.render.audio_master import ensure_master
            ensure_master(out_path)
        except Exception as ex:
            print(f"[master] skipped ({ex})", flush=True)

    return out_path


def build_final_transcript(job_id: str, keeps: list, name: str) -> dict:
    """Build edited transcript reflecting cut decisions + edits + new timestamps."""
    transcript = read_transcript(job_id)
    if not transcript:
        return {"error": "no source transcript"}
    
    final_segments = []
    cur_offset = 0.0
    for d in keeps:
        ins = d["in_sec"]
        outs = d["out_sec"]
        for seg in transcript.get("segments", []):
            if seg["start"] >= ins and seg["end"] <= outs:
                rel_start = seg["start"] - ins + cur_offset
                rel_end = seg["end"] - ins + cur_offset
                new_words = []
                for w in (seg.get("words") or []):
                    new_words.append({
                        "word": w.get("word", ""),
                        "start": round(w.get("start", 0) - ins + cur_offset, 2),
                        "end": round(w.get("end", 0) - ins + cur_offset, 2),
                        "probability": w.get("probability", 1.0),
                        "edited": bool(w.get("edited")),
                    })
                final_segments.append({
                    "start": round(rel_start, 2),
                    "end": round(rel_end, 2),
                    "text": "".join(w["word"] for w in new_words) or seg.get("text", ""),
                    "words": new_words,
                })
        cur_offset += outs - ins
    
    return {
        "version": "edited",
        "language": transcript.get("language", "ko"),
        "duration": round(cur_offset, 2),
        "_meta": {
            "name": name,
            "exported_at": datetime.now().isoformat(),
            "source_job": job_id,
            "edit_decisions": keeps,
        },
        "segments": final_segments,
    }


def write_srt(job_id: str, keep_decisions: list, srt_path: Path) -> None:
    transcript = read_transcript(job_id)
    if not transcript: return
    def fmt_ts(sec):
        ms = int((sec - int(sec)) * 1000)
        s = int(sec) % 60
        m = (int(sec) // 60) % 60
        h = int(sec) // 3600
        return f"{h:02}:{m:02}:{s:02},{ms:03}"
    cues = []
    cur_offset = 0.0
    for d in keep_decisions:
        dur = d["out_sec"] - d["in_sec"]
        for seg in transcript.get("segments", []):
            if seg["start"] >= d["in_sec"] and seg["end"] <= d["out_sec"]:
                rel_start = seg["start"] - d["in_sec"] + cur_offset
                rel_end = seg["end"] - d["in_sec"] + cur_offset
                text = "".join(w.get("word", "") for w in seg.get("words", [])) if seg.get("words") else seg.get("text", "")
                cues.append((rel_start, rel_end, text.strip()))
        cur_offset += dur
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, (s, e, t) in enumerate(cues, 1):
            f.write(f"{i}\n{fmt_ts(s)} --> {fmt_ts(e)}\n{t}\n\n")


def export_concat(job_id: str, edit_plan: dict) -> Path | None:
    """Cross-dissolve export: real xfade between clips for natural transitions.
    
    Strategy: render each keep to its own mp4, then iteratively pair-wise xfade.
    Slower but stable for any number of segments.
    """
    job_dir = JOBS_DIR / job_id
    src = job_dir / "trimmed.mp4"
    out_dir = job_dir / "output"
    out_dir.mkdir(exist_ok=True)
    
    name = edit_plan.get("_name", edit_plan.get("name", "edited"))
    safe = re.sub(r"[^a-zA-Z0-9가-힣_-]", "_", name)[:40]
    ts = datetime.now().strftime("%H%M%S")
    out_path = out_dir / f"{safe}_{ts}.mp4"
    
    raw_keeps = [d for d in edit_plan.get("decisions", []) if d.get("type") == "keep"]
    if not raw_keeps:
        return None
    
    # Merge close keeps (gap < 250ms)
    GAP = 0.250
    keeps = []
    for d in raw_keeps:
        if keeps and float(d["in_sec"]) - keeps[-1]["out_sec"] < GAP:
            keeps[-1] = {"type": "keep", "in_sec": keeps[-1]["in_sec"], "out_sec": float(d["out_sec"])}
        else:
            keeps.append({"type": "keep", "in_sec": float(d["in_sec"]), "out_sec": float(d["out_sec"])})
    
    XFADE = 0.400  # 400ms cross-dissolve — natural, clearly visible but not slow
    AFADE = 0.040  # 40ms audio crossfade
    
    work_dir = out_dir / f"_work_{ts}"
    work_dir.mkdir(exist_ok=True)
    
    try:
        # Step 1: render each keep to its own mp4 (fps=30, re-encoded)
        seg_paths = []
        for i, d in enumerate(keeps):
            ins = float(d["in_sec"])
            outs = float(d["out_sec"])
            seg_dur = outs - ins
            if seg_dur < XFADE * 2:
                # Too short for xfade — skip it (or could include without fade)
                continue
            seg_path = work_dir / f"seg_{i:04d}.mkv"
            cmd = [
                _FFMPEG, "-y", "-ss", f"{ins:.3f}", "-to", f"{outs:.3f}", "-i", str(src),
                "-vf", "fps=30,setpts=PTS-STARTPTS",
                "-af", "asetpts=PTS-STARTPTS",
                "-c:v", "libx264", "-crf", "20", "-preset", "ultrafast",
                "-c:a", "pcm_s16le",
                "-pix_fmt", "yuv420p",
                str(seg_path)
            ]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if r.returncode != 0 or not seg_path.exists():
                (out_dir / f"_ffmpeg_err_{ts}.log").write_text(f"seg {i} failed:\n{r.stderr[-2000:]}")
                shutil.rmtree(work_dir, ignore_errors=True)
                return None
            seg_paths.append(seg_path)
        
        if not seg_paths:
            shutil.rmtree(work_dir, ignore_errors=True)
            return None
        
        if len(seg_paths) == 1:
            # Single segment: re-encode to mp4 with AAC
            cmd = [
                _FFMPEG, "-y", "-i", str(seg_paths[0]),
                "-c:v", "copy",
                "-c:a", "aac", "-b:a", "192k",
                str(out_path)
            ]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if r.returncode != 0:
                (out_dir / f"_ffmpeg_err_{ts}.log").write_text(f"single seg encode failed:\n{r.stderr[-2000:]}")
                shutil.rmtree(work_dir, ignore_errors=True)
                return None
        else:
            # Step 2: iterative pair-wise xfade
            current = seg_paths[0]
            for i in range(1, len(seg_paths)):
                next_clip = seg_paths[i]
                # Probe current duration
                probe_cmd = [_FFMPEG, "-i", str(current), "-f", "null", "-"]
                probe = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=60)
                m = re.search(r"time=(\d+):(\d+):(\d+\.\d+)", probe.stderr)
                if not m:
                    (out_dir / f"_ffmpeg_err_{ts}.log").write_text(f"probe {i} failed:\n{probe.stderr[-1000:]}")
                    shutil.rmtree(work_dir, ignore_errors=True)
                    return None
                h, mm, ss = m.groups()
                cur_dur = int(h) * 3600 + int(mm) * 60 + float(ss)
                offset = max(0.0, cur_dur - XFADE)
                
                fc = (
                    f"[0:v][1:v]xfade=transition=fade:duration={XFADE:.4f}:offset={offset:.4f}[outv];"
                    f"[0:a][1:a]acrossfade=d={AFADE:.4f}[outa]"
                )
                # Final pass: encode AAC. Intermediate: keep PCM lossless.
                is_final_merge = (i == len(seg_paths) - 1)
                if is_final_merge:
                    audio_codec_args = ["-c:a", "aac", "-b:a", "192k"]
                    merged_ext = ".mp4"
                else:
                    audio_codec_args = ["-c:a", "pcm_s16le"]
                    merged_ext = ".mkv"
                merged = work_dir / f"merged_{i:04d}{merged_ext}"
                cmd = [
                    _FFMPEG, "-y", "-i", str(current), "-i", str(next_clip),
                    "-filter_complex", fc,
                    "-map", "[outv]", "-map", "[outa]",
                    "-c:v", "libx264", "-crf", "20", "-preset", "ultrafast",
                    "-pix_fmt", "yuv420p",
                ] + audio_codec_args + [
                    str(merged)
                ]
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
                if r.returncode != 0 or not merged.exists():
                    (out_dir / f"_ffmpeg_err_{ts}.log").write_text(f"merge {i} failed:\n{r.stderr[-2000:]}")
                    shutil.rmtree(work_dir, ignore_errors=True)
                    return None
                current = merged
            shutil.move(str(current), str(out_path))
        
        srt_path = out_path.with_suffix(".srt")
        write_srt(job_id, keeps, srt_path)
        return out_path
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)
