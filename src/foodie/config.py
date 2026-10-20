"""Settings. Everything the user can change comes from .env; the limits below are fixed."""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import dotenv_values

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"

# Quota and safety limits (docs/architecture.md section 13). Not in .env on purpose.
MAX_IMAGES_PER_MESSAGE = 4
MAX_QUEUE_JOBS = 20
RATE_LIMIT_PHOTOS = 5
RATE_LIMIT_WINDOW_SECONDS = 60
MAX_IMAGE_BYTES = 8 * 1024 * 1024
CLAUDE_TIMEOUT_SECONDS = 90
CLAUDE_MAX_ATTEMPTS = 2
LEDGER_RETRIES = 3
LEDGER_RETRY_SECONDS = 2
EXPORT_COMMAND = "!export"
EXPORT_RATE_LIMIT = 1  # exports per person ...
EXPORT_RATE_WINDOW_SECONDS = 60  # ... per this many seconds

REQUIRED_KEYS = ("DISCORD_TOKEN", "CHANNEL_ID", "CLAUDE_MODEL", "DATA_DIR")
PLACEHOLDER_MARKERS = ("你的", "your_", "your-")


class ConfigError(Exception):
    """Raised with a message that says exactly which setting is wrong."""


@dataclass(frozen=True)
class Config:
    # repr=False keeps the token out of any accidental log line.
    discord_token: str = field(repr=False)
    channel_id: int
    claude_model: str
    data_dir: Path
    claude_path: str

    @property
    def photos_dir(self) -> Path:
        return self.data_dir / "photos"

    @property
    def ledger_path(self) -> Path:
        return self.data_dir / "food_log.xlsx"


def load_config(env_path: Path = ENV_PATH) -> Config:
    if not env_path.exists():
        raise ConfigError(f"找不到設定檔 {env_path}。請照 docs/discord-bot-setup.md 第五節建立 .env。")

    values = dotenv_values(env_path)
    problems: list[str] = []

    def get(key: str) -> str:
        raw = (values.get(key) or "").strip()
        if not raw:
            problems.append(f"{key} 沒有填")
        elif any(marker in raw for marker in PLACEHOLDER_MARKERS):
            problems.append(f"{key} 還是範例文字,請換成真的值")
            return ""
        return raw

    token = get("DISCORD_TOKEN")
    channel_raw = get("CHANNEL_ID")
    model = get("CLAUDE_MODEL")
    data_raw = get("DATA_DIR")

    channel_id = 0
    if channel_raw:
        if channel_raw.isascii() and channel_raw.isdigit():
            channel_id = int(channel_raw)
        else:
            problems.append("CHANNEL_ID 應該是一串數字(右鍵頻道 → 複製頻道 ID)")

    claude_path = shutil.which("claude") or ""
    if not claude_path:
        problems.append("找不到 claude 指令(請確認 Claude Code 已安裝,且在 PATH 裡)")

    if problems:
        raise ConfigError("設定有問題:\n- " + "\n- ".join(problems))

    data_dir = Path(data_raw).expanduser()
    if not data_dir.is_absolute():
        data_dir = PROJECT_ROOT / data_dir  # relative paths mean "relative to the project folder"

    return Config(
        discord_token=token,
        channel_id=channel_id,
        claude_model=model,
        data_dir=data_dir.resolve(),
        claude_path=claude_path,
    )
