"""Вкладка «Шортсы»: загрузка вертикальных видео с настраиваемым шаблоном."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from app.shorts_templates import generate_shorts_metadata, get_shorts_fields
from app.widgets.upload_form import UploadForm


class ShortsTab(UploadForm):
    """Форма загрузки шортсов с авто-шаблоном (поля задаются конфигом)."""

    def __init__(self, parent=None) -> None:
        super().__init__(is_shorts=True, parent=parent)
        self.category_combo.clear()
        self.category_combo.addItem("Films & Animation", "1")
        self.category_combo.addItem("People & Blogs", "22")
        self.category_combo.addItem("Entertainment", "24")
        self.category_combo.addItem("Music", "10")
        self.category_combo.addItem("Gaming", "20")
        self.category_combo.setCurrentIndex(0)

        index = self.privacy_combo.findData("unlisted")
        if index != -1:
            self.privacy_combo.setCurrentIndex(index)

    def _build_template_card(self) -> QGroupBox:
        box = QGroupBox("Шаблон (автозаполнение)", self)
        grid = QGridLayout(box)
        grid.setContentsMargins(14, 16, 14, 14)
        grid.setSpacing(10)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)

        self._field_edits = []
        for idx, field in enumerate(get_shorts_fields()):
            row = idx // 2
            col = (idx % 2) * 2
            grid.addWidget(self._field_label(field.label), row, col)
            edit = QLineEdit(box)
            edit.setPlaceholderText(field.placeholder)
            edit.textChanged.connect(self._on_template_field_changed)
            grid.addWidget(edit, row, col + 1)
            self._field_edits.append(edit)

        rows = (len(self._field_edits) + 1) // 2
        hint = QLabel(
            "Заполните поля — название, описание и теги подставятся автоматически "
            "и останутся редактируемыми.",
            box,
        )
        hint.setObjectName("mutedLabel")
        hint.setWordWrap(True)
        grid.addWidget(hint, rows, 0, 1, 4)

        return box

    def _on_template_field_changed(self) -> None:
        """Автозаполняем поля при вводе хотя бы одного поля шаблона."""
        self._apply_auto_template()
        self._update_upload_state()

    def _field_values(self) -> dict[str, str]:
        values = {}
        for field, edit in zip(get_shorts_fields(), self._field_edits):
            values[field.key] = edit.text()
        return values

    def _apply_auto_template(self) -> None:
        """Заполняет название/описание/теги из текущих полей шаблона."""
        values = self._field_values()
        if not any(v.strip() for v in values.values()):
            return
        title, description, tags = generate_shorts_metadata(values)

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
