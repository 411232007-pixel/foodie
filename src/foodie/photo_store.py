"""Save photos into DATA_DIR/photos. Holds 防護 3 (see docs/architecture.md section 12)."""

from __future__ import annotations

import itertools
import re
import unicodedata
from datetime import datetime
from pathlib import Path

MAX_NAME_CHARS = 20
FALLBACK_NAME = "未命名"

_FORBIDDEN_CHARS = re.compile(r'[\\/:*?"<>|]')  # path separators and what Windows refuses
_RESERVED_NAMES = {"CON", "PRN", "AUX", "NUL"} | {f"COM{i}" for i in range(1, 10)} | {f"LPT{i}" for i in range(1, 10)}


class PhotoStoreError(Exception):
    """The photo could not be stored safely."""


def detect_image_ext(data: bytes) -> str | None:
    """Look at the file's own first bytes; never trust the uploader's file name."""
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return ".gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return None


def candidate_path(photos_dir: Path, when: datetime, name: str, suffix: str, ext: str) -> Path:
    """Where the photo should go: `YYYY-MM-DD hh-mm-ss <short name><suffix><ext>` inside photos_dir."""
    prefix = f"{when:%Y-%m-%d %H-%M-%S}"
    name = name[:MAX_NAME_CHARS]

    # Without the protection below, the name from claude is used exactly as it came.
    path = photos_dir / f"{prefix} {name}{suffix}{ext}"

    # ==== 防護 3：食物名稱變檔名前先清洗　開始 ====
    name = "".join(ch for ch in name if unicodedata.category(ch)[0] != "C")  # control, invisible, direction-flip
    name = _FORBIDDEN_CHARS.sub("", name)  # / \ : * ? " < > |
    name = name.replace("..", "")  # "go up one folder"
    name = name.strip(" .")  # Windows silently drops trailing dots and spaces
    if name.split(".")[0].upper() in _RESERVED_NAMES:
        name = f"_{name}"  # CON, NUL, COM1 ... cannot be file names on Windows
    name = name or FALLBACK_NAME
    path = photos_dir / f"{prefix} {name}{suffix}{ext}"
    if photos_dir.resolve() not in path.resolve().parents:  # last line of defence
        raise PhotoStoreError(f"檔案路徑跑出照片資料夾:{path}")
    # ==== 防護 3 結束 ====

    return path


def save_photo(photos_dir: Path, when: datetime, name: str, data: bytes, ext: str) -> Path:
    """Write the photo without ever overwriting a file: a clash gets -2, -3, ... before the extension."""
    photos_dir.mkdir(parents=True, exist_ok=True)
    for number in itertools.count(1):
        suffix = "" if number == 1 else f"-{number}"
        path = candidate_path(photos_dir, when, name, suffix, ext)
        try:
            with open(path, "xb") as handle:  # "x" = create, fail if it already exists
                handle.write(data)
        except FileExistsError:
            continue
        return path
    raise AssertionError("unreachable")
