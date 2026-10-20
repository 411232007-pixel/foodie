"""The words the bot says in the channel."""

from __future__ import annotations

import discord

from foodie.processor import PhotoResult

FAILED_TEXT = "分析失敗，請再傳一次"
UNCLEAR_TEXT = "照片看不清楚，請重拍一張"
LEDGER_BUSY_TEXT = "紀錄檔暫時寫不進去(可能正開著 Excel)，請關掉後再傳一次"
TOO_BIG_TEXT = "圖片太大了(上限 8 MB)，請縮小後再傳"
BUSY_TEXT = "目前太忙，請稍後再傳"
TOO_FAST_TEXT = "你傳得太頻繁了，請稍等一下再傳"
DISCORD_LIMIT = 1900  # Discord refuses messages over 2000 characters


def number(value: float) -> str:
    return f"{value:,.0f}" if float(value).is_integer() else f"{value:,.1f}"


def total_line(total: float) -> str:
    return f"今日已攝取熱量(全頻道累計):約 {number(total)} 大卡"


def failure_text(result: PhotoResult) -> str:
    if result.status == "unclear":
        return UNCLEAR_TEXT
    if result.status == "ledger_busy":
        return LEDGER_BUSY_TEXT
    if result.status == "too_big":
        return TOO_BIG_TEXT
    return FAILED_TEXT


def single_reply(result: PhotoResult) -> str:
    if result.status != "ok":
        return failure_text(result)
    if not result.is_food:
        lines = [
            f"你傳的不是食物,是{result.name}。",
            f"成份:{result.name}",
            "重量:0 公克",
            "熱量:0 大卡(不是食物,不計入總熱量)",
        ]
    else:
        lines = [
            f"是食物:{result.name}",
            f"成份:{'、'.join(result.ingredients) or '(沒有列出)'}",
            f"重量:約 {number(result.weight_g)} 公克",
            f"熱量:約 {number(result.calories_kcal)} 大卡",
        ]
    lines.append(total_line(result.daily_total or 0.0))
    return "\n".join(lines)


def multi_reply(results: list[PhotoResult], skipped: int = 0) -> str:
    lines = [f"這則訊息的 {len(results)} 張照片:"]
    for index, result in enumerate(results, start=1):
        if result.status != "ok":
            lines.append(f"{index}. {failure_text(result)}")
        elif not result.is_food:
            lines.append(f"{index}. 你傳的不是食物,是{result.name}")
        else:
            lines.append(
                f"{index}. {result.name} — 約 {number(result.weight_g)} 公克、約 {number(result.calories_kcal)} 大卡"
            )
    totals = [r.daily_total for r in results if r.status == "ok" and r.daily_total is not None]
    if totals:
        lines.append(total_line(totals[-1]))
    if skipped:
        lines.append(f"(一則訊息最多處理 {len(results)} 張,另外 {skipped} 張沒有處理)")
    return "\n".join(lines)


def build_reply(results: list[PhotoResult], skipped: int = 0) -> str:
    text = single_reply(results[0]) if len(results) == 1 and not skipped else multi_reply(results, skipped)
    # Names come from the model, which got them from strangers' photos: defuse @everyone, @here, <@id>.
    text = discord.utils.escape_mentions(text)
    return text[:DISCORD_LIMIT]
