"""Вкладка «Субтитры»: выбор видео, оценка времени и наложение karaoke-субтитров."""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app import caption as cap
from app.caption_worker import CaptionWorker

VIDEO_EXTENSIONS = (
    "Видеофайлы (*.mp4 *.mov *.avi *.mkv *.webm *.m4v *.flv *.wmv *.3gp *.mpeg "
    "*.mpg *.ts);;Все файлы (*)"
)

LANG_OPTIONS = [("Автоопределение", None), ("Русский", "ru"),
                ("Английский", "en"), ("Японский", "ja")]


class CaptionTab(QWidget):
    """Форма наложения субтитров на видео."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._video_path: Path | None = None
        self._worker: CaptionWorker | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        layout.addWidget(self._build_header())
        layout.addWidget(self._build_file_card())
        layout.addWidget(self._build_options_card())

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("", self)
        self.status_label.setObjectName("statusLabel")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.caption_btn = QPushButton("🎬  Создать субтитры", self)
        self.caption_btn.setObjectName("accentButton")
        self.caption_btn.setMinimumHeight(46)
        self.caption_btn.setEnabled(False)
        self.caption_btn.clicked.connect(self._on_caption_clicked)
        layout.addWidget(self.caption_btn)

        self.result_label = QLabel("", self)
        self.result_label.setObjectName("fileNameLabel")
        self.result_label.setWordWrap(True)
        layout.addWidget(self.result_label)

        layout.addStretch(1)

    def _build_header(self) -> QWidget:
        header = QWidget(self)
        v = QVBoxLayout(header)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(4)

        title = QLabel("Наложение субтитров", header)
        title.setObjectName("titleLabel")

        subtitle = QLabel(
            "Выберите видео — речь распознается автоматически, и в него будут "
            "встроены karaoke-субтитры (текущее слово — жёлтым, остальные — белым).",
            header,
        )
        subtitle.setObjectName("subtitleLabel")
        subtitle.setWordWrap(True)

        v.addWidget(title)
        v.addWidget(subtitle)
        return header

    def _build_file_card(self) -> QGroupBox:
        box = QGroupBox("Видеофайл", self)
        grid = QGridLayout(box)
        grid.setContentsMargins(14, 16, 14, 14)
        grid.setSpacing(10)

        self.file_path_edit = QLineEdit(box)
        self.file_path_edit.setPlaceholderText("Файл не выбран — нажмите «Выбрать видео»")
        self.file_path_edit.setReadOnly(True)
        grid.addWidget(self.file_path_edit, 0, 0, 1, 2)

        self.choose_btn = QPushButton("📂  Выбрать видео", box)
        self.choose_btn.clicked.connect(self._choose_video)
        grid.addWidget(self.choose_btn, 0, 2)

        return box

    def _build_options_card(self) -> QGroupBox:
        box = QGroupBox("Параметры", self)
        grid = QGridLayout(box)
        grid.setContentsMargins(14, 16, 14, 14)
        grid.setSpacing(10)
        grid.setColumnStretch(1, 1)

        grid.addWidget(self._field_label("Качество"), 0, 0)
        self.model_combo = QComboBox(box)
        for key, label in cap.MODEL_LABELS.items():
            self.model_combo.addItem(label, key)
        self.model_combo.setCurrentIndex(list(cap.MODEL_LABELS).index("small"))
        self.model_combo.currentIndexChanged.connect(self._update_estimate)
        grid.addWidget(self.model_combo, 0, 1)

        grid.addWidget(self._field_label("Язык"), 1, 0)
        self.lang_combo = QComboBox(box)
        for label, _code in LANG_OPTIONS:
            self.lang_combo.addItem(label)
        grid.addWidget(self.lang_combo, 1, 1)

        self.estimate_label = QLabel("⏱ Оценка появится после выбора видео", box)
        self.estimate_label.setObjectName("mutedLabel")
        grid.addWidget(self.estimate_label, 2, 0, 1, 2)

        return box

    @staticmethod
    def _field_label(text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        return label

    def _choose_video(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите видео", str(Path.home()), VIDEO_EXTENSIONS
        )
        if not file_path:
            return
        self._video_path = Path(file_path)
        self.file_path_edit.setText(str(file_path))
        self.caption_btn.setEnabled(True)
        self.result_label.setText("")
        self._update_estimate()

    def _update_estimate(self) -> None:
        if not self._video_path or not self._video_path.exists():
            return
        model = self.model_combo.currentData()
        estimate = cap.estimate_time(self._video_path, model)
        self.estimate_label.setText(f"⏱ Примерное время работы: {estimate}")

    def _selected_lang(self) -> str | None:
        index = self.lang_combo.currentIndex()
        if 0 <= index < len(LANG_OPTIONS):
            return LANG_OPTIONS[index][1]
        return None


    def _on_caption_clicked(self) -> None:
        if not self._video_path or not self._video_path.exists():
            self._set_status("Сначала выберите видеофайл.", error=True)
            return

        out_path = self._video_path.with_name(self._video_path.stem + "_captioned.mp4")

        self._set_busy(True)
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.result_label.setText("")
        self.estimate_label.hide()

        self._worker = CaptionWorker(
            video_path=str(self._video_path),
            model=self.model_combo.currentData(),
            lang=self._selected_lang(),
            font="DejaVu Sans",
            font_size=35,
            out_path=str(out_path),
            parent=self,
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.succeeded.connect(self._on_success)
        self._worker.failed.connect(self._on_failure)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_progress(self, percent: int, message: str) -> None:
        self.progress_bar.setValue(percent)
        self._set_status(f"{message} ({percent}%)")

    def _on_success(self, out_path: str) -> None:
        self.progress_bar.hide()
        self.result_label.setText(
            f"✅ Субтитры готовы!\n"
            f"Файл: {Path(out_path).name}\n"
            f"Путь: {out_path}\n"
            "Откройте его — текущее слово подсвечивается жёлтым."
        )
        self._set_status("Готово!")
        self.caption_btn.setEnabled(False)

    def _on_failure(self, message: str) -> None:
        self.progress_bar.hide()
        self._set_status(f"Ошибка: {message}", error=True)
        self.estimate_label.show()

    def _on_finished(self) -> None:
        self._set_busy(False)

    def _set_busy(self, busy: bool) -> None:
        self.caption_btn.setEnabled(not busy and self._video_path is not None)
        self.choose_btn.setEnabled(not busy)

    def _set_status(self, message: str, error: bool = False) -> None:
        color = "#E53935" if error else "#9E9E9E"
        self.status_label.setStyleSheet(f"color: {color};")
        self.status_label.setText(message)

    def shutdown(self) -> None:
        """Останавливает активный воркер при закрытии окна."""
        if self._worker is not None and self._worker.isRunning():
            self._worker.requestInterruption()
            if not self._worker.wait(3000):
                self._worker.terminate()
                self._worker.wait(1000)

