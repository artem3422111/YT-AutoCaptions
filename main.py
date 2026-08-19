"""ViVideoYouTube — точка входа приложения.

Запуск:  venv/bin/python main.py
"""
from __future__ import annotations

import sys


def main() -> int:
    # Импорт PyQt выполняем внутри, чтобы красивые сообщения об ошибках
    # выводились до старта GUI.
    try:
        from PyQt6.QtWidgets import QApplication
    except ImportError:
        print(
            "❌ Не установлен PyQt6.\n"
            "   Установите зависимости:  venv/bin/pip install -r requirements.txt",
            file=sys.stderr,
        )
        return 1

    from app.main_window import MainWindow
    from app.theme import QSS

    app = QApplication(sys.argv)
    app.setApplicationName("ViVideoYouTube")
    app.setStyleSheet(QSS)

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
