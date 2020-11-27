import datetime


__all__ = (
    'format_dt', 'regional_indicator', 
    'keycap_digit', 'ZWSP'
)


ZWSP = '\N{ZERO WIDTH SPACE}'


def format_dt(dt: datetime.datetime) -> str:
    return dt.strftime('%F @ %T UTC')


def regional_indicator(char: str) -> str:
    return chr(0x1f1a5 + ord(char.upper()))


def keycap_digit(num: int) -> str:
    return (str(num).encode('utf-8') + b'\xe2\x83\xa3').decode('utf-8')


def ordinal(num: int) -> str:
    return f'{num}{"tsnrhtdd"[(num // 10 % 10 != 1) * (num % 10 < 4) * num % 10 :: 4]}'
