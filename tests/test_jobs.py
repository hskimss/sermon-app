import pytest
from app.jobs import extract_youtube_id, cache_key, find_or_create_job, JOBS_DIR
import app.jobs as jobs_module


@pytest.fixture(autouse=True)
def isolated_jobs_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(jobs_module, "JOBS_DIR", tmp_path / "jobs")


def test_extract_youtube_id_short_url():
    assert extract_youtube_id("https://youtu.be/abc12345678") == "abc12345678"


def test_extract_youtube_id_watch_url():
    assert extract_youtube_id("https://www.youtube.com/watch?v=abc12345678") == "abc12345678"


def test_extract_youtube_id_invalid():
    assert extract_youtube_id("https://example.com/not-youtube") is None


def test_cache_key_same_input():
    k1 = cache_key("https://youtu.be/abc12345678", 0, 2700)
    k2 = cache_key("https://youtu.be/abc12345678", 0, 2700)
    assert k1 == k2


def test_cache_key_different_start():
    k1 = cache_key("https://youtu.be/abc12345678", 0, 2700)
    k2 = cache_key("https://youtu.be/abc12345678", 10, 2700)
    assert k1 != k2


def test_cache_key_different_end():
    k1 = cache_key("https://youtu.be/abc12345678", 0, 2700)
    k2 = cache_key("https://youtu.be/abc12345678", 0, 3000)
    assert k1 != k2


def test_find_or_create_job_new():
    job_id, reused = find_or_create_job(
        "https://youtu.be/abc12345678", 0, 2700, "longform", None)
    assert reused is False
    assert "abc12345678" in job_id


def test_find_or_create_job_reuse():
    job_id1, reused1 = find_or_create_job(
        "https://youtu.be/abc12345678", 0, 2700, "longform", None)
    job_id2, reused2 = find_or_create_job(
        "https://youtu.be/abc12345678", 0, 2700, "longform", None)
    assert reused1 is False
    assert reused2 is True
    assert job_id1 == job_id2


def test_find_or_create_job_different_input():
    job_id1, _ = find_or_create_job(
        "https://youtu.be/abc12345678", 0, 2700, "longform", None)
    job_id2, reused2 = find_or_create_job(
        "https://youtu.be/xyz99999999", 0, 2700, "longform", None)
    assert reused2 is False
    assert job_id1 != job_id2
