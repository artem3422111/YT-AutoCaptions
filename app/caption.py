"""Авто-капшен: распознавание речи (faster-whisper) и встраивание karaoke-субтитров.

Активное слово подсвечивается жёлтым точно по таймкоду (ASS \\kf), остальные — белые.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

SPEED_FACTORS: dict[str, float] = {
    "tiny": 0.25,
    "base": 0.6,
    "small": 1.0,
    "medium": 3.0,
}
MODEL_LABELS: dict[str, str] = {
    "tiny": "Быстро (tiny)",
    "base": "Баланс (base)",
    "small": "Точно (small)",
    "medium": "Максимально (medium)",
}

COLOR_ACTIVE = "&H0000FFFF"
COLOR_PASSIVE = "&H00FFFFFF"


@dataclass
class Word:
    text: str
    start: float
    end: float


@dataclass
class Line:
    words: list[Word]

    @property
    def start(self) -> float:
        return self.words[0].start

    @property
    def end(self) -> float:
        return self.words[-1].end


def _srt_ts(seconds: float) -> str:
    """Секунды -> ASS-таймкод H:MM:SS.cc."""
    seconds = max(0.0, seconds)
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds % 1) * 100)
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def get_duration(video_path: Path) -> float:
    """Длительность видео в секундах через ffprobe."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)],
            capture_output=True, text=True, timeout=30,
        )
        return float(out.stdout.strip())
    except Exception:
        return 0.0


def estimate_time(video_path: Path, model: str) -> str:
    """Грубая оценка времени на наложение субтитров в удобном виде."""
    duration = get_duration(video_path)
    if duration <= 0:
        return "не удалось определить длительность"
    factor = SPEED_FACTORS.get(model, 1.0)
    work = duration * factor
    low = max(5.0, work * 0.6)
    high = max(8.0, work * 1.6)
    return _fmt_range(low, high)


def _fmt_range(low: float, high: float) -> str:
    """'~1–2 мин' или '~30–50 сек'."""
    if high < 90:
        return f"~{int(low)}–{int(high)} сек"
    return f"~{int(low/60)}–{int(high/60)} мин"

def caption_video(
    video: Path,
    model: str = "small",
    lang: str | None = "ru",
    font: str = "DejaVu Sans",
    font_size: int = 35,
    out: Path | None = None,
    progress: callable | None = None,
    keep: bool = False,
) -> Path:
    """Распознаёт речь и встраивает karaoke-субтитры; возвращает итоговый файл."""
    if out is None:
        out = video.with_name(video.stem + "_captioned.mp4")

    def report(stage, pct):
        if progress:
            progress(stage, pct)

    report("Извлечение аудио…", 10)
    with tempfile.TemporaryDirectory(prefix="autocap_") as tmp:
        tmp_dir = Path(tmp)
        wav = tmp_dir / "audio.wav"
        ass = tmp_dir / "subs.ass"

        extract_audio(video, wav)

        report(f"Распознавание речи (модель {model})…", 30)
        lines = transcribe(wav, model, lang)
        if not lines:
            raise RuntimeError("Речь не распознана — проверьте наличие звуковой дорожки.")

        report("Генерация субтитров (karaoke)…", 75)
        ass.write_text(build_ass(lines, font, font_size), encoding="utf-8")

        report("Встраивание субтитров в видео…", 85)
        burn_subtitles(video, ass, out)

        if keep:
            keep_dir = out.parent / (out.stem + "_subs")
            keep_dir.mkdir(exist_ok=True)
            (keep_dir / "subs.ass").write_text(
                ass.read_text(encoding="utf-8"), encoding="utf-8"
            )

    report("Готово!", 100)
    return out


def extract_audio(video_path: Path, out_wav: Path) -> None:
    """Извлекает аудио в WAV 16kHz моно (оптимально для Whisper)."""
    _run([
        "ffmpeg", "-y", "-i", str(video_path),
        "-vn", "-ac", "1", "-ar", "16000", str(out_wav),
    ])


def transcribe(audio_path: Path, model_size: str, lang: str | None) -> list[Line]:
    """Распознаёт речь, возвращая строки с по-словесными таймкодами."""
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise SystemExit(
            "❌ Не установлена утилита капшена.\n"
            "   Установите:  venv/bin/pip install -r requirements.txt"
        ) from exc

    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, _info = model.transcribe(
        str(audio_path), language=lang,
        word_timestamps=True, vad_filter=True,
    )

    lines: list[Line] = []
    for segment in segments:
        words = [
            Word((w.word or "").strip(), w.start, w.end)
            for w in (segment.words or [])
        ]
        if words:
            lines.append(Line(words))
    return lines


def build_ass(lines: list[Line], font: str, font_size: int) -> str:
    """Собирает ASS-файл: активное слово жёлтым, остальные белые, по центру."""
    MAX_CHARS = 30
    headers = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{font},{font_size},{COLOR_ACTIVE},{COLOR_PASSIVE},&H00101010,&HA0000000,-1,0,0,0,100,100,0,0,1,3,2,5,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events: list[str] = []
    for line in lines:
        for chunk in _split_by_chars(line, MAX_CHARS):
            events.append(_karaoke_event(chunk))
    return headers + "\n".join(events)


def _split_by_chars(line: Line, max_chars: int) -> list[Line]:
    """Разбивает строку на подстроки по количеству символов (не по словам)."""
    chunks: list[Line] = []
    current: list[Word] = []
    length = 0
    for word in line.words:
        add = len(word.text) + 1
        if current and length + add > max_chars:
            chunks.append(Line(current))
            current = []
            length = 0
        current.append(word)
        length += add
    if current:
        chunks.append(Line(current))
    return chunks


def _karaoke_event(line: Line) -> str:
    """Karaoke-событие: подсветка текущего слова жёлтым точно по времени."""
    pieces: list[str] = []
    for word in line.words:
        dur_ms = int((word.end - word.start) * 100)
        dur_ms = max(1, dur_ms)
        pieces.append(f"{{\\kf{dur_ms}}}{word.text}")
    body = " ".join(pieces)
    return (
        f"Dialogue: 0,{_srt_ts(line.start)},{_srt_ts(line.end)},"
        f"Default,,0,0,0,,{body}"
    )


def burn_subtitles(video_path: Path, ass_path: Path, out_path: Path) -> None:
    """Встраивает ASS-субтитры в видео (burn-in) через ffmpeg."""
    ass_s = str(ass_path).replace("\\", "/").replace(":", "\\:")
    _run([
        "ffmpeg", "-y", "-i", str(video_path),
        "-vf", f"subtitles={ass_s}",
        "-c:a", "copy", "-preset", "medium", "-crf", "19",
        str(out_path),
    ])


def _run(cmd: list[str]) -> None:
    try:
        proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    except FileNotFoundError as exc:
        raise SystemExit(f"❌ Не найдена команда: {cmd[0]}") from exc
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr[-2000:])
        raise SystemExit(f"❌ Команда не удалась: {cmd[0]}")

