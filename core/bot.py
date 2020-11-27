import datetime
import logging

from functools import cached_property
from typing import Optional

from donphan import create_pool, create_tables, create_types, create_views

import discord
from discord.ext import commands
from donphan.connection import MaybeAcquire

from .config import Config
from .context import Context
from .help import EmbedHelpCommand
from .logging import WebhookHandler
from .timers import Timers


class Bot(commands.Bot):

    def __init__(self, *, config: str):
        self.config = Config.from_file(self, config)

        # Setup logging
        self.log = logging.getLogger(__name__)

        webhook_handler = WebhookHandler(self.config.logging.webhook_url)

        file_handler = logging.FileHandler(f'{self.config.app_name}.log')
        file_handler.setFormatter(logging.Formatter(
            '{asctime} - {module}:{levelname} - {message}', style='{'
        ))

        log = logging.getLogger()
        log.setLevel(self.config.logging.level)
        log.addHandler(webhook_handler)
        log.addHandler(file_handler)
        log.addHandler(logging.StreamHandler())

        # Setup bot
        self.start_time = datetime.datetime.max

        prefix = commands.when_mentioned if self.prefix is None else commands.when_mentioned_or(self.prefix)
        allowed_mentions = discord.AllowedMentions.none()  # <3 Moogy
        intents = discord.Intents.all()

        super().__init__(
            command_prefix=prefix,
            help_command=EmbedHelpCommand(),
            allowed_mentions=allowed_mentions,
            intents=intents
        )

        # Load extensions
        for extension in self.config.extensions:
            try:
                self.load_extension(extension)
            except Exception:
                self.log.exception(f'Failed to load extension {extension}\n')

    @cached_property
    def prefix(self) -> Optional[str]:
        try:
            return self.config.bot.prefix
        except AttributeError:
            return None

    @property
    def uptime(self) -> datetime.timedelta:
        return max(datetime.datetime.utcnow() - self.start_time, datetime.timedelta())

    async def process_commands(self, message: discord.Message):
        if message.author.bot:
            return

        ctx = await self.get_context(message, cls=Context)
        await self.invoke(ctx)

    async def on_ready(self):
        self.log.info(f'Logged in as {self.user} ({self.user.id})')
        
        # Fetch bot owner
        await self.is_owner(self.user)
        if self.owner_id:
            self.owner = self.get_user(self.owner_id)

    async def on_error(self, event_method: str, *args, **kwargs):
        self.log.exception(f'Ignoring exception in {event_method}\n')

    async def connect(self, *args, **kwargs):

        # connect to DB
        dsn = "postgres://{0.user}:{0.password}@{0.hostname}/{0.database}".format(self.config.database)
        self._pool = await create_pool(dsn)
        self.db = MaybeAcquire(pool=self._pool)

        await create_types()
        await create_tables()
        await create_views()

        Timers.start_task(self)

        # Login
        self.start_time = datetime.datetime.utcnow()
        return await super().connect(*args, **kwargs)

    def run(self, *args, **kwargs):
        super().run(self.config.bot.token, *args, **kwargs)
