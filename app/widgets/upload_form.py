"""Базовый виджет формы загрузки видео/шортсов: выбор файла, детали, превью."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.config import config
from app.audio_worker import AudioWorker
from app.upload_worker import UploadWorker
from app.youtube_client import UploadResult

VIDEO_EXTENSIONS = (
    "Видеофайлы (*.mp4 *.mov *.avi *.mkv *.webm *.m4v *.flv *.wmv *.3gp *.mpeg "
    "*.mpg *.ts);;Все файлы (*)"
)
IMAGE_EXTENSIONS = (
    "Изображения (*.jpg *.jpeg *.png *.webp *.gif);;Все файлы (*)"
)


class UploadForm(QWidget):
    """Общая форма для загрузки видео и шортсов."""

    def __init__(self, is_shorts: bool = False, parent=None) -> None:
        super().__init__(parent)
        self.is_shorts = is_shorts
        self._video_path: Path | None = None
        self._thumbnail_path: Path | None = None
        self._worker: UploadWorker | None = None
        self._audio_worker: AudioWorker | None = None
        self._current_upload_path: Path | None = None

        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        layout.addWidget(self._build_header())

        anime_card = self._build_anime_card()
        if anime_card is not None:
            layout.addWidget(anime_card)

        layout.addWidget(self._build_file_card())

        layout.addWidget(self._build_details_card())

        layout.addWidget(self._build_settings_card())

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("", self)
        self.status_label.setObjectName("statusLabel")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.upload_btn = QPushButton(
            "⬆  Загрузить шортс на YouTube" if self.is_shorts else
            "⬆  Загрузить видео на YouTube",
            self,
        )
        self.upload_btn.setObjectName("accentButton")
        self.upload_btn.setMinimumHeight(46)
        self.upload_btn.clicked.connect(self._on_upload_clicked)
        self.upload_btn.setEnabled(False)
        layout.addWidget(self.upload_btn)

        layout.addStretch(1)

    def _build_header(self) -> QWidget:
        header = QWidget(self)
        v = QVBoxLayout(header)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(4)

        title = QLabel(
            "Загрузка шортса" if self.is_shorts else "Загрузка видео", header
        )
        title.setObjectName("titleLabel")

        subtitle = QLabel(
            "Выберите видеофайл и заполните детали публикации.", header
        )
        subtitle.setObjectName("subtitleLabel")

        v.addWidget(title)
        v.addWidget(subtitle)
        return header

    def _build_file_card(self) -> QGroupBox:
        box = QGroupBox("Видеофайл", self)
        grid = QGridLayout(box)
        grid.setContentsMargins(14, 16, 14, 14)
        grid.setSpacing(10)

        self.file_path_edit = QLineEdit(box)
        self.file_path_edit.setPlaceholderText(
            "Файл не выбран — нажмите «Выбрать файл»"
        )
        self.file_path_edit.setReadOnly(True)
        grid.addWidget(self.file_path_edit, 0, 0, 1, 2)

        self.choose_btn = QPushButton("📂  Выбрать файл", box)
        self.choose_btn.setObjectName("chooseFileButton")
        self.choose_btn.clicked.connect(self._choose_video_file)
        grid.addWidget(self.choose_btn, 0, 2)

        self.file_name_label = QLabel("", box)
        self.file_name_label.setObjectName("fileNameLabel")
        grid.addWidget(self.file_name_label, 1, 0, 1, 3)

        return box

    def _build_details_card(self) -> QGroupBox:
        box = QGroupBox("Детали публикации", self)
        grid = QGridLayout(box)
        grid.setContentsMargins(14, 16, 14, 14)
        grid.setSpacing(10)
        grid.setColumnStretch(1, 1)

        grid.addWidget(self._field_label("Название *"), 0, 0)
        self.title_edit = QLineEdit(box)
        self.title_edit.setPlaceholderText("Введите название видео")
        self.title_edit.setMaxLength(100)
        self.title_edit.textChanged.connect(self._update_upload_state)
        grid.addWidget(self.title_edit, 0, 1, 1, 2)

        grid.addWidget(self._field_label("Описание"), 1, 0)
        self.desc_edit = QPlainTextEdit(box)
        self.desc_edit.setPlaceholderText("Расскажите, о чём это видео…")
        self.desc_edit.setMaximumHeight(120)
        grid.addWidget(self.desc_edit, 1, 1, 1, 2)

        grid.addWidget(self._field_label("Теги"), 2, 0)
        self.tags_edit = QLineEdit(box)
        self.tags_edit.setPlaceholderText("через запятую: python, туториал, ютуб")
        grid.addWidget(self.tags_edit, 2, 1, 1, 2)

        grid.addWidget(self._field_label("Категория"), 3, 0)
        self.category_combo = QComboBox(box)
        self.category_combo.addItem("People & Blogs", "22")
        grid.addWidget(self.category_combo, 3, 1)

        hint = QLabel(
            "Для шортсов YouTube рекомендует категорию «Films & Animation».",
            box,
        )
        hint.setObjectName("mutedLabel")
        hint.setWordWrap(True)
        if not self.is_shorts:
            hint.hide()
        grid.addWidget(hint, 3, 2)

        return box


    def _build_settings_card(self) -> QGroupBox:
        box = QGroupBox("Настройки публикации", self)
        grid = QGridLayout(box)
        grid.setContentsMargins(14, 16, 14, 14)
        grid.setSpacing(10)
        grid.setColumnStretch(1, 1)

        grid.addWidget(self._field_label("Видимость"), 0, 0)
        self.privacy_combo = QComboBox(box)
        for label, value in (
            ("Приватно", "private"),
            ("Не перечислено", "unlisted"),
            ("Публично", "public"),
        ):
            self.privacy_combo.addItem(label, value)
        grid.addWidget(self.privacy_combo, 0, 1, 1, 2)

        grid.addWidget(self._field_label("Превью (мин. 1280×720)"), 1, 0)
        self.thumbnail_edit = QLineEdit(box)
        self.thumbnail_edit.setPlaceholderText("Необязательно")
        self.thumbnail_edit.setReadOnly(True)
        grid.addWidget(self.thumbnail_edit, 1, 1)

        self.thumbnail_btn = QPushButton("Выбрать", box)
        self.thumbnail_btn.clicked.connect(self._choose_thumbnail)
        grid.addWidget(self.thumbnail_btn, 1, 2)

        self.kids_check = QCheckBox("Это видео для детей", box)
        grid.addWidget(self.kids_check, 2, 1, 1, 2)

        self.no_music_check = QCheckBox(
            "🎵 Убрать музыку (оставить голос и эффекты)", box
        )
        self.no_music_check.setToolTip(
            "Перед загрузкой видео прогоняется через Demucs: музыка убирается, "
            "голос/озвучка сохраняются. Заметно снижает риск бана за авторские права "
            "на музыку/саундтрек."
        )
        grid.addWidget(self.no_music_check, 3, 1, 1, 2)

        return box

    @staticmethod
    def _field_label(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        return label

    def _build_anime_card(self):
        """Возвращает виджет с шаблоном, либо None (обычное видео)."""
        return None

    def _apply_auto_template(self) -> None:
        """Заполняет название/описание/теги по шаблону (наследники)."""
        pass


    def _choose_video_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите видеофайл", str(Path.home()), VIDEO_EXTENSIONS
        )
        if not file_path:
            return
        self.set_video_file(file_path)

    def set_video_file(self, file_path: str) -> None:
        """Устанавливает выбранный видеофайл и подставляет название из имени."""
        path = Path(file_path)
        if not path.exists():
            self._set_status(f"Файл не найден: {path}", error=True)
            return

        self._video_path = path
        self.file_path_edit.setText(str(path))

        if not self.title_edit.text().strip():
            self.title_edit.setText(path.stem.replace("_", " ").replace("-", " "))

        self.file_name_label.setText(f"✓ {path.name} ({self._format_size(path)})")
        self._update_upload_state()

    def _choose_thumbnail(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите превью (thumbnail)", str(Path.home()), IMAGE_EXTENSIONS
        )
        if not file_path:
            return
        self._thumbnail_path = Path(file_path)
        self.thumbnail_edit.setText(file_path)

    @staticmethod
    def _format_size(path: Path) -> str:
        size = path.stat().st_size
        for unit in ("Б", "КБ", "МБ", "ГБ"):
            if size < 1024:
                return f"{size:.0f} {unit}"
            size /= 1024
        return f"{size:.1f} ТБ"

    def _update_upload_state(self) -> None:
        has_video = self._video_path is not None
        has_title = bool(self.title_edit.text().strip())
        self.upload_btn.setEnabled(has_video and has_title)

    def _validate(self) -> str | None:
        """Возвращает текст ошибки или None, если всё валидно."""
        if self._video_path is None:
            return "Пожалуйста, выберите видеофайл."
        if not self.title_edit.text().strip():
            return "Введите название видео."
        if self.is_shorts:
            return self._validate_shorts_duration()
        return None

    def _validate_shorts_duration(self) -> str | None:
        """Показывает предупреждение для шортсов, но не блокирует загрузку."""
        try:
            duration = self._probe_video_duration()
        except Exception:
            return None
        if duration is not None and duration > 180:
            self._set_status(
                f"⚠️ Внимание: длительность видео {duration:.0f}с. "
                "YouTube Shorts поддерживают до 60 секунд (классика) или до 3 минут.",
                warn=True,
            )
        return None

    def _probe_video_duration(self) -> float | None:
        """Пытается определить длительность видео через встроенный ffprobe."""
        import shutil
        import subprocess

        ffprobe = shutil.which("ffprobe")
        if not ffprobe:
            return None
        try:
            out = subprocess.check_output(
                [
                    ffprobe,
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    str(self._video_path),
                ],
                timeout=30,
            )
            return float(out.decode().strip())
        except Exception:
            return None


    def _on_upload_clicked(self) -> None:
        error = self._validate()
        if error:
            self._set_status(error, error=True)
            return

        self._set_busy(True, "Подготовка к загрузке…")
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self._set_status("")

        if self.no_music_check.isChecked():
            self._prepare_music_removal()
        else:
            self._start_upload(self._video_path)

    def _prepare_music_removal(self) -> None:
        """Удаляет музыку (Demucs) во временный файл, затем грузит обработанный."""
        out_path = Path(tempfile.gettempdir()) / (
            self._video_path.stem + "_vocals.mp4"
        )
        self._set_status("🎵 Удаляем музыку (голос останется)…")

        self._audio_worker = AudioWorker(
            video_path=str(self._video_path),
            out_path=str(out_path),
            parent=self,
        )
        self._audio_worker.progress.connect(self._on_progress)
        self._audio_worker.succeeded.connect(self._on_music_done)
        self._audio_worker.failed.connect(self._on_music_failed)
        self._audio_worker.start()

    def _on_music_done(self, processed_path: str) -> None:
        """Демucs готов — грузим обработанное видео."""
        self._start_upload(Path(processed_path))

    def _on_music_failed(self, message: str) -> None:
        self._set_busy(False)
        self.progress_bar.hide()
        self._set_status(f"Ошибка удаления музыки: {message}", error=True)

    def _start_upload(self, video_path: Path) -> None:
        """Запускает загрузку конкретного видеофайла на YouTube."""
        self._current_upload_path = Path(video_path)
        self._worker = UploadWorker(
            video_path=str(self._current_upload_path),
            title=self.title_edit.text().strip(),
            description=self.desc_edit.toPlainText().strip(),
            tags=self._parse_tags(self.tags_edit.text()),
            category_id=str(self.category_combo.currentData()),
            privacy=str(self.privacy_combo.currentData()),
            thumbnail_path=(
                str(self._thumbnail_path) if self._thumbnail_path else None
            ),
            made_for_kids=self.kids_check.isChecked(),
            parent=self,
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.succeeded.connect(self._on_success)
        self._worker.failed.connect(self._on_failure)
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()

    def _parse_tags(self, raw: str) -> list[str]:
        return [t.strip() for t in raw.split(",") if t.strip()][:100]

    def shutdown(self) -> None:
        """Корректно останавливает активные воркеры при закрытии окна.

        Даёт потокам шанс завершиться мягко; если сетевой запрос «залип» —
        использует жёсткую остановку, чтобы приложение не зависло на закрытии.
        """
        for worker in (self._worker, self._audio_worker):
            if worker is not None and worker.isRunning():
                worker.requestInterruption()
                if not worker.wait(3000):
                    worker.terminate()
                    worker.wait(1000)


    def _on_progress(self, percent: int, message: str) -> None:
        self.progress_bar.setValue(percent)
        self._set_status(f"{message} ({percent}%)")
        if percent >= 100:
            self.progress_bar.hide()

    def _on_success(self, result: UploadResult) -> None:
        self._set_status(f"🎉 Видео загружено: {result.title}")
        self.status_label.setText(
            f"🎉 Видео загружено: {result.title}\nСсылка: {result.url}"
        )
        self.status_label.setObjectName("fileNameLabel")
        self.status_label.setStyleSheet(
            f"color: {PALETTE_SUCCESS}; font-weight: 600;"
        )

    def _on_failure(self, message: str) -> None:
        self._set_status(f"Ошибка загрузки: {message}", error=True)
        self.progress_bar.hide()

    def _on_worker_finished(self) -> None:
        self._set_busy(False)

    def _set_busy(self, busy: bool, message: str = "") -> None:
        self.upload_btn.setEnabled(not busy)
        self.choose_btn.setEnabled(not busy)
        self.thumbnail_btn.setEnabled(not busy)
        if message:
            self._set_status(message)

    def _set_status(self, message: str, error: bool = False, warn: bool = False) -> None:
        self.status_label.setObjectName(
            "errorLabel" if error else (
                "warnLabel" if warn else "statusLabel"
            )
        )
        color = PALETTE_ERROR if error else (PALETTE_WARN if warn else PALETTE_TEXT_MUTED)
        self.status_label.setStyleSheet(f"color: {color};")
        self.status_label.setText(message)


from app.theme import Palette as _Palette  # noqa: E402

PALETTE_SUCCESS = _Palette.SUCCESS
PALETTE_ERROR = _Palette.ERROR
PALETTE_WARN = _Palette.WARN
PALETTE_TEXT_MUTED = _Palette.TEXT_MUTED

