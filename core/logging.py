import asyncio
import datetime
import logging
import textwrap

from typing import Dict, List

import aiohttp

import discord
from discord.ext import tasks

from utils.strings import ZWSP

__all__ = ('EmbedWebhookLogger', 'WebhookHandler')


COLOURS: Dict[int, discord.Colour] = {
    logging.DEBUG: discord.Colour.light_grey(),
    logging.INFO: discord.Colour.gold(),
    logging.WARNING: discord.Colour.orange(),
    logging.ERROR: discord.Colour.red(),
    logging.CRITICAL: discord.Colour.dark_red(),
    logging.NOTSET: discord.Colour.dark_gray()
}


class EmbedWebhookLogger:

    def __init__(self, webhook_url: str, *, loop: asyncio.AbstractEventLoop = None):
        self.loop = loop or asyncio.get_event_loop()
        self._webhook_url = webhook_url
        self._lock = asyncio.Lock()
        self._to_log: List[discord.Embed] = list()

        self._loop.add_exception_type(discord.HTTPException)
        self._loop.start()

    def log(self, embed: discord.Embed):
        self._to_log.append(embed)

    @tasks.loop(seconds=5)
    async def _loop(self):
        while self._to_log:
            embeds = [self._to_log.pop(0) for _ in range(min(10, len(self._to_log)))]
            await self._webhook.send(embeds=embeds)

    @_loop.before_loop
    async def _before_loop(self):
        self._session = aiohttp.ClientSession()
        self._webhook = discord.Webhook.from_url(self._webhook_url, adapter=discord.AsyncWebhookAdapter(self._session))


class WebhookHandler(logging.Handler):
    
    def __init__(self, webhook_url, level=logging.NOTSET):
        super().__init__(level)
        self._webhook_logger = EmbedWebhookLogger(webhook_url)

    def emit(self, record: logging.LogRecord):
        self.format(record)

        message = f'{record.message}\n{record.exc_text or ""}'
        message = textwrap.shorten(message, width=1990, placeholder='...')

        self._webhook_logger.log(
            discord.Embed(
                colour=COLOURS.get(record.levelno),
                title=record.name,
                description=f"```py\n{message}\n```",
                timestamp=datetime.datetime.fromtimestamp(record.created)
            ).set_footer(text=f'{record.filename}:{record.lineno}')
        )
