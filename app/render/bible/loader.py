"""성경 본문 캐시 + 책명 매핑.

스키마:
{
  "translation": "krv",
  "language": "ko",
  "license": "사용자 자체 입력 — 저작권 확인 책임",
  "books": {
    "요한복음": {                       # ← 한국어 정식명 키
      "abbr": "요",
      "en":   "John",
      "chapters": {
        "3": {"16": "하나님이 세상을 …", "17": "…"}
      }
    },
    ...
  }
}
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

PKG_DIR = Path(__file__).resolve().parent
DEFAULT_TRANSLATION = os.getenv("SERMON_BIBLE_TRANS", "krv")


# 한국어 정식명 ↔ 영어 정식명 매핑 (66권)
# detect_scripture_refs와 일관 — scripture.py BOOKS_KO 참조
KO_TO_EN: dict[str, str] = {
    "창세기": "Genesis", "출애굽기": "Exodus", "레위기": "Leviticus",
    "민수기": "Numbers", "신명기": "Deuteronomy",
    "여호수아": "Joshua", "사사기": "Judges", "룻기": "Ruth",
    "사무엘상": "1 Samuel", "사무엘하": "2 Samuel",
    "열왕기상": "1 Kings", "열왕기하": "2 Kings",
    "역대상": "1 Chronicles", "역대하": "2 Chronicles",
    "에스라": "Ezra", "느헤미야": "Nehemiah", "에스더": "Esther",
    "욥기": "Job", "시편": "Psalms", "잠언": "Proverbs",
    "전도서": "Ecclesiastes", "아가": "Song of Solomon",
    "이사야": "Isaiah", "예레미야": "Jeremiah",
    "예레미야애가": "Lamentations", "에스겔": "Ezekiel", "다니엘": "Daniel",
    "호세아": "Hosea", "요엘": "Joel", "아모스": "Amos", "오바댜": "Obadiah",
    "요나": "Jonah", "미가": "Micah", "나훔": "Nahum", "하박국": "Habakkuk",
    "스바냐": "Zephaniah", "학개": "Haggai", "스가랴": "Zechariah", "말라기": "Malachi",
    "마태복음": "Matthew", "마가복음": "Mark", "누가복음": "Luke", "요한복음": "John",
    "사도행전": "Acts",
    "로마서": "Romans", "고린도전서": "1 Corinthians", "고린도후서": "2 Corinthians",
    "갈라디아서": "Galatians", "에베소서": "Ephesians",
    "빌립보서": "Philippians", "골로새서": "Colossians",
    "데살로니가전서": "1 Thessalonians", "데살로니가후서": "2 Thessalonians",
    "디모데전서": "1 Timothy", "디모데후서": "2 Timothy",
    "디도서": "Titus", "빌레몬서": "Philemon",
    "히브리서": "Hebrews", "야고보서": "James",
    "베드로전서": "1 Peter", "베드로후서": "2 Peter",
    "요한일서": "1 John", "요한이서": "2 John", "요한삼서": "3 John",
    "유다서": "Jude", "요한계시록": "Revelation",
}
EN_TO_KO: dict[str, str] = {v: k for k, v in KO_TO_EN.items()}


class BookNameMapper:
    @staticmethod
    def to_english(book_ko: str) -> Optional[str]:
        return KO_TO_EN.get(book_ko)

    @staticmethod
    def to_korean(book_en: str) -> Optional[str]:
        return EN_TO_KO.get(book_en)


class BibleStore:
    """JSON 한 개 = 한 번역본. 책명 키는 정식 한글 또는 정식 영어."""

    def __init__(self, json_path: Path):
        self.path = Path(json_path)
        self._data: Optional[dict] = None

    def load(self) -> dict:
        if self._data is None:
            if not self.path.exists():
                self._data = {"translation": self.path.stem, "books": {}}
            else:
                self._data = json.loads(self.path.read_text(encoding="utf-8"))
        return self._data

    @property
    def translation(self) -> str:
        return self.load().get("translation", self.path.stem)

    @property
    def language(self) -> str:
        return self.load().get("language", "?")

    def is_empty(self) -> bool:
        return not bool(self.load().get("books"))

    def lookup(
        self, book: str, chapter: int, verse_start: int,
        verse_end: Optional[int] = None,
    ) -> Optional[str]:
        """book(한글 또는 영문) + 장:절 → 본문. 없으면 None."""
        data = self.load()
        books = data.get("books") or {}
        rec = books.get(book)
        if rec is None:
            # 한↔영 양방향 시도
            alt = KO_TO_EN.get(book) or EN_TO_KO.get(book)
            if alt:
                rec = books.get(alt)
        if rec is None:
            return None
        chapters = rec.get("chapters") or {}
        ch = chapters.get(str(chapter)) or chapters.get(chapter)
        if ch is None:
            return None
        ve = verse_end if verse_end and verse_end > verse_start else verse_start
        parts: list[str] = []
        for v in range(verse_start, ve + 1):
            t = ch.get(str(v)) or ch.get(v)
            if t:
                parts.append(t.strip())
        if not parts:
            return None
        return " ".join(parts)


@lru_cache(maxsize=4)
def get_default_store(translation: str = DEFAULT_TRANSLATION) -> BibleStore:
    """프로세스 캐시 — 같은 번역본 한 번만 로드."""
    return BibleStore(PKG_DIR / f"{translation}.json")
