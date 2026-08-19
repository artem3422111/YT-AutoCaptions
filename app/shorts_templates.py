"""Генерация метаданных шортсов (название, описание, теги) с гибкой настройкой.

Шаблон полностью конфигурируется (подойдёт любому формату контента — аниме,
реакции, обзоры и т.п.):
  - файл-шаблон shorts_template.txt (см. shorts_template.txt.example)
    определяет список полей ввода (секция FIELDS), заголовок (TITLE),
    описание (DESCRIPTION) и теги (TAGS);
  - плейсхолдеры {имя_поля}, а также {site}, {tg}, {tags} подставляются в текст.
Если файл не задан — используются поля и заготовки по умолчанию (аниме).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.config import config

# Встроенные поля по умолчанию (аниме): ключ, подпись в UI, placeholder
_DEFAULT_FIELDS = [
    ("название", "Название", "Например: Attack on Titan"),
    ("озвучка", "Озвучка", "Например: AniLibria"),
]


@dataclass
class Field:
    """Поле ввода шаблона шортсов."""
    key: str          # имя плейсхолдера {key}
    label: str        # подпись в интерфейсе
    placeholder: str  # подсказка внутри поля


def get_shorts_fields() -> list[Field]:
    """Возвращает список полей ввода для текущего шаблона."""
    if config.SHORTS_TEMPLATE_FILE and config.SHORTS_TEMPLATE_FILE.exists():
        sections = _parse_template(config.SHORTS_TEMPLATE_FILE)
        fields = _parse_fields(sections.get("FIELDS", []))
        if fields:
            return fields
    return [Field(key, label, placeholder) for key, label, placeholder in _DEFAULT_FIELDS]


def generate_shorts_metadata(
    values: dict[str, str],
) -> tuple[str, str, list[str]]:
    """Генерирует (title, description, tags), подставляя значения полей.

    values — словарь {ключ_поля: введённый текст}. Ключи определяются
    функцией get_shorts_fields().
    """
    if config.SHORTS_TEMPLATE_FILE and config.SHORTS_TEMPLATE_FILE.exists():
        return _from_template_file(config.SHORTS_TEMPLATE_FILE, values)
    return _builtin(values)


def _from_template_file(
    path: Path, values: dict[str, str]
) -> tuple[str, str, list[str]]:
    """Читает пользовательский шаблон и подставляет значения."""
    sections = _parse_template(path)
    tags = _split_tags(sections.get("TAGS", []))
    placeholders = _make_placeholders(values, tags)

    title = _render(sections.get("TITLE", [""]), placeholders)
    description = _render(sections.get("DESCRIPTION", []), placeholders)
    result_tags = list(tags)
    result_tags.extend(_field_variants(values))
    return title, description, _unique(result_tags)[:100]


def _builtin(values: dict[str, str]) -> tuple[str, str, list[str]]:
    """Встроенная генерация (когда пользователь не создал файл-шаблон)."""
    title_part = _title_part(values)
    lines = [title_part]
    for label, value in _nonempty_supplements(values):
        if label:
            lines.append(f"{label}: {value}")
    lines.append("")
    if config.SHORTS_SITE_URL:
        lines.append(f"🎬 Наш сайт: {config.SHORTS_SITE_URL}")
    if config.SHORTS_TG_URL:
        lines.append(f"📢 Телеграм: {config.SHORTS_TG_URL}")
    lines.append("Подпишись на канал! ❤️")
    lines.append("")
    lines.append("#аниме #анимешортс #аниме_нарезка")

    tags = list(config.SHORTS_BASE_TAGS)
    tags.extend(_field_variants(values))
    return title_part, "\n".join(lines), _unique(tags)[:100]


def _title_part(values: dict[str, str]) -> str:
    """Строит заголовок из первого заполненного поля, остальные — через '—'."""
    filled = [v for v in values.values() if v.strip()]
    if not filled:
        return ""
    return " — ".join(f"«{filled[0]}»" if i == 0 else v for i, v in enumerate(filled))


def _nonempty_supplements(values: dict[str, str]) -> list[tuple[str, str]]:
    """Возвращает пары (подпись поля, значение) для непустых полей, кроме первого."""
    labels = {f.key: f.label for f in get_shorts_fields()}
    filled = [(labels.get(k, k), v.strip()) for k, v in values.items() if v.strip()]
    return filled[1:]


def _make_placeholders(values: dict[str, str], tags: list[str]) -> dict[str, str]:
    placeholders = {
        key: value.strip() for key, value in values.items()
    }
    placeholders["site"] = config.SHORTS_SITE_URL
    placeholders["tg"] = config.SHORTS_TG_URL
    placeholders["tags"] = _tags_to_hashtag(tags)
    return placeholders


def _field_variants(values: dict[str, str]) -> list[str]:
    """Теги из заполненных полей (оригинал + транслитерация)."""
    result: list[str] = []
    for value in values.values():
        value = value.strip()
        if not value:
            continue
        result.append(value)
        alt = _transliterate(value)
        if alt and alt.lower() != value.lower():
            result.append(alt)
    return result


def _parse_fields(lines: list[str]) -> list[Field]:
    """Разбирает секцию FIELDS: строки 'ключ | Подпись | placeholder'."""
    fields: list[Field] = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        if not parts or not parts[0]:
            continue
        key = parts[0]
        label = parts[1] if len(parts) > 1 else key
        placeholder = parts[2] if len(parts) > 2 else key
        fields.append(Field(key, label, placeholder))
    return fields


def _parse_template(path: Path) -> dict[str, list[str]]:
    """Разбирает файл на секции FIELDS / TITLE / DESCRIPTION / TAGS."""
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.rstrip()
        upper = line.strip().upper()
        if upper in ("FIELDS:", "TITLE:", "DESCRIPTION:", "TAGS:"):
            current = upper[:-1]
            sections.setdefault(current, [])
            continue
        if current:
            sections[current].append(line)
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
