"""Вкладка «Убрать музыку» — разделение голоса и музыки (Demucs).

Пользователь выбирает видео, нажимает кнопку — Demucs убирает музыку/саундтрек,
оставляя голос/озвучку. Результат сохраняется как <имя>_vocals.mp4.
"""
from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import (
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

from app.audio_worker import AudioWorker

VIDEO_EXTENSIONS = (
    "Видеофайлы (*.mp4 *.mov *.avi *.mkv *.webm *.m4v *.flv *.wmv *.3gp *.mpeg "
    "*.mpg *.ts);;Все файлы (*)"
)


class MusicRemoverTab(QWidget):
    """Форма удаления музыки из видео (оставляя голос)."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._video_path: Path | None = None
        self._worker: AudioWorker | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        layout.addWidget(self._build_header())
        layout.addWidget(self._build_file_card())

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("", self)
        self.status_label.setObjectName("statusLabel")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        self.remove_btn = QPushButton("🎵  Убрать музыку", self)
        self.remove_btn.setObjectName("accentButton")
        self.remove_btn.setMinimumHeight(46)
        self.remove_btn.setEnabled(False)
        self.remove_btn.clicked.connect(self._on_remove_clicked)
        layout.addWidget(self.remove_btn)

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

        title = QLabel("Удаление музыки", header)
        title.setObjectName("titleLabel")

        subtitle = QLabel(
            "Выберите видео — Demucs выделит голос/озвучку и уберёт музыку/"
            "саундтрек. Снижает риск бана за авторские права на музыку.",
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

    # ------------------------------------------------------------------ #
    # Выбор файла
    # ------------------------------------------------------------------ #
    def _choose_video(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите видео", str(Path.home()), VIDEO_EXTENSIONS
        )
        if not file_path:
            return
        self._video_path = Path(file_path)
        self.file_path_edit.setText(str(file_path))
        self.remove_btn.setEnabled(True)
        self.result_label.setText("")

    # ------------------------------------------------------------------ #
    # Запуск
    # ------------------------------------------------------------------ #
    def _on_remove_clicked(self) -> None:
        if not self._video_path or not self._video_path.exists():
            self._set_status("Сначала выберите видеофайл.", error=True)
            return

        out_path = self._video_path.with_name(self._video_path.stem + "_vocals.mp4")

        self._set_busy(True)
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self.result_label.setText("")

        self._worker = AudioWorker(
            video_path=str(self._video_path),
            out_path=str(out_path),
            device="auto",
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
            f"✅ Готово! Музыка убрана, голос сохранён.\n"
            f"Файл: {out_path}\n"
            "Теперь можно загрузить его в «Видео» или «Шортсы»."
        )
        self._set_status("Готово!")
        self.remove_btn.setEnabled(False)

    def _on_failure(self, message: str) -> None:
        self.progress_bar.hide()
        self._set_status(f"Ошибка: {message}", error=True)

    def _on_finished(self) -> None:
        self._set_busy(False)

    # ------------------------------------------------------------------ #
    # Вспомогательное
    # ------------------------------------------------------------------ #
    def _set_busy(self, busy: bool) -> None:
        self.remove_btn.setEnabled(not busy and self._video_path is not None)
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

