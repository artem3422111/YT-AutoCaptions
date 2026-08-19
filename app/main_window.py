"""Главное окно ViVideoYouTube: вкладки, меню авторизации, статус-бар."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QMainWindow,
    QStatusBar,
    QTabWidget,
)

from app import __version__
from app.auth_worker import AuthWorker
from app.config import config
from app.theme import QSS
from app.widgets.caption_tab import CaptionTab
from app.widgets.music_remover_tab import MusicRemoverTab
from app.widgets.shorts_tab import ShortsTab
from app.widgets.video_tab import VideoTab
from app.youtube_client import YouTubeClient


class MainWindow(QMainWindow):
    """Главное окно приложения."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(config.APP_NAME)
        self.resize(820, 760)
        self.setStyleSheet(QSS)

        self.client = YouTubeClient()
        self._auth_worker = None

        self._build_ui()
        self._build_menu()
        self._setup_status_bar()

    def _build_ui(self) -> None:
        self.tabs = QTabWidget(self)
        self.tabs.setDocumentMode(False)
        self.tabs.setMovable(False)

        self.video_tab = VideoTab(self)
        self.shorts_tab = ShortsTab(self)
        self.caption_tab = CaptionTab(self)
        self.music_tab = MusicRemoverTab(self)

        self.tabs.addTab(self.video_tab, "🎬  Видео")
        self.tabs.addTab(self.shorts_tab, "⚡  Шортсы")
        self.tabs.addTab(self.caption_tab, "💬  Субтитры")
        self.tabs.addTab(self.music_tab, "🎵  Убрать музыку")

        self.setCentralWidget(self.tabs)

    def _build_menu(self) -> None:
        menubar = self.menuBar()

        app_menu = menubar.addMenu("&Приложение")
        auth_action = app_menu.addAction("🔑  Авторизация в YouTube")
        auth_action.triggered.connect(self._authorize)
        app_menu.addSeparator()
        exit_action = app_menu.addAction("Выход")
        exit_action.triggered.connect(self.close)

        help_menu = menubar.addMenu("&Справка")
        about_action = help_menu.addAction("О программе")
        about_action.triggered.connect(self._show_about)

    def _setup_status_bar(self) -> None:
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage(f"Готово. Стек: Python · PyQt6 · YouTube Data API")

    def _authorize(self) -> None:
        """Запускает OAuth2-авторизацию в фоновом потоке (откроется браузер)."""
        if self._auth_worker is not None and self._auth_worker.isRunning():
            self.status.showMessage("Авторизация уже выполняется…")
            return

        self.status.showMessage("Авторизация… Откройте браузер и подтвердите доступ.")
        self._auth_worker = AuthWorker(self)
        self._auth_worker.succeeded.connect(self._on_auth_succeeded)
        self._auth_worker.failed.connect(self._on_auth_failed)
        self._auth_worker.start()

    def _on_auth_succeeded(self, channel_name: str) -> None:
        self.status.showMessage(f"✅ Авторизация успешна: {channel_name}")

    def _on_auth_failed(self, message: str) -> None:
        from PyQt6.QtWidgets import QMessageBox

        self.status.showMessage(f"❌ Ошибка авторизации: {message}")

        if "403" in message and "access_denied" in message:
            QMessageBox.warning(
                self,
                "Доступ запрещён (Error 403)",
                "Google отказал в доступе, так как приложение «Vilibrity» "
                "находится в тестовом режиме (Testing) и не прошло верификацию.\n\n"
                "Чтобы войти под своим аккаунтом:\n"
                "1) Откройте Google Cloud Console → проект Vilibrity;\n"
                "2) APIs & Services → OAuth consent screen;\n"
                "3) В разделе «Test users» нажмите Add users;\n"
                "4) Добавьте тот Google-аккаунт, под которым входите;\n"
                "5) Подождите до часа и повторите авторизацию.\n\n"
                f"Детали: {message}",
            )
        else:
            QMessageBox.warning(
                self, "Ошибка авторизации", f"Не удалось авторизоваться:\n{message}"
            )

    def closeEvent(self, event) -> None:
        """Останавливает фоновые потоки до закрытия окна."""
        self._stop_background_threads()
        event.accept()
        super().closeEvent(event)

    def _stop_background_threads(self) -> None:
        """Останавливает все активные фоновые воркеры."""
        self.video_tab.shutdown()
        self.shorts_tab.shutdown()
        self.caption_tab.shutdown()
        self.music_tab.shutdown()

        if self._auth_worker is not None and self._auth_worker.isRunning():
            self._auth_worker.requestInterruption()
            if not self._auth_worker.wait(3000):
                self._auth_worker.terminate()
                self._auth_worker.wait(1000)


    def _show_about(self) -> None:
        from PyQt6.QtWidgets import QMessageBox

        QMessageBox.about(
            self,
            "О программе",
            f"<b>{config.APP_NAME}</b><br>"
            f"Версия {__version__}<br><br>"
            "Мини-приложение для загрузки видео и шортсов на YouTube.<br>"
            "Стек: Python 3.14 · PyQt6 · YouTube Data API v3",
        )
