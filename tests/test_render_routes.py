"""P6 — render route 단위 테스트.

검증 대상:
- /api/render/health 응답 schema
- /api/render/<id>/mp4 invalid id rejection (디렉토리 traversal 방지)
- /api/render/<id>/mp4 캐시 적중 시 send_file 동작
- /api/render/<id>/status passthrough
"""
from __future__ import annotations

import io
import os
import sys
from pathlib import Path
from unittest import mock

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Flask test client — server 모듈 import (기존 endpoint와 충돌하지 않도록)
import importlib

import app.server as server_mod


@pytest.fixture
def client(tmp_path, monkeypatch):
    # cache dir를 임시로 redirect
    monkeypatch.setattr(server_mod, "_RENDER_CACHE_DIR", tmp_path / "render_cache")
    server_mod.app.config["TESTING"] = True
    return server_mod.app.test_client()


def test_health_endpoint_schema(client):
    """/api/render/health → {"ok": bool, "host": "..."}"""
    with mock.patch("app.render.client.HyperFramesClient.health", return_value=True):
        r = client.get("/api/render/health")
    assert r.status_code == 200
    body = r.get_json()
    assert "ok" in body and "host" in body
    assert body["ok"] is True
    assert body["host"].startswith("http://")


def test_health_endpoint_unreachable(client):
    with mock.patch("app.render.client.HyperFramesClient.health", return_value=False):
        r = client.get("/api/render/health")
    assert r.get_json()["ok"] is False


def test_mp4_rejects_invalid_render_id(client):
    """디렉토리 traversal/특수문자 reject (또는 redirect → 4xx)."""
    bad = ["../etc/passwd", "abc; rm -rf /", "a", "a" * 200, "../foo", "abc/def"]
    for rid in bad:
        r = client.get(f"/api/render/{rid}/mp4", follow_redirects=True)
        assert r.status_code in (400, 404), \
            f"{rid!r} should be rejected (got {r.status_code})"


def test_mp4_409_when_not_ready(client):
    with mock.patch("app.render.client.HyperFramesClient.status",
                    return_value={"render_id": "abc1234", "status": "rendering"}):
        r = client.get("/api/render/abc1234/mp4")
    assert r.status_code == 409
    assert r.get_json()["status"] == "rendering"


def test_mp4_502_when_hp_unreachable(client):
    from app.render import RenderError
    with mock.patch("app.render.client.HyperFramesClient.status",
                    side_effect=RenderError("connection refused")):
        r = client.get("/api/render/abc1234/mp4")
    assert r.status_code == 502
    assert r.get_json().get("hp_unreachable") is True


def test_mp4_streams_cached_file(client, tmp_path):
    """캐시 파일이 있으면 HP 호출 없이 send_file."""
    cache_dir = tmp_path / "render_cache"
    cache_dir.mkdir(parents=True)
    fake_mp4 = b"\x00\x00\x00\x18ftypmp42" + os.urandom(100)
    (cache_dir / "rid12345.mp4").write_bytes(fake_mp4)
    # status 호출이 일어나면 안 됨 — mock 안 함
    r = client.get("/api/render/rid12345/mp4")
    assert r.status_code == 200
    assert r.mimetype == "video/mp4"
    assert r.data == fake_mp4


def test_status_endpoint_passthrough(client):
    with mock.patch("app.render.client.HyperFramesClient.status",
                    return_value={"render_id": "abc1234", "status": "ready",
                                  "elapsed_sec": 8.5, "size_bytes": 110000}):
        r = client.get("/api/render/abc1234/status")
    assert r.status_code == 200
    body = r.get_json()
    assert body["status"] == "ready"
    assert body["size_bytes"] == 110000
