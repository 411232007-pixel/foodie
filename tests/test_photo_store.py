import unicodedata
from datetime import datetime
from pathlib import Path

import pytest

from foodie.photo_store import FALLBACK_NAME, detect_image_ext, save_photo
from tests.samples import JPEG, PNG

WHEN = datetime(2026, 10, 20, 15, 17, 3)


@pytest.fixture
def photos(tmp_path: Path) -> Path:
    folder = tmp_path / "photos"
    folder.mkdir()
    return folder


def test_file_name_format(photos):
    path = save_photo(photos, WHEN, "牛肉麵", JPEG, ".jpg")
    assert path.name == "2026-10-20 15-17-03 牛肉麵.jpg"
    assert path.read_bytes() == JPEG


def test_same_second_clash_gets_numbered_and_nothing_is_overwritten(photos):
    first = save_photo(photos, WHEN, "牛肉麵", b"one", ".jpg")
    second = save_photo(photos, WHEN, "牛肉麵", b"two", ".jpg")
    third = save_photo(photos, WHEN, "牛肉麵", b"three", ".jpg")
    assert [p.name for p in (first, second, third)] == [
        "2026-10-20 15-17-03 牛肉麵.jpg",
        "2026-10-20 15-17-03 牛肉麵-2.jpg",
        "2026-10-20 15-17-03 牛肉麵-3.jpg",
    ]
    assert first.read_bytes() == b"one" and third.read_bytes() == b"three"


@pytest.mark.parametrize(
    "evil",
    [
        "..\\..\\evil",
        "../../evil",
        "x\\..\\..\\evil",  # the form that really escapes on Windows once the guard is removed
        "x/../../evil",
        "a/b/c",
        "C:\\Windows\\foo",
        "x:y",
        "..",
        "....",
        "a\x00b\nc",
        "evil‮gpj.exe",
        "zero​width",
        "next\u0085line",
        '<>:"|?*',
        "  . . ",
        "CON",
        "nul.txt",
        "COM1",
        "",
    ],
)
def test_evil_names_stay_inside_the_photos_folder(photos, evil):
    path = save_photo(photos, WHEN, evil, JPEG, ".jpg")
    assert path.parent == photos
    assert path.exists()
    assert not (photos.parent / "evil.jpg").exists()
    stem = path.name.removeprefix("2026-10-20 15-17-03 ")
    assert not any(ch in stem for ch in '\\/:*?"<>|\x00\n')
    assert not any(unicodedata.category(ch)[0] == "C" for ch in stem)
    assert ".." not in stem


def test_empty_name_gets_a_fallback(photos):
    assert FALLBACK_NAME in save_photo(photos, WHEN, "////", JPEG, ".jpg").name


def test_reserved_windows_name_is_changed(photos):
    assert save_photo(photos, WHEN, "CON", JPEG, ".jpg").name.endswith(" _CON.jpg")


def test_long_names_are_shortened(photos):
    path = save_photo(photos, WHEN, "長" * 100, JPEG, ".jpg")
    assert path.name == f"2026-10-20 15-17-03 {'長' * 20}.jpg"


@pytest.mark.parametrize(
    ("data", "ext"),
    [(JPEG, ".jpg"), (PNG, ".png"), (b"GIF89a....", ".gif"), (b"RIFF\x00\x00\x00\x00WEBPVP8 ", ".webp"), (b"MZ\x90", None), (b"", None)],
)
def test_image_type_comes_from_the_bytes(data, ext):
    assert detect_image_ext(data) == ext
