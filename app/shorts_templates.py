"""Шаблоны автоматической генерации метаданных для аниме-шортсов.

Пользователь вводит название аниме и озвучку — приложение красиво собирает
название, описание (с сайтом и телеграмом) и набор тегов с автодублированием
названия на русском/английском (транслитерация).
"""
from __future__ import annotations

# --- Статические части шаблона (при желании легко поменять) ---
SITE_URL = "vilibrity.ru"
TG_URL = "https://t.me/VilibrityOfficial"

# Общие теги, добавляются в каждый шортс
BASE_TAGS = [
    "аниме",
    "анимешортс",
    "аниме нарезка",
    "аниме моменты",
    "аниме эдиты",
    "аниме 60 секунд",
    "shorts",
    "anime",
    "anime shorts",
]


def generate_shorts_metadata(
    anime_name: str, dubbing: str = ""
) -> tuple[str, str, list[str]]:
    """Генерирует (title, description, tags) для аниме-шортса.

    anime_name — название аниме (можно на латинице или кириллице).
    dubbing    — название озвучки (необязательно).
    """
    anime_name = anime_name.strip()
    dubbing = dubbing.strip()

    # --- Название (по шаблону пользователя) ---
    if dubbing:
        title = f"«{anime_name}» — нарезка | {dubbing}"
    else:
        title = f"«{anime_name}» — нарезка"

    # --- Описание ---
    lines = [f"«{anime_name}» — нарезка" + (" 🔥" if not dubbing else " 🔥")]
    if dubbing:
        lines.append(f"Озвучка: {dubbing}")
    lines.append("")
    lines.append(f"🎬 Наш сайт: {SITE_URL}")
    lines.append(f"📢 Телеграм: {TG_URL}")
    lines.append("Подпишись на канал! ❤️")
    lines.append("")
    lines.append("#аниме #анимешортс #аниме_нарезка")
    description = "\n".join(lines)

    # --- Теги с дублированием названия на русский/английский ---
    tags = list(BASE_TAGS)
    tags.extend(_title_variants(anime_name, dubbing))
    # Дедупликация, с сохранением порядка, максимум 100 тегов
    seen: set[str] = set()
    unique: list[str] = []
    for t in tags:
        key = t.lower()
        if key not in seen:
            seen.add(key)
            unique.append(t)
    return title, description, unique[:100]


def _title_variants(name: str, dubbing: str) -> list[str]:
    """Возвращает теги из названия аниме (латиница + кириллица) и озвучки."""
    result: list[str] = []
    for part in (name, dubbing):
        if not part:
            continue
        result.append(part)
        alt = _transliterate(part)
        if alt and alt.lower() != part.lower():
            result.append(alt)
    return result


# --- Транслитерация (встроенная, без внешних зависимостей) ---
_CYRILLIC_TO_LATIN = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}
_LATIN_TO_CYRILLIC = {v: k for k, v in _CYRILLIC_TO_LATIN.items()}


def _transliterate(text: str) -> str:
    """Переводит кириллицу в латиницу (и наоборот, если текст уже латиница).

    Возвращает пустую строку, если текст смешанный/не распознаётся.
    """
    if not text:
        return ""

    # Определяем, кириллица ли в основном
    cyrillic_count = sum(1 for ch in text if "\u0400" <= ch <= "\u04FF")
    if cyrillic_count > len(text) / 2:
        # кириллица -> латиница
        return "".join(_CYRILLIC_TO_LATIN.get(ch.lower(), ch if ch == " " else "")
                       for ch in text).strip()
    # Считаем, что латиница -> кириллица (если есть транслит)
    return "".join(
        _LATIN_TO_CYRILLIC.get(ch.lower(), ch if ch == " " else "")
        for ch in text
    ).strip()
