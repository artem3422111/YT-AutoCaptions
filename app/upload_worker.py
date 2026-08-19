"""Воркер загрузки видео в отдельном потоке (QThread).

Позволяет не блокировать UI во время медленной загрузки файла на YouTube.
Общается с интерфейсом через сигналы: progress, finished, error.
"""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from app.youtube_client import UploadResult, YouTubeClient


class UploadWorker(QThread):
    """Выполняет загрузку одного видео/шортса в фоновом потоке."""

    progress = pyqtSignal(int, str)      # (percent, message)
    succeeded = pyqtSignal(object)       # UploadResult
    failed = pyqtSignal(str)             # сообщение об ошибке

    def __init__(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: list[str],
        category_id: str,
        privacy: str,
        thumbnail_path: str | None = None,
        made_for_kids: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._video_path = video_path
        self._title = title
        self._description = description
        self._tags = tags
        self._category_id = category_id
        self._privacy = privacy
        self._thumbnail_path = thumbnail_path
        self._made_for_kids = made_for_kids
        self._client = YouTubeClient()

    def run(self) -> None:
        try:
            result: UploadResult = self._client.upload_video(
                video_path=self._video_path,
                title=self._title,
                description=self._description,
                tags=self._tags,
                category_id=self._category_id,
                privacy=self._privacy,
                thumbnail_path=self._thumbnail_path,
                made_for_kids=self._made_for_kids,
                progress_callback=self._emit_progress,
            )
            self.succeeded.emit(result)
        except Exception as exc:  # noqa: BLE001 — показываем любую ошибку пользователю
            self.failed.emit(str(exc))

    def _emit_progress(self, percent: int, message: str) -> None:
        self.progress.emit(int(percent), message)
