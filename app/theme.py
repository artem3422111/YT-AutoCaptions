"""Тёмная тема приложения (QSS + палитра, акцент — красный YouTube)."""

from __future__ import annotations


class Palette:
    """Палитра цветов, используется в QSS и в коде."""

    BG_DARK = "#121212"
    BG_PANEL = "#1E1E1E"
    BG_INPUT = "#2A2A2A"
    BG_HOVER = "#333333"
    BORDER = "#3A3A3A"
    BORDER_FOCUS = "#F03A17"
    TEXT = "#F1F1F1"
    TEXT_MUTED = "#9E9E9E"
    ACCENT = "#F03A17"
    ACCENT_HOVER = "#FF4D2E"
    ACCENT_PRESSED = "#D62E0F"
    SUCCESS = "#2EBD59"
    ERROR = "#E53935"
    WARN = "#FFB300"
    SELECTED = "#2A3B52"

QSS = f"""
* {{
    font-family: "Segoe UI", "Roboto", "Noto Sans", sans-serif;
    font-size: 13px;
    color: {Palette.TEXT};
    outline: none;
}}

QMainWindow, QDialog {{
    background-color: {Palette.BG_DARK};
}}

QWidget {{
    background-color: transparent;
}}

QTabWidget::pane {{
    border: 1px solid {Palette.BORDER};
    border-radius: 8px;
    background-color: {Palette.BG_PANEL};
    top: -1px;
}}

QTabBar::tab {{
    background-color: {Palette.BG_PANEL};
    border: 1px solid {Palette.BORDER};
    border-bottom: none;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    padding: 10px 28px;
    margin-right: 2px;
    color: {Palette.TEXT_MUTED};
    font-weight: 600;
}}

QTabBar::tab:hover {{
    background-color: {Palette.BG_HOVER};
    color: {Palette.TEXT};
}}

QTabBar::tab:selected {{
    background-color: {Palette.BG_INPUT};
    color: {Palette.ACCENT};
    border-bottom: 3px solid {Palette.ACCENT};
}}

QPushButton {{
    background-color: {Palette.BG_INPUT};
    border: 1px solid {Palette.BORDER};
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 600;
    color: {Palette.TEXT};
}}

QPushButton:hover {{
    background-color: {Palette.BG_HOVER};
    border-color: {Palette.BORDER_FOCUS};
}}

QPushButton:pressed {{
    background-color: {Palette.BORDER};
}}

QPushButton:disabled {{
    color: {Palette.TEXT_MUTED};
    background-color: {Palette.BG_PANEL};
    border-color: {Palette.BORDER};
}}

QPushButton#accentButton {{
    background-color: {Palette.ACCENT};
    border: none;
    border-radius: 6px;
    color: #FFFFFF;
    font-size: 14px;
    font-weight: 700;
    padding: 12px 24px;
}}

QPushButton#accentButton:hover {{
    background-color: {Palette.ACCENT_HOVER};
}}

QPushButton#accentButton:pressed {{
    background-color: {Palette.ACCENT_PRESSED};
}}

QPushButton#accentButton:disabled {{
    background-color: {Palette.BG_INPUT};
    color: {Palette.TEXT_MUTED};
}}

QLineEdit, QTextEdit, QPlainTextEdit, QComboBox, QSpinBox {{
    background-color: {Palette.BG_INPUT};
    border: 1px solid {Palette.BORDER};
    border-radius: 6px;
    padding: 8px 10px;
    selection-background-color: {Palette.ACCENT};
    selection-color: #FFFFFF;
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
QComboBox:focus, QSpinBox:focus {{
    border: 1px solid {Palette.BORDER_FOCUS};
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: 1px solid {Palette.BORDER};
    border-top-right-radius: 6px;
    border-bottom-right-radius: 6px;
}}

QComboBox QAbstractItemView {{
    background-color: {Palette.BG_INPUT};
    border: 1px solid {Palette.BORDER};
    selection-background-color: {Palette.SELECTED};
    selection-color: {Palette.TEXT};
}}

QCheckBox, QRadioButton {{
    spacing: 8px;
}}

QCheckBox::indicator, QRadioButton::indicator {{
    width: 16px;
    height: 16px;
    border: 2px solid {Palette.BORDER};
    border-radius: 4px;
    background-color: {Palette.BG_INPUT};
}}

QCheckBox::indicator:checked {{
    background-color: {Palette.ACCENT};
    border-color: {Palette.ACCENT};
}}

QRadioButton::indicator {{
    border-radius: 8px;
}}

QRadioButton::indicator:checked {{
    background-color: {Palette.ACCENT};
    border-color: {Palette.ACCENT};
}}

QProgressBar {{
    border: 1px solid {Palette.BORDER};
    border-radius: 6px;
    background-color: {Palette.BG_INPUT};
    text-align: center;
    color: {Palette.TEXT};
    height: 18px;
}}

QProgressBar::chunk {{
    background-color: {Palette.ACCENT};
    border-radius: 5px;
}}

QScrollBar:vertical {{
    background: {Palette.BG_PANEL};
    width: 12px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background: {Palette.BG_HOVER};
    min-height: 30px;
    border-radius: 6px;
}}

QScrollBar::handle:vertical:hover {{
    background: {Palette.BORDER};
}}

QScrollBar::add-line, QScrollBar::sub-line {{
    height: 0;
}}

QScrollBar:horizontal {{
    background: {Palette.BG_PANEL};
    height: 12px;
}}

QScrollBar::handle:horizontal {{
    background: {Palette.BG_HOVER};
    min-width: 30px;
    border-radius: 6px;
}}

QScrollBar::add-page, QScrollBar::sub-page {{
    background: none;
}}

QLabel#titleLabel {{
    font-size: 20px;
    font-weight: 700;
    color: {Palette.TEXT};
}}

QLabel#subtitleLabel {{
    font-size: 13px;
    color: {Palette.TEXT_MUTED};
}}

QLabel#fieldLabel {{
    font-weight: 600;
    color: {Palette.TEXT};
}}

QLabel#mutedLabel {{
    color: {Palette.TEXT_MUTED};
}}

QLabel#fileNameLabel {{
    color: {Palette.SUCCESS};
    font-weight: 600;
}}

QLabel#statusLabel {{
    color: {Palette.TEXT_MUTED};
}}

QLabel#errorLabel {{
    color: {Palette.ERROR};
}}

QGroupBox {{
    border: 1px solid {Palette.BORDER};
    border-radius: 8px;
    margin-top: 14px;
    padding-top: 10px;
    font-weight: 700;
    background-color: {Palette.BG_PANEL};
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {Palette.ACCENT};
}}

QFrame#card {{
    background-color: {Palette.BG_PANEL};
    border: 1px solid {Palette.BORDER};
    border-radius: 8px;
}}

QMenuBar {{
    background-color: {Palette.BG_DARK};
    border-bottom: 1px solid {Palette.BORDER};
}}

QMenuBar::item {{
    padding: 6px 10px;
    background: transparent;
}}

QMenuBar::item:selected {{
    background: {Palette.BG_INPUT};
}}

QMenu {{
    background-color: {Palette.BG_PANEL};
    border: 1px solid {Palette.BORDER};
    padding: 6px;
}}

QMenu::item {{
    padding: 6px 28px 6px 20px;
    border-radius: 4px;
}}

QMenu::item:selected {{
    background-color: {Palette.SELECTED};
}}

QMenu::separator {{
    height: 1px;
    background: {Palette.BORDER};
    margin: 4px 8px;
}}

QStatusBar {{
    background-color: {Palette.BG_PANEL};
    border-top: 1px solid {Palette.BORDER};
    color: {Palette.TEXT_MUTED};
}}

QListWidget, QTreeWidget, QTableWidget {{
    background-color: {Palette.BG_INPUT};
    border: 1px solid {Palette.BORDER};
    border-radius: 6px;
}}

QListWidget::item {{
    padding: 6px;
    border-radius: 4px;
}}

QListWidget::item:selected {{
    background-color: {Palette.SELECTED};
}}
"""


