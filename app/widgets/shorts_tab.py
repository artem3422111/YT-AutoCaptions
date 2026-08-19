"""Вкладка «Шортсы» — загрузка вертикальных видео (9:16, до ~3 минут).

Отличается от обычного видео: у неё есть шаблон авто-заполнения для
аниме-нарезок — пользователь вводит только название аниме и озвучку,
а название/описание/теги генерируются автоматически.
"""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.shorts_templates import generate_shorts_metadata
from app.widgets.upload_form import UploadForm


class ShortsTab(UploadForm):
    """Форма загрузки шортсов (вертикальные видео) с авто-шаблоном."""

    def __init__(self, parent=None) -> None:
        super().__init__(is_shorts=True, parent=parent)
        # Релевантные категории для шортсов; по умолчанию «Films & Animation».
        self.category_combo.clear()
        self.category_combo.addItem("Films & Animation", "1")
        self.category_combo.addItem("People & Blogs", "22")
        self.category_combo.addItem("Entertainment", "24")
        self.category_combo.addItem("Music", "10")
        self.category_combo.addItem("Gaming", "20")
        self.category_combo.setCurrentIndex(0)

        # Приватность по умолчанию — «Не перечислено» (безопасно для нарезок).
        index = self.privacy_combo.findData("unlisted")
        if index != -1:
            self.privacy_combo.setCurrentIndex(index)

    # ------------------------------------------------------------------ #
    # Карточка шаблона
    # ------------------------------------------------------------------ #
    def _build_anime_card(self) -> QGroupBox:
        box = QGroupBox("Шаблон аниме (автозаполнение)", self)
        grid = QGridLayout(box)
        grid.setContentsMargins(14, 16, 14, 14)
        grid.setSpacing(10)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)

        grid.addWidget(self._field_label("Название аниме *"), 0, 0)
        self.anime_name_edit = QLineEdit(box)
        self.anime_name_edit.setPlaceholderText("Например: Attack on Titan")
        self.anime_name_edit.textChanged.connect(self._on_anime_changed)
        grid.addWidget(self.anime_name_edit, 0, 1)

        grid.addWidget(self._field_label("Озвучка"), 0, 2)
        self.dubbing_edit = QLineEdit(box)
        self.dubbing_edit.setPlaceholderText("Например: AniLibria")
        self.dubbing_edit.textChanged.connect(self._on_anime_changed)
        grid.addWidget(self.dubbing_edit, 0, 3)

        hint = QLabel(
            "Введите название аниме (и озвучку) — название, описание и теги "
            "заполнятся сами и останутся редактируемыми.",
            box,
        )
        hint.setObjectName("mutedLabel")
        hint.setWordWrap(True)
        grid.addWidget(hint, 1, 0, 1, 4)

        return box

    def _on_anime_changed(self) -> None:
        """При вводе названия аниме/озвучки автозаполняем остальные поля."""
        # Если название аниме ещё пусто — ничего не генерируем.
        if not self.anime_name_edit.text().strip():
            return
        self._apply_auto_template()
        self._update_upload_state()

    def _apply_auto_template(self) -> None:
        """Заполняет название/описание/теги по шаблону из полей аниме."""
        anime = self.anime_name_edit.text().strip()
        if not anime:
            return
        dubbing = self.dubbing_edit.text().strip()
        title, description, tags = generate_shorts_metadata(anime, dubbing)

        if not self.title_edit.isModified():
            self.title_edit.blockSignals(True)
            self.title_edit.setText(title)
            self.title_edit.blockSignals(False)

        if not self.desc_edit.document().isModified():
            self.desc_edit.blockSignals(True)
            self.desc_edit.document().setModified(False)
            self.desc_edit.setPlainText(description)
            self.desc_edit.blockSignals(False)

        if not self.tags_edit.isModified():
            self.tags_edit.blockSignals(True)
            self.tags_edit.setText(", ".join(tags))
            self.tags_edit.blockSignals(False)
