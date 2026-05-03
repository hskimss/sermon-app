"""성경 본문 라이브러리.

설계: HF_PHASE_PLAN_v2.md §2 P3a
- krv.json : 한국어 본문 (사용자가 직접 채움 — 저작권 확인 후)
- kjv.json : KJV (영어, Public Domain) — 인프라 검증용 데모 데이터

라이선스 주의:
- 개역개정 (KRV 신표준) = 대한성서공회 © → 공개/외부 공유 금지
- 개역한글 (1961) = PD 가능성 있으나 명시 미확정
- KJV (1611) = Public Domain (전 세계)
"""
from .loader import (
    BibleStore,
    BookNameMapper,
    DEFAULT_TRANSLATION,
    get_default_store,
)

__all__ = [
    "BibleStore",
    "BookNameMapper",
    "DEFAULT_TRANSLATION",
    "get_default_store",
]
