"""The Discord side: listen to one channel, queue photos, work through them one at a time."""

from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from dataclasses import dataclass

import discord

from foodie import replies
from foodie.config import (
    MAX_IMAGE_BYTES,
    MAX_IMAGES_PER_MESSAGE,
    MAX_QUEUE_JOBS,
    RATE_LIMIT_PHOTOS,
    RATE_LIMIT_WINDOW_SECONDS,
    Config,
)
from foodie.ledger import Ledger
from foodie.processor import PhotoResult, process_image

log = logging.getLogger("foodie.bot")

WAITING_EMOJI = "⏳"
IMAGE_SUFFIXES = (".jpg", ".jpeg", ".png", ".gif", ".webp")
# Reply to the message and ping only its author: never @everyone, roles or anyone named in the text.
REPLY_MENTIONS = discord.AllowedMentions(everyone=False, roles=False, users=False, replied_user=True)


@dataclass
class Job:
    message: discord.Message
    attachments: list[discord.Attachment]
    skipped: int
    caption: str


class RateLimiter:
    """At most `limit` photos per person per `window` seconds."""

    def __init__(self, limit: int, window: float) -> None:
        self.limit, self.window = limit, window
        self._seen: dict[int, deque[float]] = {}

    def allow(self, user_id: int, count: int) -> bool:
        now = time.monotonic()
        recent = self._seen.setdefault(user_id, deque())
        while recent and now - recent[0] > self.window:
            recent.popleft()
        if len(recent) + count > self.limit:
            return False
        recent.extend([now] * count)
        return True


def is_image(attachment: discord.Attachment) -> bool:
    kind = (attachment.content_type or "").lower()
    return kind.startswith("image/") or attachment.filename.lower().endswith(IMAGE_SUFFIXES)


class FoodieBot(discord.Client):
    def __init__(self, cfg: Config, ledger: Ledger) -> None:
        intents = discord.Intents.default()
        intents.message_content = True  # without this Discord hides attachments from bots
        super().__init__(intents=intents)
        self.cfg = cfg
        self.ledger = ledger
        self.queue: asyncio.Queue[Job] = asyncio.Queue(maxsize=MAX_QUEUE_JOBS)
        self.limiter = RateLimiter(RATE_LIMIT_PHOTOS, RATE_LIMIT_WINDOW_SECONDS)
        self._worker: asyncio.Task | None = None
        self._current: Job | None = None  # the job being worked on right now
        self._warned_reaction = False

    async def setup_hook(self) -> None:
        self._worker = asyncio.create_task(self._work_forever())

    async def on_ready(self) -> None:
        channel = self.get_channel(self.cfg.channel_id)
        if channel is None:
            log.warning("看不到 CHANNEL_ID=%s 這個頻道。請確認 ID 正確,而且 bot 已被邀進該 Server。", self.cfg.channel_id)
        else:
            log.info("已上線:%s(bot id=%s),正在聽頻道 #%s", self.user, getattr(self.user, "id", "?"), getattr(channel, "name", "?"))

    async def close(self) -> None:
        """Shutting down: take the ⏳ off every message that will now never be answered."""
        abandoned = [self._current] if self._current else []
        while True:
            try:
                abandoned.append(self.queue.get_nowait())
            except asyncio.QueueEmpty:
                break
        if self._worker:
            self._worker.cancel()
        for job in abandoned:
            await self._unreact(job.message)
        await super().close()

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or message.channel.id != self.cfg.channel_id:
            return
        images = [a for a in message.attachments if is_image(a)]
        if not images:
            return

        if self.queue.full():
            await self._reply(message, replies.BUSY_TEXT)
            return
        taken = images[:MAX_IMAGES_PER_MESSAGE]
        if not self.limiter.allow(message.author.id, len(taken)):
            await self._reply(message, replies.TOO_FAST_TEXT)
            return

        await self._react(message)
        self.queue.put_nowait(Job(message, taken, len(images) - len(taken), message.content or ""))
        log.info("收到 %s 的 %d 張照片,排隊中(前面有 %d 則)", message.author.display_name, len(taken), self.queue.qsize() - 1)

    async def _work_forever(self) -> None:
        """One job at a time, so there is never more than one `claude -p` running."""
        while True:
            job = await self.queue.get()
            self._current = job
            try:
                await self._handle(job)
            except Exception:
                log.exception("處理訊息時發生意外")
                await self._reply(job.message, replies.FAILED_TEXT)
            finally:
                await self._unreact(job.message)  # ⏳ must never stay behind
                self._current = None
                self.queue.task_done()

    async def _handle(self, job: Job) -> None:
        uploader = job.message.author.display_name
        uploader_id = str(job.message.author.id)
        results: list[PhotoResult] = []
        for attachment in job.attachments:  # in order, so each row's daily total builds on the last
            results.append(await self._one_photo(attachment, uploader, uploader_id, job.caption))
        await self._reply(job.message, replies.build_reply(results, job.skipped))

    async def _one_photo(self, attachment: discord.Attachment, uploader: str, uploader_id: str, caption: str) -> PhotoResult:
        if attachment.size > MAX_IMAGE_BYTES:
            return PhotoResult("too_big")
        try:
            data = await attachment.read()
        except Exception as exc:
            log.warning("下載圖片失敗:%s(%s)", attachment.filename, exc)
            return PhotoResult("failed")
        try:
            return await asyncio.to_thread(process_image, self.cfg, self.ledger, data, uploader, uploader_id, caption)
        except Exception:
            log.exception("處理一張照片時發生意外(其他張照片不受影響)")
            return PhotoResult("failed")

    # The three helpers below talk to Discord and must never raise: one failed reply or reaction
    # (message deleted, network blip, missing permission) may not stop the queue behind it.

    async def _reply(self, message: discord.Message, text: str) -> None:
        try:
            await message.reply(text, allowed_mentions=REPLY_MENTIONS, mention_author=True)
        except Exception as exc:
            log.warning("回覆失敗:%s", exc)

    async def _react(self, message: discord.Message) -> None:
        try:
            await message.add_reaction(WAITING_EMOJI)
        except discord.Forbidden:
            if not self._warned_reaction:
                self._warned_reaction = True
                log.warning("沒有 Add Reactions 權限,加不了 %s。請照 docs/discord-bot-setup.md 重新授權 bot。", WAITING_EMOJI)
        except Exception as exc:
            log.warning("加 %s 失敗:%s", WAITING_EMOJI, exc)

    async def _unreact(self, message: discord.Message) -> None:
        try:
            await message.remove_reaction(WAITING_EMOJI, self.user)
        except Exception as exc:
            log.debug("移除 %s 沒成功(訊息可能已刪除,或當初就沒加上去):%s", WAITING_EMOJI, exc)
