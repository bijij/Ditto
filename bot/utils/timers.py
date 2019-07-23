import asyncio
import datetime

import discord
from discord.ext import commands

from donphan import Column, MaybeAcquire, Table


class Timers(Table):
    id: int = Column(primary_key=True, auto_increment=True)
    created_at: datetime.datetime = Column(nullable=False, default='NOW()')
    expires_at: datetime.datetime = Column(nullable=False)
    event_type: str = Column(nullable=False)
    data: dict = Column(nullable=False, default={})


class Timer:
    __slots__ = ('id', 'created_at', 'expires_at',
                 'event_type', 'args', 'kwargs')

    def __init__(self, record):
        self.id = record['id']
        self.created_at = record['created_at']
        self.expires_at = record['expires_at']
        self.event_type = record['event_type']
        data = record['data']
        self.args = data.get('args', [])
        self.kwargs = data.get('kwargs', {})

    @classmethod
    def temporary(cls, created_at, expires_at, event_type, *args, **kwargs):
        return cls(record={
            'id': None,
            'created_at': created_at,
            'expires_at': expires_at,
            'event_type': event_type,
            'data': {
                'args': args,
                'kwargs': kwargs
            }
        })

    def __eq__(self, other):
        try:
            return self.id == other.id
        except AttributeError:
            return False

    def __repr__(self):
        return f'<Timer id={self.id} created_at={self.created_at} expires_at={self.expires_at} event_type={self.event_type}>'


async def get_active_timer(connection=None, days=7) -> Timer:
    # Fetch upcoming timer from database
    record = await Timers.fetchrow_where('expires_at < (CURRENT_DATE + $1::interval) ORDER BY expires_at LIMIT 1', (datetime.timedelta(days=days),), connection=connection)
    return Timer(record) if record else None


async def wait_for_active_timers(bot: commands.Bot, connection=None, days=7) -> Timer:
    async with MaybeAcquire(connection=connection) as connection:

        # check database for active timer
        timer = await get_active_timer(connection=connection, days=days)

        # if timer was found return it
        if timer is not None:
            bot._active_timer.set()
            return timer

        # otherwise wait for active timer
        bot._active_timer.clear()
        bot._current_timer = None
        await bot._active_timer.wait()
        return await get_active_timer(connection=connection, days=days)


def dispatch_timer_event(bot: commands.bot, timer: Timer):
    event_name = f'{timer.event_type}_timer_complete'
    bot.dispatch(event_name, *timer.args, **timer.kwargs)


async def call_timer(bot: commands.Bot, timer: Timer):
    # delete timer from database
    await Timers.delete_where('id = $1', (timer.id,))
    dispatch_timer_event(bot, timer)


async def call_short_timer(bot: commands.Bot, seconds: int, timer: Timer):
    await asyncio.sleep(seconds)
    dispatch_timer_event(bot, timer)


async def dispatch_timers(bot: commands.Bot):

    await Timers.create_table()

    try:
        while not bot.is_closed():
            # fetch next timer from database
            timer = bot._current_timer = await wait_for_active_timers(bot, days=40)
            now = datetime.datetime.utcnow()

            # if timer has not expired yet sleep
            if timer.expires_at >= now:
                to_sleep = (timer.expires_at - now).total_seconds()
                await asyncio.sleep(to_sleep)

            # dispatch the event
            await call_timer(bot, timer)
    except asyncio.CancelledError:
        pass
    except (OSError, discord.ConnectionClosed):
        bot._timer_task.cancel()
        bot._timer_task = bot.loop.create_task(dispatch_timers(bot))
    except Exception as e:
        print(e)
