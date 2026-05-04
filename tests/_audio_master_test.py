"""apply_music_bed 기본 검증."""
import subprocess
from pathlib import Path

import pytest

CLIP = Path("/tmp/sermon-app/jobs/v4_test/trimmed_clip_0_60.mp3")
BEDS_DIR = Path("/tmp/sermon-app/app/render/music_beds")


@pytest.mark.skipif(not CLIP.exists(), reason="sermon clip not generated yet")
def test_reverent():
    from app.render.audio_master import apply_music_bed

    out = Path("/tmp/test_reverent.mp3")
    result = apply_music_bed(
        sermon_mp3=CLIP,
        mood="reverent",
        output=out,
        music_beds_dir=BEDS_DIR,
    )
    assert result.exists(), "output file not created"
    assert result.stat().st_size > 10_000, "output too small"

    # LUFS -16 ±1 검증
    proc = subprocess.run(
        ["ffmpeg", "-i", str(result),
         "-af", "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json",
         "-f", "null", "-"],
        capture_output=True, text=True,
    )
    import json, re
    m = re.search(r'\{[^{}]*"input_i"[^{}]*\}', proc.stderr, re.DOTALL)
    assert m, "loudnorm output not found"
    data = json.loads(m.group(0))
    lufs = float(data["input_i"])
    assert abs(lufs - (-16.0)) <= 1.5, f"LUFS {lufs} out of range"
