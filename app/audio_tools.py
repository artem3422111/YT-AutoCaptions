"""Удаление музыки через Demucs: оставляет голос и эффекты (vocals, other, drums)."""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

KEEP_STEMS = ["vocals", "other", "drums"]
DEMUCS_MODEL = "htdemucs_6s"


def remove_music(
    video_path: Path,
    out_path: Path,
    progress: callable | None = None,
    device: str = "auto",
) -> Path:
    """Убирает музыку, сохраняя голос и эффекты; возвращает итоговый файл."""
    if out_path is None or out_path == video_path:
        out_path = video_path.with_name(video_path.stem + "_vocals.mp4")

    def report(stage, pct):
        if progress:
            progress(stage, pct)

    report("Извлечение аудио…", 10)
    with tempfile.TemporaryDirectory(prefix="vocals_") as tmp:
        tmp_dir = Path(tmp)
        wav = tmp_dir / "audio.wav"

        _run([
            "ffmpeg", "-y", "-i", str(video_path),
            "-vn", "-ac", "2", "-ar", "44100", str(wav),
        ])

        report("Разделение голоса, эффектов и музыки (Demucs)…", 30)
        mix_wav = _demucs_mix(wav, device, KEEP_STEMS)

        report("Пересборка видео без музыки…", 85)
        _run([
            "ffmpeg", "-y", "-i", str(video_path),
            "-i", str(mix_wav),
            "-map", "0:v", "-map", "1:a",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            str(out_path),
        ])

    report("Готово!", 100)
    return out_path


def _demucs_mix(audio_wav: Path, device: str, keep_stems: list[str]) -> Path:
    """Разделяет на стемы и микширует указанные в единую WAV-дорожку."""
    cmd = _find_demucs()
    demucs_args = [
        *cmd, "-n", DEMUCS_MODEL,
        "--out", str(audio_wav.parent),
        str(audio_wav),
    ]
    if device == "cpu":
        demucs_args.append("-d")
        demucs_args.append("cpu")

    _run(demucs_args)

    result_dir = audio_wav.parent / DEMUCS_MODEL / audio_wav.stem
    stem_files: list[Path] = []
    for stem in keep_stems:
        cand = result_dir / f"{stem}.wav"
        if not cand.exists():
            for f in result_dir.glob(f"{stem}.*"):
                cand = f
                break
        if cand.exists():
            stem_files.append(cand)

    if not stem_files:
        raise RuntimeError("Demucs не создал нужные стемы")

    if len(stem_files) == 1:
        return stem_files[0]

    mix_out = audio_wav.parent / "mix.wav"
    inputs: list[str] = []
    for sf in stem_files:
        inputs += ["-i", str(sf)]
    _run([
        "ffmpeg", "-y", *inputs,
        "-filter_complex", (
            f"amix=inputs={len(stem_files)}:duration=first:dropout_transition=0"
        ),
        "-c:a", "pcm_s16le",
        str(mix_out),
    ])
    return mix_out


def _find_demucs() -> list[str]:
    """Возвращает команду запуска demucs."""
    import shutil

    bin_path = str(Path(sys.executable).parent / "demucs")
    if Path(bin_path).exists():
        return [bin_path]
    if shutil.which("demucs"):
        return ["demucs"]
    return [sys.executable, "-m", "demucs"]


def _run(cmd: list[str]) -> None:
    try:
        proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise SystemExit(f"❌ Не найдена команда: {cmd[0]}") from exc
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr[-2000:])
        raise SystemExit(f"❌ Команда не удалась: {cmd[0]}")
