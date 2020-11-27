from __future__ import annotations

import asyncio
import datetime

from typing import Optional, TYPE_CHECKING, Union

import asyncpg
import discord

from donphan import Column, Record, SQLType, Table

if TYPE_CHECKING:
    from .bot import Bot


class Timer:
    def __init__(self, bot: Bot, record: Record):
        self.__dict__.update(dict(record))
        self._bot = bot
        self.args = self.data.get("args", [])
        self.kwargs = self.data.get("kwargs", {})

    def __repr__(self):
        return "<Timer id={0.id} event_name={0.event_name} expires_at={0.expires_at}>".format(self)

    async def _delete(self):
        await Timers.delete(id=self.id)

    async def call(self):
        await self._delete()
        self._bot.dispatch(f"{self.event_name}_timer_complete", *self.args, **self.kwargs)

    async def delete(self):
        await self._delete()
        if Timers._current is self:
            Timers._restart_task(self._bot)


class Timers(Table, schema="core"):
    id: SQLType.Serial = Column(primary_key=True)
    created_at: SQLType.Timestamp = Column(default="NOW() AT TIME ZONE 'UTC'")
    expires_at: SQLType.Timestamp = Column(index=True)
    event_name: str = Column(nullable=False, index=True)
    data: SQLType.JSONB = Column(default="'{}'::jsonb")

    _active = asyncio.Event()

    @classmethod
    async def _get_active_timer(cls, *, days: int = 7) -> Optional[Timer]:
        record = await cls.fetchrow(expires_at__le=datetime.datetime.utcnow() + datetime.timedelta(days=days), order_by="expires_at ASC")
        return Timer(cls._bot, record) if record else None

    @classmethod
    async def _wait_for_active_timer(cls, *, days: int = 7) -> Timer:
        # Check DB for a timer
        timer = await cls._get_active_timer(days=days)

        # If timer was found return it
        if timer is not None:
            cls._active.set()
            return timer

        # Otherwise wait for a new timer
        cls._active.clear()
        cls._current = None
        await cls._active.wait()
        return await cls._wait_for_active_timer(days=days)

    @classmethod
    async def _dispatch_timers(cls):
        await cls._bot.wait_until_ready()

        try:
            while not cls._bot.is_closed():
                timer = cls._current_timer = await cls._wait_for_active_timer(days=40)
                await discord.utils.sleep_until(timer.expires_at)
                await timer.call()
        except asyncio.CancelledError:
            pass
        except (OSError, discord.ConnectionClosed, asyncpg.PostgresConnectionError):
            cls._restart_task()
        except Exception:
            await cls._bot.log.exception("Unhandled exception in internal timer task.")

    @classmethod
    def _restart_task(cls):
        cls._task.cancel()
        cls._task = cls._bot.loop.create_task(cls._dispatch_timers())

    @classmethod
    def start_task(cls, bot: Bot):
        cls._bot = bot
        cls._task = cls._bot.loop.create_task(cls._dispatch_timers())

    @classmethod
    async def create_timer(cls, event_name: str, *args, expires_at: datetime.datetime = None, expires_in: Union[float, datetime.timedelta] = None, **kwargs) -> Timer:

        if expires_at is None and expires_in is None:
            raise ValueError("Must pass in either expires_at and expires_in arguments.")

        if expires_at is not None and expires_in is not None:
            raise ValueError("Cannot pass both expires_at and expires_in arguments.")

        if isinstance(expires_in, (int, float)):
            expires_in = datetime.timedelta(seconds=expires_in)

        if isinstance(expires_in, datetime.timedelta):
            expires_at = datetime.datetime.utcnow() + expires_in
        else:
            raise TypeError("Invalid type supplied for expires_in expected datetime.timedelta or number.")

        if expires_at < datetime.datetime.utcnow():
            raise ValueError("Cannot create timer in the past.")

        # delta = expires_at - datetime.datetime.utcnow()

        data = {
            "args": args,
            "kwargs": kwargs
        }

        # Create new record in DB
        record = await cls.insert(returning="*", expires_at=expires_at, event_name=event_name, data=data)

        # Restart the timer task
        cls._restart_task()

        return Timer(record)
