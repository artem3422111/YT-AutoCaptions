"""OAuth2-авторизация YouTube Data API: запускает оаuth-flow и хранит token.json."""
from __future__ import annotations

from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from app.config import config


class YouTubeAuth:
    """Управляет OAuth2 credentials для загрузки видео на YouTube."""

    def __init__(self) -> None:
        self._creds: Credentials | None = None
        self._token_file: Path = config.OAUTH_TOKEN_FILE

    @property
    def has_saved_token(self) -> bool:
        """True, если есть ранее сохранённый файл токена (без сети и браузера)."""
        return self._token_file.exists()

    @property
    def has_credentials(self) -> bool:
        """True, если есть валидные либо готовые к обновлению credentials."""
        return self.get_credentials(interactive=False) is not None

    def get_credentials(self, interactive: bool = True) -> Credentials | None:
        """Возвращает валидные credentials, при необходимости запуская OAuth-браузер."""
        if self._creds is not None:
            return self._creds

        loaded = self._load_saved_token(refresh_if_needed=False)
        if loaded is not None and self._is_still_valid(loaded):
            self._creds = loaded
            return self._creds

        if loaded is not None and loaded.expired and loaded.refresh_token:
            self._creds = self._try_refresh(loaded)
            if self._creds is not None:
                return self._creds

        if not interactive:
            return None

        self._creds = self._create_flow_credentials()
        return self._creds

    @staticmethod
    def _is_still_valid(creds: Credentials) -> bool:
        return bool(creds and creds.valid)

    def _load_saved_token(self, refresh_if_needed: bool) -> Credentials | None:
        """Читает сохранённый token.json без сетевых вызовов."""
        if not self._token_file.exists():
            return None
        try:
            return Credentials.from_authorized_user_file(
                str(self._token_file), config.YOUTUBE_SCOPES
            )
        except Exception:
            return None

    def _try_refresh(self, creds: Credentials) -> Credentials | None:
        """Пытается обновить истёкший токен через refresh_token."""
        try:
            creds.refresh(Request())
            self._save_token(creds)
            return creds
        except Exception:
            return None

    def _create_flow_credentials(self) -> Credentials:
        """Запускает OAuth flow: открывает браузер, ловит код на localhost."""
        flow = InstalledAppFlow.from_client_secrets_file(
            str(config.CLIENT_SECRET_FILE), config.YOUTUBE_SCOPES
        )
        creds = flow.run_local_server(
            port=0,
            prompt="consent",
            authorization_prompt_message="",
            success_message=(
                "ViVideoYouTube: авторизация успешна! "
                "Можно закрыть это окно и вернуться в приложение."
            ),
        )
        self._save_token(creds)
        return creds

    def _save_token(self, creds: Credentials) -> None:
        """Сохраняет credentials в token.json."""
        with open(self._token_file, "w", encoding="utf-8") as f:
            f.write(creds.to_json())

    def clear_token(self) -> None:
        """Удаляет сохранённый токен (для повторной авторизации)."""
        self._creds = None
        if self._token_file.exists():
            self._token_file.unlink()
