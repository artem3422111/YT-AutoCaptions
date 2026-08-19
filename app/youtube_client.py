"""Клиент YouTube Data API для загрузки видео и шортсов (OAuth2 + API Key)."""
from __future__ import annotations

import mimetypes
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

from app.youtube_auth import YouTubeAuth


class UploadResult:
    """Результат успешной загрузки."""

    def __init__(self, video_id: str, url: str, title: str) -> None:
        self.video_id = video_id
        self.url = url
        self.title = title


class YouTubeClient:
    """Обёртка над YouTube Data API."""

    def __init__(self) -> None:
        self._auth = YouTubeAuth()
        self._youtube = None

    def build_client(self) -> None:
        """Собирает клиент YouTube с валидными credentials."""
        creds = self._auth.get_credentials()
        if not creds:
            raise PermissionError(
                "Не удалось получить OAuth2-авторизацию. Проверьте client_secret JSON."
            )
        self._youtube = build("youtube", "v3", credentials=creds)

    def get_youtube(self):
        """Возвращает клиент YouTube, при необходимости собирая его."""
        if self._youtube is None:
            self.build_client()
        return self._youtube

    @property
    def is_authorized(self) -> bool:
        """True, если есть валидные либо готовые к обновлению credentials."""
        return self._auth.has_credentials

    def auth_needs_refresh(self) -> bool:
        """True, если токен ещё не создан (нужно первично авторизоваться)."""
        return not self._auth.has_credentials

    def upload_video(
        self,
        video_path: str | Path,
        title: str,
        description: str,
        tags: list[str] | None = None,
        category_id: str = "22",
        privacy: str = "private",
        thumbnail_path: str | Path | None = None,
        made_for_kids: bool = False,
        notify_subscribers: bool = True,
        publish_at: str | None = None,
        progress_callback=None,
    ) -> UploadResult:
        """Загружает видео на YouTube; progress_callback обновляет UI."""
        return self._upload(
            video_path=video_path,
            title=title,
            description=description,
            tags=tags,
            category_id=category_id,
            privacy=privacy,
            thumbnail_path=thumbnail_path,
            made_for_kids=made_for_kids,
            notify_subscribers=notify_subscribers,
            publish_at=publish_at,
            progress_callback=progress_callback,
        )

    def _upload(
        self,
        video_path: str | Path,
        title: str,
        description: str,
        tags: list[str] | None,
        category_id: str,
        privacy: str,
        thumbnail_path: str | Path | None,
        made_for_kids: bool,
        notify_subscribers: bool,
        publish_at: str | None,
        progress_callback,
    ) -> UploadResult:
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Файл видео не найден: {video_path}")

        youtube = self.get_youtube()

        if progress_callback:
            progress_callback(5, "Подготовка…")

        body = {
            "snippet": {
                "title": title.strip() or video_path.stem,
                "description": description.strip(),
                "tags": tags or [],
                "categoryId": category_id,
            },
            "status": {
                "privacyStatus": privacy,
                "selfDeclaredMadeForKids": made_for_kids,
                "notifySubscribers": notify_subscribers,
            },
        }

        if publish_at:
            body["status"]["publishAt"] = publish_at

        mime_type = mimetypes.guess_type(str(video_path))[0] or "video/*"
        media = MediaFileUpload(str(video_path), mimetype=mime_type, resumable=True)

        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        if progress_callback:
            progress_callback(15, "Идёт загрузка…")

        response = self._resumable_execute(request, progress_callback)

        if progress_callback:
            progress_callback(90, "Загрузка завершена, финальные штрихи…")

        video_id = response.get("id")

        if thumbnail_path:
            thumb = Path(thumbnail_path)
            if thumb.exists():
                try:
                    youtube.thumbnails().set(
                        videoId=video_id,
                        media_body=MediaFileUpload(str(thumb), mimetype="image/*"),
                    ).execute()
                except HttpError:
                    pass

        if progress_callback:
            progress_callback(100, "Готово!")

        url = f"https://www.youtube.com/watch?v={video_id}"
        return UploadResult(video_id=video_id, url=url, title=title)

    def _resumable_execute(self, request, progress_callback):
        """Последовательное выполнение resumable-запроса с обновлением статуса."""
        response = None
        last_percent = 0
        while response is None:
            status, response = request.next_chunk()
            if status and progress_callback:
                percent = int(status.progress() * 100)
                if percent > last_percent:
                    last_percent = percent
                    progress_callback(15 + percent * 0.7, f"Идёт загрузка… {percent}%")
        return response


    def get_uploaded_videos(self, max_results: int = 50) -> list[dict]:
        """Возвращает список недавно загруженных видео текущего пользователя."""
        youtube = self.get_youtube()
        response = (
            youtube.videos()
            .list(part="snippet,status", mine=True, maxResults=max_results)
            .execute()
        )
        return response.get("items", [])

    def get_playlists(self, max_results: int = 100) -> list[dict]:
        """Возвращает список плейлистов текущего канала."""
        youtube = self.get_youtube()
        try:
            response = (
                youtube.playlists()
                .list(part="snippet", mine=True, maxResults=max_results)
                .execute()
            )
            return response.get("items", [])
        except HttpError:
            return []

    def get_categories(self) -> list[dict]:
        """Возвращает список категорий видео YouTube (регион 'US')."""
        youtube = self.get_youtube()
        response = (
            youtube.videoCategories()
            .list(part="snippet", regionCode="US")
            .execute()
        )
        return response.get("items", [])

    def get_channel_info(self) -> dict | None:
        """Возвращает информацию о текущем канале (или None)."""
        youtube = self.get_youtube()
        try:
            response = (
                youtube.channels()
                .list(part="snippet,statistics", mine=True)
                .execute()
            )
            items = response.get("items", [])
            return items[0] if items else None
        except HttpError:
            return None

