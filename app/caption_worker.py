"""Воркер капшена в отдельном потоке (QThread).

Распознавание речи и встраивание субтитров — длительная операция, поэтому
выполняется в фоне. UI общается через сигналы progress / succeeded / failed.
"""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from app import caption as cap


class CaptionWorker(QThread):
    """Накладывает karaoke-субтитры на видео в фоновом потоке."""

    progress = pyqtSignal(int, str)   # (percent, message)
    succeeded = pyqtSignal(str)       # путь к итоговому файлу
    failed = pyqtSignal(str)          # сообщение об ошибке

    def __init__(
        self,
        video_path: str,
        model: str,
        lang: str | None,
        font: str,
        font_size: int,
        out_path: str | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._video = Path(video_path)
        self._out = Path(out_path) if out_path else None
        self._model = model
        self._lang = lang
        self._font = font
        self._font_size = font_size

    def run(self) -> None:
        try:
            result = cap.caption_video(
                video=self._video,
                model=self._model,
                lang=self._lang,
                font=self._font,
                font_size=self._font_size,
                out=self._out,
                progress=self._emit_progress,
            )
            self.succeeded.emit(str(result))
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))

    def _emit_progress(self, stage: str, pct: int) -> None:
        self.progress.emit(int(pct), stage)
