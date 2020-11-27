from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.ext import commands
from donphan.connection import MaybeAcquire

if TYPE_CHECKING:
    from .bot import Bot


class Context(commands.Context):
    bot: Bot
    message: discord.Message
    prefix: str
    command: commands.Command

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = MaybeAcquire(pool=self.bot._pool)
