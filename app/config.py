"""Централизованная загрузка конфигурации из .env и client_secret JSON."""
from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


class Config:
    """Контейнер настроек приложения."""

    API_KEY: str = os.getenv("API_KEY", "")
    CLIENT_ID: str = os.getenv("CLIENT_ID", "")
    CLIENT_SECRET: str = os.getenv("CLIENT_SECRET", "")
    CLIENT_SECRET_FILE: Path = BASE_DIR / os.getenv(
        "CLIENT_SECRET_FILE",
        "client_secret_1040653347011-jtgdc90nk422cascfp8ufc3q7ic8ffo0.apps.googleusercontent.com.json",
    )
    OAUTH_TOKEN_FILE: Path = BASE_DIR / os.getenv("OAUTH_TOKEN_FILE", "token.json")

    YOUTUBE_SCOPES: list[str] = [
        s.strip()
        for s in os.getenv(
            "YOUTUBE_SCOPES",
            "openid,https://www.googleapis.com/auth/youtube.upload,"
            "https://www.googleapis.com/auth/youtube.force-ssl,"
            "https://www.googleapis.com/auth/youtube.readonly",
        ).split(",")
        if s.strip()
    ]

    DEFAULT_CATEGORY_ID: str = os.getenv("DEFAULT_CATEGORY_ID", "22")
    REDIRECT_URI: str = "http://localhost"
    APP_NAME: str = "ViVideoYouTube"

    @classmethod
    def load_client_secret(cls) -> dict:
        """Возвращает JSON с OAuth-данными Google (installed app)."""
        if not cls.CLIENT_SECRET_FILE.exists():
            raise FileNotFoundError(
                f"Не найден файл OAuth-клиента: {cls.CLIENT_SECRET_FILE}"
            )
        with open(cls.CLIENT_SECRET_FILE, "r", encoding="utf-8") as f:
            return json.load(f)


config = Config()
