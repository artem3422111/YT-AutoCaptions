"""Воркер OAuth2-авторизации в фоновом потоке, не блокирует UI."""
from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal

from app.youtube_client import YouTubeClient


class AuthWorker(QThread):
    """Выполняет OAuth2-авторизацию YouTube в фоновом потоке."""

    succeeded = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._client = YouTubeClient()

    def run(self) -> None:
        try:
            self._client.build_client()
            channel = self._client.get_channel_info()
            name = channel["snippet"]["title"] if channel else "канал"
            self.succeeded.emit(name)
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))
