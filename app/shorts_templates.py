"""Авто-генерация метаданных (название, описание, теги) для аниме-шортсов.

Поддерживает полную настройку шаблона через файл shorts_template.txt
(см. shorts_template.txt.example). Если файл не задан — используются
значения из .env и встроенные заготовки.
"""
from __future__ import annotations

from pathlib import Path

from app.config import config


def generate_shorts_metadata(
    anime_name: str, dubbing: str = ""
) -> tuple[str, str, list[str]]:
    """Генерирует (title, description, tags) из названия аниме и озвучки."""
    anime_name = anime_name.strip()
    dubbing = dubbing.strip()

    if config.SHORTS_TEMPLATE_FILE and config.SHORTS_TEMPLATE_FILE.exists():
        return _from_template_file(config.SHORTS_TEMPLATE_FILE, anime_name, dubbing)
    return _builtin(anime_name, dubbing)


def _from_template_file(
    path: Path, anime_name: str, dubbing: str
) -> tuple[str, str, list[str]]:
    """Читает пользовательский шаблон и подставляет значения."""
    sections = _parse_template(path)
    tags = _split_tags(sections.get("TAGS", []))

    placeholders = {
        "anime": anime_name,
        "dubbing": dubbing,
        "site": config.SHORTS_SITE_URL,
        "tg": config.SHORTS_TG_URL,
        "tags": _tags_to_hashtag(tags),
    }

    title = _render(sections.get("TITLE", [""]), placeholders)
    description = _render(sections.get("DESCRIPTION", []), placeholders)
    result_tags = list(tags)
    result_tags.extend(_title_variants(anime_name, dubbing))
    return title, description, _unique(result_tags)[:100]


def _builtin(anime_name: str, dubbing: str) -> tuple[str, str, list[str]]:
    """Встроенная генерация (когда пользователь не создал файл-шаблон)."""
    if dubbing:
        title = f"«{anime_name}» — нарезка | {dubbing}"
    else:
        title = f"«{anime_name}» — нарезка"

    lines = [f"«{anime_name}» — нарезка"]
    if dubbing:
        lines.append(f"Озвучка: {dubbing}")
    lines.append("")
    if config.SHORTS_SITE_URL:
        lines.append(f"🎬 Наш сайт: {config.SHORTS_SITE_URL}")
    if config.SHORTS_TG_URL:
        lines.append(f"📢 Телеграм: {config.SHORTS_TG_URL}")
    lines.append("Подпишись на канал! ❤️")
    lines.append("")
    lines.append("#аниме #анимешортс #аниме_нарезка")
    description = "\n".join(lines)

    tags = list(config.SHORTS_BASE_TAGS)
    tags.extend(_title_variants(anime_name, dubbing))
    return title, description, _unique(tags)[:100]


def _parse_template(path: Path) -> dict[str, list[str]]:
    """Разбирает файл на секции TITLE / DESCRIPTION / TAGS."""
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        upper = line.strip().upper()
        if upper in ("TITLE:", "DESCRIPTION:", "TAGS:"):
            current = upper[:-1]
            sections.setdefault(current, [])
            continue
        if current:
            sections[current].append(line)
    # убираем лишние пустые строки по краям title/description
    for key in ("TITLE", "DESCRIPTION"):
        if key in sections:
            sections[key] = _trim_edges(sections[key])
    return sections


def _trim_edges(lines: list[str]) -> list[str]:
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def _render(lines: list[str], placeholders: dict[str, str]) -> str:
    """Форматирует строки плейсхолдерами и объединяет в текст."""
    rendered: list[str] = []
    for line in lines:
        for key, value in placeholders.items():
            line = line.replace("{" + key + "}", value)
        rendered.append(line)
    return "\n".join(rendered)


def _split_tags(raw: list[str]) -> list[str]:
    """Разбирает строки секции TAGS в список тегов (запятые и переносы строк)."""
    tags: list[str] = []
    for chunk in raw:
        for part in chunk.replace(",", "\n").splitlines():
            tag = part.strip()
            if tag:
                tags.append(tag)
    return tags


def _tags_to_hashtag(tags: list[str]) -> str:
    """Превращает теги в строку хэштегов: ['аниме','shorts'] -> '#аниме #shorts'."""
    return " ".join(f"#{t}" for t in tags)


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for t in items:
        key = t.lower()
        if key not in seen:
            seen.add(key)
            result.append(t)
    return result


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


_CYRILLIC_TO_LATIN = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
    "ж": "zh", "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m",
    "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
    "ф": "f", "х": "kh", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch",
    "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}
_LATIN_TO_CYRILLIC = {v: k for k, v in _CYRILLIC_TO_LATIN.items()}


def _transliterate(text: str) -> str:
    """Переводит кириллицу в латиницу (и наоборот, если текст уже латиница)."""
    if not text:
        return ""

    cyrillic_count = sum(1 for ch in text if "\u0400" <= ch <= "\u04FF")
    if cyrillic_count > len(text) / 2:
        return "".join(_CYRILLIC_TO_LATIN.get(ch.lower(), ch if ch == " " else "")
                       for ch in text).strip()
    return "".join(
        _LATIN_TO_CYRILLIC.get(ch.lower(), ch if ch == " " else "")
        for ch in text
    ).strip()
