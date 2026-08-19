"""Воркер удаления музыки в отдельном потоке (QThread)."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from app.audio_tools import remove_music


class AudioWorker(QThread):
    """Удаляет музыку из видео в фоновом потоке, не блокируя UI."""

    progress = pyqtSignal(int, str)
    succeeded = pyqtSignal(str)
    failed = pyqtSignal(str)

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
