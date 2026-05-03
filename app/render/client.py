"""HP-Z2-LLM HyperFrames 렌더 서버 클라이언트.

설계 문서: HYPERFRAMES_DESIGN.md §2.2
- POST /render → {render_id, status, estimated_sec}
- GET  /render/<id>/status
- callback: POST {callback_url} on completion
"""
from __future__ import annotations

import os
from typing import Any

import requests

HF_RENDER_URL = os.getenv(
    "HF_RENDER_URL", "http://100.104.121.7:8770"
)


class RenderError(RuntimeError):
    pass


class HyperFramesClient:
    def __init__(self, base_url: str | None = None, timeout: int = 30):
        self.base_url = (base_url or HF_RENDER_URL).rstrip("/")
        self.timeout = timeout

    def health(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/health", timeout=5)
            return r.status_code == 200
        except requests.RequestException:
            return False

    def submit(self, payload: dict) -> dict:
        """렌더 요청 제출. 즉시 {render_id, status, estimated_sec} 반환."""
        try:
            r = requests.post(
                f"{self.base_url}/render", json=payload, timeout=self.timeout
            )
            r.raise_for_status()
            return r.json()
        except requests.RequestException as ex:
            raise RenderError(f"submit 실패: {ex}") from ex

    def status(self, render_id: str) -> dict:
        try:
            r = requests.get(
                f"{self.base_url}/render/{render_id}/status", timeout=10
            )
            r.raise_for_status()
            return r.json()
        except requests.RequestException as ex:
            raise RenderError(f"status 조회 실패: {ex}") from ex

    def output_url(self, render_id: str, ext: str = "mp4") -> str:
        return f"{self.base_url}/output/{render_id}.{ext}"

    def fetch_output(self, render_id: str, dest_path: str | os.PathLike,
                     ext: str = "mp4", timeout: int = 600) -> str:
        """완성 mp4를 sermon-app 로컬로 가져옴 (콜백 안 쓸 때 사용)."""
        url = self.output_url(render_id, ext)
        with requests.get(url, stream=True, timeout=timeout) as r:
            r.raise_for_status()
            with open(dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1 << 16):
                    if chunk:
                        f.write(chunk)
        return str(dest_path)

    def stream_output(self, render_id: str, ext: str = "mp4",
                      timeout: int = 600):
        """HP에서 mp4 chunked stream을 그대로 반환 (Flask가 generator로 사용).

        Returns:
            requests.Response (with `iter_content`) — 호출자가 close 책임.
        """
        url = self.output_url(render_id, ext)
        # raise_for_status 후 자체 close — Flask `send_file`/`Response(stream)` 패턴
        r = requests.get(url, stream=True, timeout=timeout)
        r.raise_for_status()
        return r
