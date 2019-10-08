import asyncio
import datetime

import discord

import asyncpg
from donphan import Column, MaybeAcquire, Table

_active_timer = None
_bot = None


class _Timers(Table):
    id: int = Column(primary_key=True, auto_increment=True)
    created_at: datetime.datetime = Column(nullable=False, default='NOW()')
    expires_at: datetime.datetime = Column(nullable=False, index=True)
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

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return f'<Timer id={self.id} created_at={self.created_at} expires_at={self.expires_at} event_type={self.event_type}>'


async def get_active_timer(connection=None, days=7) -> Timer:
    # Fetch upcoming timer from database
    record = await _Timers.fetchrow_where(
        'expires_at < (CURRENT_DATE + $1::interval) ORDER BY expires_at LIMIT 1', (datetime.timedelta(days=days),), connection=connection)
    return Timer(record) if record else None


async def _wait_for_active_timers(connection=None, days=7) -> Timer:
    async with MaybeAcquire(connection=connection) as connection:

        # check database for active timer
        timer = await get_active_timer(connection=connection, days=days)

        # if timer was found return it
        if timer is not None:
            _bot._active_timer.set()
            return timer

        # otherwise wait for active timer
        _bot._active_timer.clear()
        _bot._current_timer = None
        await _bot._active_timer.wait()
        return await get_active_timer(connection=connection, days=days)


def _dispatch_timer_event(timer: Timer):
    event_name = f'{timer.event_type}_timer_complete'
    _bot.dispatch(event_name, *timer.args, **timer.kwargs)


async def _call_timer(timer: Timer):
    # delete timer from database
    await _Timers.delete_where('id = $1', (timer.id,))
    _dispatch_timer_event(timer)


async def _call_short_timer(seconds: int, timer: Timer):
    await asyncio.sleep(seconds)
    _dispatch_timer_event(timer)


async def _dispatch_timers():

    # Ensure timers table exists.
    await _Timers.create()

    try:
        while not _bot.is_closed():
            # fetch next timer from database
            timer = _bot._current_timer = await _wait_for_active_timers(days=40)
            now = datetime.datetime.utcnow()

            # if timer has not expired yet sleep
            if timer.expires_at >= now:
                to_sleep = (timer.expires_at - now).total_seconds()
                await asyncio.sleep(to_sleep)

            # dispatch the event
            await _call_timer(timer)

    except asyncio.CancelledError:
        pass
    except (OSError, discord.ConnectionClosed, asyncpg.PostgresConnectionError):
        _bot._timer_task.cancel()
        _bot._timer_task = _bot.loop.create_task(_dispatch_timers())
    except Exception as e:
        print(e)


async def create_timer(expires_at: datetime.datetime, event_type: str, *args, **kwargs):
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
        _bot.loop.create_task(_call_short_timer(delta, timer))
        return timer

    # Store the timer in the database
    record = await _Timers.insert(
        returning=_Timers.id,
        created_at=now,
        expires_at=expires_at,
        event_type=event_type,
        data={'args': args, 'kwargs': kwargs}
    )

    # Set the timer's ID
    timer.id = record[0]

    # Only set the data check if the timer can be waited for
    if delta <= (60 * 60 * 24 * 40):
        _bot._active_timer.set()

    # Check if the timer is earlier than the currently set timer
    if _bot._current_timer and expires_at < _bot._current_timer.expires_at:
        # Cancel the timer task and restart it
        _bot._timer_task.cancel()
        _bot._timer_task = _bot.loop.create_task(_dispatch_timers())

    return timer


async def delete_timer(record: asyncpg.Record):
    """Deletes an upcoming timer

    Args:
        record (asyncpg.Record): the timer's database record to delete.
    """
    await _Timers.delete_record(record)

    # if the current timer is being deleted
    if _bot._current_timer and _bot._current_timer.id == id:
        _bot._timer_task.cancel()
        _bot._timer_task = _bot.loop.create_task(_dispatch_timers())
