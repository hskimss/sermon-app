"""성구 인용 검출 (P3 prelim — regex 1차).

`(책명) (장)[장: ] (절)[절]?` 패턴.
- 명시적: "요한복음 3:16", "요 3:16", "마태복음 5장 3절"
- 약식 ("성경에 보면…")은 Gemma 4 보강 단계에서 처리 (P3 본 단계)
"""
from __future__ import annotations

import re
from typing import Iterable

# 한국어 성경 66권 정식명 + 약칭 (필요 시 확장)
BOOKS_KO: dict[str, str] = {
    # 모세오경
    "창세기": "창세기", "창": "창세기",
    "출애굽기": "출애굽기", "출": "출애굽기",
    "레위기": "레위기", "레": "레위기",
    "민수기": "민수기", "민": "민수기",
    "신명기": "신명기", "신": "신명기",
    # 역사서
    "여호수아": "여호수아", "수": "여호수아",
    "사사기": "사사기", "삿": "사사기",
    "룻기": "룻기", "룻": "룻기",
    "사무엘상": "사무엘상", "삼상": "사무엘상",
    "사무엘하": "사무엘하", "삼하": "사무엘하",
    "열왕기상": "열왕기상", "왕상": "열왕기상",
    "열왕기하": "열왕기하", "왕하": "열왕기하",
    "역대상": "역대상", "대상": "역대상",
    "역대하": "역대하", "대하": "역대하",
    "에스라": "에스라", "스": "에스라",
    "느헤미야": "느헤미야", "느": "느헤미야",
    "에스더": "에스더", "에": "에스더",
    # 시가서
    "욥기": "욥기", "욥": "욥기",
    "시편": "시편", "시": "시편",
    "잠언": "잠언", "잠": "잠언",
    "전도서": "전도서", "전": "전도서",
    "아가": "아가", "아": "아가",
    # 대선지서
    "이사야": "이사야", "사": "이사야",
    "예레미야": "예레미야", "렘": "예레미야",
    "예레미야애가": "예레미야애가", "애": "예레미야애가",
    "에스겔": "에스겔", "겔": "에스겔",
    "다니엘": "다니엘", "단": "다니엘",
    # 소선지서
    "호세아": "호세아", "호": "호세아",
    "요엘": "요엘", "욜": "요엘",
    "아모스": "아모스", "암": "아모스",
    "오바댜": "오바댜", "옵": "오바댜",
    "요나": "요나", "욘": "요나",
    "미가": "미가", "미": "미가",
    "나훔": "나훔", "나": "나훔",
    "하박국": "하박국", "합": "하박국",
    "스바냐": "스바냐", "습": "스바냐",
    "학개": "학개", "학": "학개",
    "스가랴": "스가랴", "슥": "스가랴",
    "말라기": "말라기", "말": "말라기",
    # 4복음서
    "마태복음": "마태복음", "마": "마태복음",
    "마가복음": "마가복음", "막": "마가복음",
    "누가복음": "누가복음", "눅": "누가복음",
    "요한복음": "요한복음", "요": "요한복음",
    "사도행전": "사도행전", "행": "사도행전",
    # 바울서신
    "로마서": "로마서", "롬": "로마서",
    "고린도전서": "고린도전서", "고전": "고린도전서",
    "고린도후서": "고린도후서", "고후": "고린도후서",
    "갈라디아서": "갈라디아서", "갈": "갈라디아서",
    "에베소서": "에베소서", "엡": "에베소서",
    "빌립보서": "빌립보서", "빌": "빌립보서",
    "골로새서": "골로새서", "골": "골로새서",
    "데살로니가전서": "데살로니가전서", "살전": "데살로니가전서",
    "데살로니가후서": "데살로니가후서", "살후": "데살로니가후서",
    "디모데전서": "디모데전서", "딤전": "디모데전서",
    "디모데후서": "디모데후서", "딤후": "디모데후서",
    "디도서": "디도서", "딛": "디도서",
    "빌레몬서": "빌레몬서", "몬": "빌레몬서",
    "히브리서": "히브리서", "히": "히브리서",
    # 일반서신/계시록
    "야고보서": "야고보서", "약": "야고보서",
    "베드로전서": "베드로전서", "벧전": "베드로전서",
    "베드로후서": "베드로후서", "벧후": "베드로후서",
    "요한일서": "요한일서", "요일": "요한일서",
    "요한이서": "요한이서", "요이": "요한이서",
    "요한삼서": "요한삼서", "요삼": "요한삼서",
    "유다서": "유다서", "유": "유다서",
    "요한계시록": "요한계시록", "계": "요한계시록",
}

# 우선순위 정렬: 긴 이름 먼저(빌립보서 vs 빌)
_BOOK_ALT = sorted(BOOKS_KO.keys(), key=len, reverse=True)
_BOOK_RE = "|".join(re.escape(b) for b in _BOOK_ALT)

# 패턴 1: "요한복음 3:16" / "요한복음3:16" / "요 3:16-17"
_PAT_COLON = re.compile(
    rf"(?P<book>{_BOOK_RE})\s*(?P<chap>\d+)\s*:\s*(?P<vs>\d+)(?:\s*[~\-–—]\s*(?P<ve>\d+))?"
)
# 패턴 2: "요한복음 3장 16절" / "마태복음 5장 3-12절"
_PAT_KOREAN = re.compile(
    rf"(?P<book>{_BOOK_RE})\s*(?P<chap>\d+)\s*장\s*(?P<vs>\d+)(?:\s*[~\-–—]\s*(?P<ve>\d+))?\s*절?"
)


def detect_scripture_refs(
    transcript: dict, clip: dict | None = None
) -> list[dict]:
    """transcript 내에서 성구 인용을 검출.

    Args:
        transcript: {"segments": [{"start","end","text","words":[...]}]}
        clip: {"start_sec","end_sec"} — 주어지면 이 범위만 검출

    Returns:
        [
          {"book","chapter","verse_start","verse_end","appears_at_sec",
           "matched_text","seg_idx"},
          ...
        ]
    """
    in_s = float(clip["start_sec"]) if clip else 0.0
    out_s = float(clip["end_sec"]) if clip else float("inf")

    refs: list[dict] = []
    seen: set[tuple] = set()  # 동일 인용 dedup

    for sIdx, seg in enumerate(transcript.get("segments", []) or []):
        s_start = float(seg.get("start", 0))
        s_end = float(seg.get("end", 0))
        if s_end < in_s or s_start > out_s:
            continue
        text = seg.get("text", "") or ""

        for pat in (_PAT_COLON, _PAT_KOREAN):
            for m in pat.finditer(text):
                book_raw = m.group("book")
                chap = int(m.group("chap"))
                vs = int(m.group("vs"))
                ve = int(m.group("ve")) if m.group("ve") else vs
                book = BOOKS_KO.get(book_raw, book_raw)
                key = (book, chap, vs, ve)
                if key in seen:
                    continue
                seen.add(key)
                # appears_at_sec: 클립 시작 기준 상대 시각
                appears_at = max(0.0, s_start - in_s)
                refs.append({
                    "book": book,
                    "chapter": chap,
                    "verse_start": vs,
                    "verse_end": ve,
                    "appears_at_sec": round(appears_at, 2),
                    "matched_text": m.group(0),
                    "seg_idx": sIdx,
                })
    refs.sort(key=lambda r: r["appears_at_sec"])
    return refs


def list_supported_books() -> Iterable[str]:
    return sorted(set(BOOKS_KO.values()))
