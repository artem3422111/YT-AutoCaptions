#!/usr/bin/env python3
"""CLI-версия наложения karaoke-субтитров: обёртка над app/caption.py."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app import caption as cap


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="subtitle_tool",
        description="Распознаёт речь в видео и встраивает karaoke-субтитры.",
    )
    parser.add_argument("video", type=Path, help="Путь к видеофайлу")
    parser.add_argument(
        "-o", "--out", type=Path,
        help="Выходной файл (по умолчанию <видео>_captioned.mp4)",
    )
    parser.add_argument(
        "--model", default="small",
        choices=list(cap.SPEED_FACTORS),
        help="Модель: tiny/base (быстро) -> small/medium (точно)",
    )
    parser.add_argument(
        "--lang", default="ru", help="Язык (ru/en/ja…), пустое = автоопределение"
    )
    parser.add_argument("--font", default="DejaVu Sans", help="Шрифт субтитров")
    parser.add_argument(
        "--font-size", type=int, default=35, help="Размер шрифта (для 1080p)"
    )
    parser.add_argument(
        "--keep", action="store_true",
        help="Сохранить промежуточный ASS-файл рядом с результатом",
    )
    args = parser.parse_args(argv)

    if not args.video.exists():
        print(f"❌ Файл не найден: {args.video}", file=sys.stderr)
        return 1

    lang = args.lang or None
    out = args.out or args.video.with_name(args.video.stem + "_captioned.mp4")

    def report(stage, pct):
        print(f"[{pct:>3}%] {stage}")

    try:
        result = cap.caption_video(
            video=args.video,
            model=args.model,
            lang=lang,
            font=args.font,
            font_size=args.font_size,
            out=out,
            progress=report,
            keep=args.keep,
        )
        print(f"✅ Готово: {result}")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"❌ Ошибка: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
