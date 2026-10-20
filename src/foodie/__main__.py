"""Start the agent:  uv run python -m foodie"""

from __future__ import annotations

import logging
import sys

import discord

from foodie.bot import FoodieBot
from foodie.config import ConfigError, load_config
from foodie.ledger import Ledger


def run() -> None:
    # Chinese text and emoji must never crash the logger on a narrow console code page.
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(errors="replace")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    # discord.py warns that voice is missing; this bot never uses voice, so that line is only noise.
    logging.getLogger("discord.client").addFilter(lambda record: "voice will NOT be supported" not in record.getMessage())

    try:
        cfg = load_config()
    except ConfigError as exc:
        print(f"無法啟動:{exc}", file=sys.stderr)
        raise SystemExit(1) from None

    cfg.photos_dir.mkdir(parents=True, exist_ok=True)
    bot = FoodieBot(cfg, Ledger(cfg.ledger_path))
    try:
        bot.run(cfg.discord_token, log_handler=None)
    except discord.LoginFailure:
        print("無法啟動:Discord 不接受這個 token。請重新 Reset Token,貼進 .env 的 DISCORD_TOKEN。", file=sys.stderr)
        raise SystemExit(1) from None
    except discord.PrivilegedIntentsRequired:
        print(
            "無法啟動:Message Content Intent 沒打開。到 Developer Portal → Bot,"
            "打開 MESSAGE CONTENT INTENT 並按 Save Changes。",
            file=sys.stderr,
        )
        raise SystemExit(1) from None
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    run()
