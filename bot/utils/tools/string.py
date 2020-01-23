import datetime

from typing import Union


__all__ = [
    'format_dt', 'regional_indicator', 'keycap_digit', 'rank_emoji', 'plural', 'ordinal'
]


def format_dt(dt: datetime.datetime):
    """Formats datetime strings.

    Args:
        dt: (datetime.datetime): The datetime object to format.
    """
    return dt.strftime('%F @ %T UTC')


def regional_indicator(c: str) -> str:
    """Returns a regional indicator emoji given a character."""
    return chr(0x1f1e6 - ord('A') + ord(c.upper()))


def keycap_digit(c: Union[int, str]) -> str:
    """Returns a keycap digit emoji given a character."""
    return (str(c).encode("utf-8") + b"\xe2\x83\xa3").decode("utf-8")


def rank_emoji(i: int) -> str:
    """Returns a rank emoji for a leaderboard."""
    if i < 3:
        return (
            '\N{FIRST PLACE MEDAL}',
            '\N{SECOND PLACE MEDAL}',
            '\N{THIRD PLACE MEDAL}',
        )[i]
    return '\N{SPORTS MEDAL}'


class plural:
    def __init__(self, value):
        self.value = value

    def __format__(self, format_spec):
        v = self.value
        singular, sep, plural = format_spec.partition('|')
        plural = plural or f'{singular}s'
        if abs(v) != 1:
            return f'{v} {plural}'
        return f'{v} {singular}'


def ordinal(n):
    """Determines The ordinal for a given integer."""
    return f'{n}{"tsnrhtdd"[(n // 10 % 10 != 1) * (n % 10 < 4) * n % 10 :: 4]}'
