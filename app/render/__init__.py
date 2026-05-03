"""sermon-app HyperFrames 통합 모듈.

설계 문서: 교회 앱/HYPERFRAMES_DESIGN.md (v1.0)

- payload.build_short_payload(job_id, clip) → HyperFrames 렌더 요청 body
- scripture.detect_scripture_refs(transcript, clip) → 인용 메타
- client.HyperFramesClient(base_url) → HP /render 엔드포인트 통신
"""
from .payload import build_short_payload
from .scripture import detect_scripture_refs, lookup_verse
from .client import HyperFramesClient, RenderError
from .bible import BibleStore, BookNameMapper, get_default_store

__all__ = [
    "build_short_payload",
    "detect_scripture_refs",
    "lookup_verse",
    "HyperFramesClient",
    "RenderError",
    "BibleStore",
    "BookNameMapper",
    "get_default_store",
]
