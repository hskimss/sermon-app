import sys
from pathlib import Path as _Path
sys.path.insert(0, str(_Path(__file__).resolve().parent.parent))

from flask import Flask, jsonify, request, send_from_directory, send_file
from pathlib import Path

app = Flask(__name__, static_folder=str(Path(__file__).parent / "static"))


@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/api/job/new", methods=["POST"])
def api_job_new():
    body = request.get_json()
    from app.jobs import find_or_create_job, get_job_status
    from app.pipeline import start_pipeline_async

    media_type = body.get("media_type", "video")
    if media_type not in ("video", "audio"):
        media_type = "video"

    job_id, reused = find_or_create_job(
        body["youtube_url"], int(body.get("start_sec", 0)),
        int(body.get("end_sec", 0)), body.get("mode", "longform"),
        body.get("target_sec"),
        media_type=media_type)

    status = get_job_status(job_id)
    if not reused or status.get("phase") in ("queued", "failed"):
        start_pipeline_async(job_id)

    return jsonify({"job_id": job_id, "reused": reused, "phase": status.get("phase", "queued"), "media_type": media_type}), 201


@app.route("/api/job/<job_id>/status", methods=["GET"])
def api_job_status(job_id):
    from app.jobs import get_job_status
    s = get_job_status(job_id)
    return (jsonify(s), 200) if s else (jsonify({"error": "not found"}), 404)


@app.route("/api/job/<job_id>/meta", methods=["GET"])
def api_job_meta(job_id):
    from app.jobs import get_job_status
    s = get_job_status(job_id)
    return (jsonify(s), 200) if s else (jsonify({"error": "not found"}), 404)


@app.route("/api/jobs", methods=["GET"])
def api_jobs_list():
    from app.editor import list_all_jobs
    return jsonify(list_all_jobs()), 200


@app.route("/api/job/<job_id>/transcript", methods=["GET"])
def api_transcript(job_id):
    from app.editor import read_transcript
    t = read_transcript(job_id)
    return (jsonify(t), 200) if t else (jsonify({"error": "transcript not ready"}), 404)


@app.route("/api/job/<job_id>/transcript-edits", methods=["POST"])
def api_save_transcript_edits(job_id):
    from app.editor import save_text_edits
    body = request.get_json()
    if save_text_edits(job_id, body.get("edits", {})):
        return jsonify({"ok": True}), 200
    return jsonify({"error": "save failed"}), 500


@app.route("/api/job/<job_id>/recommendations", methods=["GET"])
def api_recommendations(job_id):
    from app.editor import read_transcript, compute_recommendations
    t = read_transcript(job_id)
    if not t:
        return jsonify({"error": "transcript not ready"}), 404
    return jsonify(compute_recommendations(t)), 200


@app.route("/api/job/<job_id>/video", methods=["GET"])
def api_video(job_id):
    from app.editor import stream_media
    from app.jobs import get_job_status
    meta = get_job_status(job_id) or {}
    is_audio = meta.get("media_type") == "audio"
    filename = "trimmed.mp3" if is_audio else "trimmed.mp4"
    mime = "audio/mpeg" if is_audio else "video/mp4"
    return stream_media(job_id, filename, mime)


@app.route("/api/job/<job_id>/audio", methods=["GET"])
def api_audio(job_id):
    from app.editor import stream_media
    return stream_media(job_id, "trimmed.mp3", "audio/mpeg")


@app.route("/api/job/<job_id>/edit-plan", methods=["GET", "POST"])
def api_edit_plan_save(job_id):
    from app.editor import save_edit_plan, list_edit_plans
    if request.method == "GET":
        return jsonify(list_edit_plans(job_id)), 200
    body = request.get_json()
    name = body.get("name", "untitled")
    if save_edit_plan(job_id, name, body):
        return jsonify({"ok": True, "name": name}), 200
    return jsonify({"error": "save failed"}), 500


@app.route("/api/job/<job_id>/edit-plan/<filename>", methods=["GET"])
def api_edit_plan_load(job_id, filename):
    from app.editor import load_edit_plan
    p = load_edit_plan(job_id, filename)
    if p is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(p), 200


@app.route("/api/job/<job_id>/export", methods=["POST"])
def api_export(job_id):
    from app.editor import export_concat, export_audio
    from app.jobs import get_job_status
    edit_plan = request.get_json()
    meta = get_job_status(job_id) or {}
    if meta.get("media_type") == "audio":
        out = export_audio(job_id, edit_plan)
    else:
        out = export_concat(job_id, edit_plan)
    if out is None:
        return jsonify({"error": "export failed"}), 500
    return jsonify({"output": str(out), "filename": out.name}), 200


@app.route("/api/job/<job_id>/output/<path:filename>", methods=["GET"])
def api_output_file(job_id, filename):
    from app.jobs import JOBS_DIR
    p = JOBS_DIR / job_id / "output" / filename
    if not p.exists():
        return jsonify({"error": "not found"}), 404
    return send_file(str(p))


@app.route("/editor/<job_id>")
def editor_page(job_id):
    return send_from_directory(app.static_folder, "editor.html")


@app.route("/healthz")
def healthz():
    return jsonify({"ok": True}), 200




# ── Local Gemma 4 endpoints (S1 clip selection, S2 caption emphasis) ──
@app.route("/api/job/<job_id>/llm-clips", methods=["POST"])
def api_llm_clips(job_id):
    from app.jobs import JOBS_DIR
    from app import llm
    import json as _json
    job_dir = JOBS_DIR / job_id
    tp = job_dir / "transcript.json"
    if not tp.exists():
        return jsonify({"error": "no transcript"}), 404
    body = request.get_json(silent=True) or {}
    n = int(body.get("n", 5))
    use_reasoning = bool(body.get("reasoning", False))
    segs = _json.loads(tp.read_text()).get("segments", [])
    cache_path = job_dir / f"llm_clips_n{n}_r{int(use_reasoning)}.json"
    if cache_path.exists() and not body.get("force"):
        return jsonify(_json.loads(cache_path.read_text()))
    try:
        clips = llm.clip_candidates(segs, n_clips=n, use_reasoning=use_reasoning)
    except Exception as e:
        return jsonify({"error": f"{type(e).__name__}: {e}"}), 500
    cache_path.write_text(_json.dumps({"clips": clips}, ensure_ascii=False, indent=2))
    return jsonify({"clips": clips, "cached": False})


@app.route("/api/job/<job_id>/llm-emphasis", methods=["POST"])
def api_llm_emphasis(job_id):
    """Returns emphasis word ids for the editor.
    Strategy: chunk the transcript into ~5-segment groups, ask Gemma 4 for
    1-3 emphasis words per chunk, then map back to word ids (segIdx_wordIdx).
    Cached to disk after first run.
    """
    from app.jobs import JOBS_DIR
    from app import llm
    import json as _json
    job_dir = JOBS_DIR / job_id
    tp = job_dir / "transcript.json"
    if not tp.exists():
        return jsonify({"error": "no transcript"}), 404
    body = request.get_json(silent=True) or {}
    cache_path = job_dir / "llm_emphasis.json"
    if cache_path.exists() and not body.get("force"):
        return jsonify(_json.loads(cache_path.read_text()))
    segs = _json.loads(tp.read_text()).get("segments", [])
    chunk_size = int(body.get("chunk_size", 5))
    emphasis_ids = []
    for i in range(0, len(segs), chunk_size):
        group = segs[i:i+chunk_size]
        chunk_text = " ".join(s.get("text", "") for s in group)
        if not chunk_text.strip():
            continue
        try:
            emp_words = llm.emphasis_words(chunk_text)
        except Exception:
            continue
        # Map each picked word back to the closest matching word id in the chunk
        for ew in emp_words:
            ew_clean = ew.strip()
            if not ew_clean:
                continue
            for sj, seg in enumerate(group):
                seg_idx_global = i + sj
                for wj, w in enumerate(seg.get("words", []) or []):
                    word_text = (w.get("word") or "").strip()
                    if word_text and (ew_clean == word_text or ew_clean in word_text or word_text in ew_clean):
                        emphasis_ids.append(f"s{seg_idx_global}w{wj}")
                        break
                else:
                    continue
                break  # found it in this segment, move to next emphasis word
    payload = {"emphasis_ids": list(dict.fromkeys(emphasis_ids))}  # dedup, preserve order
    cache_path.write_text(_json.dumps(payload, ensure_ascii=False, indent=2))
    return jsonify(payload)


@app.route("/api/llm/health", methods=["GET"])
def api_llm_health():
    from app import llm
    return jsonify({"ok": llm.health(), "host": llm.LLM_HOST, "model": llm.DEFAULT_MODEL})




@app.route("/api/job/<job_id>/llm-bulk-export", methods=["POST"])
def api_llm_bulk_export(job_id):
    """Option 1 — export each AI-suggested clip as its own file."""
    from app.jobs import JOBS_DIR, get_job_status
    from app.editor import export_concat, export_audio
    import json as _json, re as _re
    job_dir = JOBS_DIR / job_id
    body = request.get_json(silent=True) or {}
    n = int(body.get("n", 5))
    # Look for cached clips file (n=5 by default)
    cached = list(job_dir.glob("llm_clips_*.json"))
    if not cached:
        return jsonify({"error": "no AI clips cached. Run /llm-clips first."}), 404
    clips = _json.loads(cached[0].read_text()).get("clips", [])[:n]
    if not clips:
        return jsonify({"error": "empty clips"}), 404
    media_type = (get_job_status(job_id) or {}).get("media_type", "video")
    exporter = export_audio if media_type == "audio" else export_concat
    outputs = []
    errors = []
    for i, c in enumerate(clips):
        ins = float(c.get("start_sec", 0))
        outs = float(c.get("end_sec", 0))
        if outs <= ins:
            continue
        arch = _re.sub(r"[^a-zA-Z0-9]", "_", c.get("hook_archetype", "clip"))[:20]
        score = c.get("virality_score", 0)
        plan = {
            "_name": f"clip{i+1}_{score}_{arch}",
            "decisions": [{"type": "keep", "in_sec": ins, "out_sec": outs}],
        }
        try:
            out = exporter(job_id, plan)
            if out:
                outputs.append({"index": i+1, "filename": out.name, "score": score, "archetype": c.get("hook_archetype")})
            else:
                errors.append({"index": i+1, "error": "exporter returned None"})
        except Exception as e:
            errors.append({"index": i+1, "error": f"{type(e).__name__}: {e}"})
    return jsonify({"outputs": outputs, "errors": errors, "count": len(outputs)})


@app.route("/api/job/<job_id>/llm-highlight-reel", methods=["POST"])
def api_llm_highlight_reel(job_id):
    """Option 2-A — AI rearranges clips for narrative arc, exports as single file."""
    from app.jobs import JOBS_DIR, get_job_status
    from app.editor import export_concat, export_audio
    from app import llm
    import json as _json
    job_dir = JOBS_DIR / job_id
    body = request.get_json(silent=True) or {}
    n = int(body.get("n", 5))
    cached = list(job_dir.glob("llm_clips_*.json"))
    if not cached:
        return jsonify({"error": "no AI clips cached. Run /llm-clips first."}), 404
    clips = _json.loads(cached[0].read_text()).get("clips", [])[:n]
    if len(clips) < 2:
        return jsonify({"error": "need at least 2 clips"}), 400
    # Level 1 — narrative arc rearrangement
    rearranged = llm.rearrange_for_arc(clips)
    # Build edit_plan with all clip ranges in new order
    decisions = []
    for c in rearranged:
        ins = float(c.get("start_sec", 0))
        outs = float(c.get("end_sec", 0))
        if outs > ins:
            decisions.append({"type": "keep", "in_sec": ins, "out_sec": outs})
    if not decisions:
        return jsonify({"error": "no valid clips after rearrangement"}), 500
    plan = {"_name": f"highlight_reel_n{len(decisions)}", "decisions": decisions}
    media_type = (get_job_status(job_id) or {}).get("media_type", "video")
    exporter = export_audio if media_type == "audio" else export_concat
    out = exporter(job_id, plan)
    if not out:
        return jsonify({"error": "export failed"}), 500
    # Save the rearrangement decision for reference
    (job_dir / "llm_highlight_arc.json").write_text(
        _json.dumps({
            "original_order": [{"i": i, "score": c.get("virality_score"),
                                "archetype": c.get("hook_archetype"),
                                "hook": (c.get("hook_text") or "")[:80]}
                               for i, c in enumerate(clips)],
            "rearranged_order": [{"score": c.get("virality_score"),
                                  "archetype": c.get("hook_archetype"),
                                  "hook": (c.get("hook_text") or "")[:80]}
                                 for c in rearranged],
            "output": out.name,
        }, ensure_ascii=False, indent=2))
    return jsonify({
        "output": out.name,
        "clip_count": len(decisions),
        "rearranged": [{"score": c.get("virality_score"),
                        "archetype": c.get("hook_archetype")}
                       for c in rearranged]
    })


# ── HyperFrames render endpoints (P2 — design HYPERFRAMES_DESIGN.md §2.3) ──
@app.route("/api/job/<job_id>/render", methods=["POST"])
def api_render(job_id):
    """sermon-app → HP HyperFrames 렌더 서버로 작업 제출.

    body:
      {
        "clip": {"start_sec": 92, "end_sec": 152, "hook_archetype": "..."},
        "composition": "sermon_short_v1",   # default
        "format": "9:16",                    # default
        "quality": "1080p",                  # default
        "callback_url": null,                # 옵션
        "dry_run": false                     # true면 payload만 반환
      }
    """
    from app.jobs import JOBS_DIR
    from app.render import build_short_payload, HyperFramesClient, RenderError

    body = request.get_json(silent=True) or {}
    clip = body.get("clip") or {}
    if "start_sec" not in clip or "end_sec" not in clip:
        return jsonify({"error": "clip.start_sec/end_sec required"}), 400

    try:
        payload = build_short_payload(
            job_id=job_id, clip=clip, jobs_dir=JOBS_DIR,
            composition=body.get("composition", "sermon_short_v1"),
            fmt=body.get("format", "9:16"),
            quality=body.get("quality", "1080p"),
            house_style=body.get("house_style", "a_church_london_v1"),
            callback_url=body.get("callback_url"),
        )
    except FileNotFoundError as ex:
        return jsonify({"error": str(ex)}), 404

    if body.get("dry_run"):
        return jsonify({"dry_run": True, "payload_preview": payload})

    client = HyperFramesClient()
    try:
        result = client.submit(payload)
    except RenderError as ex:
        return jsonify({"error": str(ex), "hp_unreachable": True}), 502
    return jsonify({**result, "render_engine": "hyperframes"})


@app.route("/api/render/<render_id>/status", methods=["GET"])
def api_render_status(render_id):
    from app.render import HyperFramesClient, RenderError
    try:
        return jsonify(HyperFramesClient().status(render_id))
    except RenderError as ex:
        return jsonify({"error": str(ex)}), 502


@app.route("/api/render/health", methods=["GET"])
def api_render_health():
    from app.render import HyperFramesClient
    c = HyperFramesClient()
    return jsonify({"ok": c.health(), "host": c.base_url})


# Mac 측 mp4 캐시 — HP에서 한 번 받으면 재사용
_RENDER_CACHE_DIR = Path.home() / ".cache" / "sermon-app" / "render"


def _safe_render_id(rid: str) -> str:
    """디렉토리 traversal 방지 — hex/영문숫자/`-_` 만 통과."""
    import re as _re
    if not _re.fullmatch(r"[A-Za-z0-9_\-]{4,64}", rid or ""):
        from flask import abort
        abort(400, description="invalid render_id")
    return rid


@app.route("/api/render/<render_id>/mp4", methods=["GET"])
def api_render_mp4(render_id):
    """HP에서 mp4 fetch + Mac 로컬 캐시 + send_file.

    캐시 위치: ~/.cache/sermon-app/render/<render_id>.mp4
    상태 의존: HP에서 status=ready 일 때만 fetch (아니면 409).
    """
    from app.render import HyperFramesClient, RenderError
    from flask import send_file
    rid = _safe_render_id(render_id)

    cache_dir = _RENDER_CACHE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / f"{rid}.mp4"

    if not cache_path.exists():
        client = HyperFramesClient()
        # ready 인지 확인 (HP가 하루 보관하므로 status로 판단)
        try:
            st = client.status(rid)
        except RenderError as ex:
            return jsonify({"error": str(ex), "hp_unreachable": True}), 502
        if st.get("status") != "ready":
            return jsonify({"error": "not ready", "status": st.get("status")}), 409
        # streaming download
        try:
            client.fetch_output(rid, cache_path)
        except Exception as ex:
            try:
                cache_path.unlink()
            except FileNotFoundError:
                pass
            return jsonify({"error": str(ex)}), 502

    return send_file(
        cache_path,
        mimetype="video/mp4",
        as_attachment=False,
        conditional=True,  # Range 지원
        download_name=f"{rid}.mp4",
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=False)
