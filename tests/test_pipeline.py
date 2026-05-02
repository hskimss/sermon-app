import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import app.jobs as jobs_module
import app.pipeline as pipeline_module


@pytest.fixture(autouse=True)
def isolated_jobs_dir(tmp_path, monkeypatch):
    jobs_dir = tmp_path / "jobs"
    monkeypatch.setattr(jobs_module, "JOBS_DIR", jobs_dir)
    monkeypatch.setattr(pipeline_module, "JOBS_DIR", jobs_dir)
    return jobs_dir


def _create_job(jobs_dir, job_id="test_job", **overrides):
    job_dir = jobs_dir / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    meta = {"job_id": job_id, "youtube_url": "https://youtu.be/abc123",
            "start_sec": 0, "end_sec": 60, "phase": "queued",
            "cache_key": "test_ck", "mode": "longform"}
    meta.update(overrides)
    (job_dir / "meta.json").write_text(json.dumps(meta))
    return job_dir


def test_download_youtube_skip_cache(tmp_path):
    out = tmp_path / "source.mp4"
    out.write_bytes(b"fake_video_data")
    with patch("app.pipeline.subprocess.run") as mock_run:
        pipeline_module.download_youtube("https://youtu.be/abc", out)
        mock_run.assert_not_called()


def test_trim_video_args(tmp_path):
    src = tmp_path / "source.mp4"
    src.write_bytes(b"data")
    dst = tmp_path / "trimmed.mp4"
    with patch("app.pipeline.subprocess.run") as mock_run:
        pipeline_module.trim_video(src, dst, 10, 70)
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "-ss" in cmd and "10" in cmd
        assert "-t" in cmd and "60" in cmd
        assert "-c" in cmd and "copy" in cmd


def test_run_pipeline_phase_transitions(isolated_jobs_dir):
    _create_job(isolated_jobs_dir)
    phases_seen = []
    original_update = pipeline_module._update_phase
    def spy_update(job_id, phase, **extra):
        phases_seen.append(phase)
        original_update(job_id, phase, **extra)
    with patch("app.pipeline._update_phase", side_effect=spy_update), \
         patch("app.pipeline.download_youtube"), \
         patch("app.pipeline.trim_video"), \
         patch("app.pipeline.transcribe"):
        pipeline_module.run_pipeline("test_job")
    assert phases_seen == ["downloading", "trimming", "transcribing", "ready"]


def test_run_pipeline_failure_caught(isolated_jobs_dir):
    job_dir = _create_job(isolated_jobs_dir)
    with patch("app.pipeline.download_youtube", side_effect=RuntimeError("boom")):
        pipeline_module.run_pipeline("test_job")
    meta = json.loads((job_dir / "meta.json").read_text())
    assert meta["phase"] == "failed"
    assert "boom" in meta["error"]


def test_update_phase_preserves_existing_keys(isolated_jobs_dir):
    job_dir = _create_job(isolated_jobs_dir, custom_field="keep_me")
    pipeline_module._update_phase("test_job", "downloading")
    meta = json.loads((job_dir / "meta.json").read_text())
    assert meta["phase"] == "downloading"
    assert meta["custom_field"] == "keep_me"
    assert meta["youtube_url"] == "https://youtu.be/abc123"


def test_start_pipeline_async_returns_immediately(isolated_jobs_dir):
    _create_job(isolated_jobs_dir)
    with patch("app.pipeline.run_pipeline"):
        t0 = time.monotonic()
        pipeline_module.start_pipeline_async("test_job")
        elapsed = time.monotonic() - t0
    assert elapsed < 0.1
