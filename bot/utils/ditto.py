import asyncio
import datetime

from typing import Iterable

import discord
from discord.ext import commands

from bot.utils.timers import Timer, Timers, call_short_timer, dispatch_timers


class Bot(commands.Bot):

    def run(self, *args, **kwargs):

        # Start the timer task
        self._active_timer = asyncio.Event(loop=self.loop)
        self._current_timer = None
        self._timer_task = self.loop.create_task(dispatch_timers(self))

        # Login
        super().run(*args, **kwargs)

    async def create_timer(self, expires_at: datetime.datetime, event_type: str, *args, **kwargs):
        """Creates a new timer object.

        Args:
            expires_at (datetime.datetime): when the timer expires
            event_type (str): The timer event type
            *args: Any additional arguments
            **kwargs: Any additional keyword arguments
        """
        now = datetime.datetime.utcnow()
        timer = Timer.temporary(now, expires_at, event_type, *args, **kwargs)

        # Check if the timer expires relatively soon
        delta = (expires_at - now).total_seconds()
        if delta <= 60:
            self.loop.create_task(call_short_timer(self, delta, timer))
            return timer

        # Store the timer in the database
        record = await Timers.insert(
            returning=Timers.id,
            created_at=now,
            expires_at=expires_at,
            event_type=event_type,
            data={'args': args, 'kwargs': kwargs}
        )

        # Set the timer's ID
        timer.id = record[0]

        # Only set the data check if the timer can be waited for
        if delta <= (60 * 60 * 24 * 40):
            self._active_timer.set()

        # Check if the timer is earlier than the currently set timer
        if self._current_timer and expires_at < self._current_timer.expires_at:
            # Cancel the timer task and restart it
            self._timer_task.cancel()
            self._timer_task = self.loop.create_task(dispatch_timers(self))

    async def delete_timer(self, record):
        """Deletes an upcoming timer

        Args:
            record (asyncpg.Record): the timer's database record to delete.
        """
        await Timers.delete_record(record)

        # if the current timer is being deleted
        if self._current_timer and self._current_timer.id == id:
            self._timer_task.cancel()
            self._taks = self.loop.create_task(dispatch_timers)

    async def add_reactions(self, message: discord.Message, reactions: Iterable[discord.Emoji]):
        """Adds reactions to a message

        Args:
            reactions (): A set of reactions to add.
        """
        for reaction in reactions:
            asyncio.ensure_future(message.add_reaction(reaction))
