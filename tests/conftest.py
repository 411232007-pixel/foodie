import sys
from pathlib import Path

import pytest

from foodie.config import Config
from foodie.ledger import Ledger


@pytest.fixture
def cfg(tmp_path: Path) -> Config:
    return Config(
        discord_token="not-a-real-token",
        channel_id=123,
        claude_model="haiku",
        data_dir=tmp_path,
        claude_path="claude",
    )


@pytest.fixture
def ledger(cfg: Config) -> Ledger:
    return Ledger(cfg.ledger_path, sleep=lambda _seconds: None)


@pytest.fixture(autouse=True)
def _quiet_stdout_errors():
    # Chinese in assertion messages must not break on a narrow console code page.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
