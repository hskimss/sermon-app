"""스모크 테스트:
1) detect_scripture_refs 동작
2) build_short_payload — 실 transcript로 60초 클립 payload 생성
3) sermon_short_v1.html placeholder 무결성
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from app.render import build_short_payload, detect_scripture_refs
from app.render.scripture import list_supported_books


def find_a_job(jobs_dir: Path) -> str | None:
    """transcript.json + words[]가 채워진 job 1개 자동 선택."""
    for d in sorted(jobs_dir.iterdir()):
        tp = d / "transcript.json"
        if not tp.exists():
            continue
        try:
            t = json.loads(tp.read_text())
        except Exception:
            continue
        segs = t.get("segments") or []
        if segs and segs[0].get("words"):
            return d.name
    return None


def main() -> int:
    jobs_dir = ROOT / "jobs"
    job_id = find_a_job(jobs_dir)
    if not job_id:
        print("[FAIL] words[] 포함된 transcript 없음")
        return 1
    print(f"[INFO] 테스트 대상 job: {job_id}")

    # 1) Scripture detect
    fake = {
        "segments": [
            {"start": 0, "end": 5, "text": "오늘은 요한복음 3:16 말씀입니다", "words": []},
            {"start": 5, "end": 10, "text": "마태복음 5장 3절도 함께 보겠습니다", "words": []},
            {"start": 10, "end": 15, "text": "롬 8:28을 잊지 맙시다", "words": []},
        ]
    }
    refs = detect_scripture_refs(fake)
    print(f"[OK] detect_scripture_refs: {len(refs)}개 검출")
    for r in refs:
        print(f"     · {r['book']} {r['chapter']}:{r['verse_start']}-{r['verse_end']}"
              f"  @ {r['appears_at_sec']}s  ({r['matched_text']})")
    expected_books = {"요한복음", "마태복음", "로마서"}
    got = {r["book"] for r in refs}
    if not expected_books.issubset(got):
        print(f"[FAIL] 기대 책 {expected_books} != 실제 {got}")
        return 1
    print(f"[OK] {len(list(list_supported_books()))}권 지원 (66권 목표)")

    # 2) Payload builder
    payload = build_short_payload(
        job_id=job_id,
        clip={"start_sec": 0.0, "end_sec": 60.0, "hook_archetype": "test"},
        jobs_dir=jobs_dir,
    )
    required = {"composition", "format", "quality", "house_style", "audio_url",
                "audio_clip", "clip_range", "words", "transcript_segments",
                "scripture_refs", "meta"}
    missing = required - set(payload.keys())
    if missing:
        print(f"[FAIL] payload 키 누락: {missing}")
        return 1
    print(f"[OK] payload 키 {len(payload)}개 모두 존재")
    print(f"     composition={payload['composition']} format={payload['format']}")
    print(f"     audio_clip={payload['audio_clip']}")
    print(f"     words={len(payload['words'])}개  segments={len(payload['transcript_segments'])}개")
    print(f"     scripture_refs={len(payload['scripture_refs'])}개")

    # 시각 정합성 — words.start/end가 모두 0..duration 내
    duration = payload["audio_clip"]["duration"]
    bad = [w for w in payload["words"] if w["start"] < 0 or w["end"] > duration + 0.5]
    if bad:
        print(f"[FAIL] clip-local 시각 범위 벗어남: {len(bad)}개")
        return 1
    print(f"[OK] 모든 word.start/end 가 [0, {duration:.1f}s] 안")

    # emphasis flag 무결성
    n_emp = sum(1 for w in payload["words"] if w["is_emphasis"])
    print(f"[INFO] is_emphasis=true 단어: {n_emp}개 (llm_emphasis.json 캐시 적용 여부에 따라 변동)")

    # 3) Composition HTML placeholder 검증
    html_path = ROOT / "app/render/compositions/sermon_short_v1.html"
    html = html_path.read_text()
    placeholders = set(re.findall(r"\{\{[A-Z_]+\}\}", html))
    expected_placeholders = {
        "{{COMPOSITION_ID}}", "{{DURATION_MS}}",
        "{{SCRIPTURE_REF}}", "{{SCRIPTURE_TEXT}}", "{{SCRIPTURE_TRANS}}",
        "{{CHANNEL}}", "{{WORDS_JSON}}", "{{SCRIPTURE_REFS_JSON}}",
        "{{TOTAL_SEC}}",
    }
    miss = expected_placeholders - placeholders
    if miss:
        print(f"[FAIL] 템플릿 placeholder 누락: {miss}")
        return 1
    print(f"[OK] sermon_short_v1.html — placeholder {len(placeholders)}개 모두 존재")

    # HyperFrames 핵심 lint
    for needle in ("data-composition-id", "window.__timelines",
                   "window.__hyperframes_ready"):
        if needle not in html:
            print(f"[FAIL] HyperFrames lint — '{needle}' 누락")
            return 1
    print("[OK] HyperFrames lint 통과 (composition-id, __timelines, __hyperframes_ready)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
