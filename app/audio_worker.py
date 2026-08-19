"""Воркер удаления музыки в отдельном потоке (QThread).

Разделение голос/музыка через Demucs — длительная операция, выполняется в фоне.
UI общается через сигналы progress / succeeded / failed.
"""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from app.audio_tools import remove_music


class AudioWorker(QThread):
    """Удаляет музыку из видео (оставляя голос) в фоновом потоке."""

    progress = pyqtSignal(int, str)   # (percent, message)
    succeeded = pyqtSignal(str)       # путь к итоговому файлу
    failed = pyqtSignal(str)          # сообщение об ошибке

    def __init__(
        self,
        video_path: str,
        out_path: str | None = None,
        device: str = "auto",
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._video = Path(video_path)
        self._out = Path(out_path) if out_path else None
        self._device = device

    def run(self) -> None:
        try:
            result = remove_music(
                video_path=self._video,
                out_path=self._out,
                progress=self._emit_progress,
                device=self._device,
            )
            self.succeeded.emit(str(result))
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))

    def _emit_progress(self, stage: str, pct: int) -> None:
        self.progress.emit(int(pct), stage)
