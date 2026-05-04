"""Audio master via ffmpeg loudnorm + optional sidechain ducking.

EBU R128 / -16 LUFS YouTube spec. Auphonic 우회 — 100% local ffmpeg.

진입점:
- measure_loudness(input) → dict
- master_audio(input, output, *, target_lufs=-16, true_peak=-1.5,
               lra=9, music_bed_path=None) → bool
- ensure_master(input, *, ...) → Path  (in-place 안전, 실패 시 원본 유지)
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Optional


def _ffmpeg_exe() -> str:
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def measure_loudness(input_path: Path | str) -> dict:
    """1-pass loudnorm 측정. dict 반환 (실패시 {})."""
    ff = _ffmpeg_exe()
    proc = subprocess.run(
        [ff, "-hide_banner", "-i", str(input_path),
         "-af", "loudnorm=I=-16:TP=-1.5:LRA=9:print_format=json",
         "-f", "null", "-"],
        capture_output=True, text=True, timeout=300,
    )
    text = proc.stderr or ""
    m = re.search(r'\{[^{}]*"input_i"[^{}]*\}', text, re.DOTALL)
    if not m:
        return {}
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return {}


def master_audio(
    input_path: Path | str,
    output_path: Path | str,
    *,
    target_lufs: float = -16.0,
    true_peak: float = -1.5,
    lra: float = 9.0,
    music_bed_path: Optional[Path] = None,
) -> bool:
    """Two-pass loudnorm. 옵션 sidechain ducking with music bed.

    Returns:
        True on verified success, False on any failure.
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    if not input_path.exists():
        return False

    measurements = measure_loudness(input_path)
    required = {"input_i", "input_tp", "input_lra",
                "input_thresh", "target_offset"}
    if not measurements or not required.issubset(measurements):
        return False

    ff = _ffmpeg_exe()
    cmd: list[str] = [ff, "-y", "-hide_banner", "-i", str(input_path)]

    loudnorm = (
        f"loudnorm=I={target_lufs}:TP={true_peak}:LRA={lra}:"
        f"measured_I={measurements['input_i']}:"
        f"measured_TP={measurements['input_tp']}:"
        f"measured_LRA={measurements['input_lra']}:"
        f"measured_thresh={measurements['input_thresh']}:"
        f"offset={measurements['target_offset']}:"
        f"linear=true:print_format=summary"
    )

    if music_bed_path and Path(music_bed_path).exists():
        cmd += ["-i", str(music_bed_path), "-filter_complex",
                f"[1:a][0:a]sidechaincompress=threshold=0.05:ratio=8:"
                f"attack=30:release=400[bed];"
                f"[0:a][bed]amix=inputs=2:weights=1.0 0.4[mix];"
                f"[mix]{loudnorm}[out]",
                "-map", "[out]"]
    else:
        cmd += ["-af", loudnorm]

    cmd += ["-c:a", "libmp3lame", "-b:a", "192k", str(output_path)]

    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if proc.returncode != 0 or not output_path.exists():
        return False

    verify = measure_loudness(output_path)
    try:
        actual = float(verify.get("input_i", "nan"))
    except (TypeError, ValueError):
        return False
    if abs(actual - target_lufs) > 1.0:
        return False
    return True


def ensure_master(
    path: Path | str,
    *,
    target_lufs: float = -16.0,
    true_peak: float = -1.5,
    lra: float = 9.0,
    music_bed_path: Optional[Path] = None,
) -> Path:
    """In-place 안전 마스터링. 실패 시 원본 그대로 반환."""
    path = Path(path)
    if not path.exists():
        return path
    tmp = path.with_name(path.stem + "_master" + path.suffix)
    ok = master_audio(path, tmp, target_lufs=target_lufs,
                      true_peak=true_peak, lra=lra,
                      music_bed_path=music_bed_path)
    if ok:
        path.unlink()
        tmp.rename(path)
    else:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass
    return path
