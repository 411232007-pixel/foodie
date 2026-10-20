"""Nothing private may be committed. These look at what git would really commit (tracked files plus
untracked-but-not-ignored files), not just at the text of .gitignore."""

import re
import shutil
import subprocess
from pathlib import Path

import pytest
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(shutil.which("git") is None or not (ROOT / ".git").exists(), reason="needs a git checkout")

PRIVATE_SUFFIXES = {".xlsx", ".xls", ".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic"}
PRIVATE_FOLDERS = {"data", "photos", ".venv"}
DISCORD_TOKEN_SHAPE = re.compile(rb"[MNO][A-Za-z0-9_-]{23,25}\.[A-Za-z0-9_-]{6}\.[A-Za-z0-9_-]{27,}")


def git_lines(*args: str) -> list[str]:
    done = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=True)
    return [line for line in done.stdout.splitlines() if line]


def committable_files() -> list[Path]:
    tracked = git_lines("-c", "core.quotepath=off", "ls-files")
    untracked = git_lines("-c", "core.quotepath=off", "ls-files", "--others", "--exclude-standard")
    return [ROOT / name for name in sorted(set(tracked + untracked)) if (ROOT / name).is_file()]


@pytest.mark.parametrize("path", [".env", "data/photos/x.jpg", "data/food_log.xlsx", "photos/x.jpg", "food_log.xlsx"])
def test_private_paths_are_ignored_by_git(path):
    done = subprocess.run(["git", "check-ignore", "-q", path], cwd=ROOT)
    assert done.returncode == 0, f"{path} is not ignored"


def test_env_example_is_allowed_to_be_committed():
    assert subprocess.run(["git", "check-ignore", "-q", ".env.example"], cwd=ROOT).returncode != 0


def test_no_private_file_is_tracked_or_about_to_be():
    bad = []
    for path in committable_files():
        relative = path.relative_to(ROOT)
        if relative.name == ".env" or path.suffix.lower() in PRIVATE_SUFFIXES or PRIVATE_FOLDERS & set(relative.parts):
            bad.append(str(relative))
    assert not bad, f"private files would be committed: {bad}"


def test_the_real_token_is_in_no_committable_file():
    token = (dotenv_values(ROOT / ".env").get("DISCORD_TOKEN") or "").strip() if (ROOT / ".env").exists() else ""
    if len(token) < 20 or any(mark in token for mark in ("你的", "your_")):
        pytest.skip("no real token in .env to look for")
    needle = token.encode("utf-8")
    leaked = [str(p.relative_to(ROOT)) for p in committable_files() if needle in p.read_bytes()]
    assert not leaked, f"the real token is inside: {leaked}"  # file names only, never the token itself


def test_nothing_shaped_like_a_discord_token_is_committable():
    leaked = [str(p.relative_to(ROOT)) for p in committable_files() if p.name != "uv.lock" and DISCORD_TOKEN_SHAPE.search(p.read_bytes())]
    assert not leaked, f"token-shaped text found in: {leaked}"
