"""Воркер авторизации в фоновом потоке (QThread).

OAuth2-flow запускает локальный сервер и ждёт ответа в браузере — это может
занять много времени. Чтобы не блокировать главный поток (что вызывало
зависание окна при нажатии крестика), авторизация выполняется здесь.
"""
from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal

from app.youtube_client import YouTubeClient


class AuthWorker(QThread):
    """Выполняет OAuth2-авторизацию YouTube в фоновом потоке."""

    succeeded = pyqtSignal(str)   # имя канала после успешной авторизации
    failed = pyqtSignal(str)      # сообщение об ошибке (включая 403 access_denied)

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
