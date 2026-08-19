"""Вкладка «Видео» — загрузка обычных видео (горизонтальный формат 16:9)."""
from __future__ import annotations

from app.widgets.upload_form import UploadForm


class VideoTab(UploadForm):
    """Форма загрузки обычного видео."""

    def __init__(self, parent=None) -> None:
        super().__init__(is_shorts=False, parent=parent)
