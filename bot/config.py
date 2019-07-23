import os
from dataclasses import dataclass, field
from types import LambdaType
from typing import Any, Dict, List, Mapping

import discord
import yaml

_bot = None


def _env_var_constructor(loader: yaml.Loader, node: yaml.Node):
    """Implements a custom YAML tag for loading optional environment variables.
    If the environment variable is set it returns its value. 
    Otherwise returns `None`.

    Example usage:
        key: !ENV 'KEY'
    """
    if node.id == 'scalar':
        value = loader.construct_scalar(node)
        key = str(value)

    else:
        raise TypeError('Expected a string')

    return os.getenv(key)


def _guild_constructor(loader: yaml.Loader, node: yaml.Node):
    """Implements a custom YAML tak for loading `discord.Guild` objects.

    Example usage:
        key: !Guild guild_id
    """
    guild_id = int(loader.construct_scalar(node))
    return lambda: _bot.get_guild(guild_id)


def _channel_constructor(loader: yaml.Loader, node: yaml.Node):
    """Implements a custom YAML tak for loading `discord.abc.GuildChannel` objects.

    Example usage:
        key: !Channel guild_id channel_id
    """
    guild_id, channel_id = [int(x)
                            for x in loader.construct_scalar(node).split()]
    return lambda: _bot.get_guild(guild_id).get_channel(channel_id)


def _role_constructor(loader: yaml.Loader, node: yaml.Node):
    """Implements a custom YAML tak for loading `discord.Role` objects.

    Example usage:
        key: !Role guild_id role_id
    """
    guild_id, role_id = [int(x)
                         for x in loader.construct_scalar(node).split()]
    return lambda: _bot.get_guild(guild_id).get_role(role_id)


def _member_constructor(loader: yaml.Loader, node: yaml.Node):
    """Implements a custom YAML tak for loading `discord.Member` objects.

    Example usage:
        key: !Member guild_id user_id
    """
    guild_id, member_id = [int(x)
                           for x in loader.construct_scalar(node).split()]
    return lambda: _bot.get_guild(guild_id).get_member(member_id)


def _user_constructor(loader: yaml.Loader, node: yaml.Node):
    """Implements a custom YAML tak for loading `discord.User` objects.

    Example usage:
        key: !User user_id
    """
    user_id = int(loader.construct_scalar(node))
    return lambda: _bot.get_user(user_id)


def _emoji_constructor(loader: yaml.Loader, node: yaml.Node):
    """Implements a custom YAML tak for loading `discord.Emoji` objects.

    Example usage:
        key: !Emoji emoji_id
    """
    emoji_id = int(loader.construct_scalar(node))
    return lambda: _bot.get_emoji(emoji_id)


def _evaluate_lambda(value):
    # Handle if object is list
    if isinstance(value, list):
        for index, item in enumerate(value):
            value[index] = _evaluate_lambda(item)

    # Handle if object is dict
    if isinstance(value, dict):
        for key, item in list(value.items()):
            value[_evaluate_lambda(key)] = _evaluate_lambda(item)

    # Handle if object is lambda function
    if isinstance(value, LambdaType):
        value = value()

    return value


class Config(yaml.YAMLObject):
    yaml_tag = u'!Config'

    def __init__(self, **kwargs):
        for name, value in kwargs:
            setattr(self, name, value)

    def __getattribute__(self, name):
        value = object.__getattribute__(self, name)
        return _evaluate_lambda(value)

    def __repr__(self):
        return f"<Config {' '.join(f'{key}={repr(value)}' for key, value in self.__dict__.items())}>"


CONSTRUCTORS = [

    # General constructors
    ("Config", Config.from_yaml),
    ("ENV", _env_var_constructor),


    # Discord constructors
    ("Emoji", _emoji_constructor),
    ("Guild", _guild_constructor),
    ("User", _user_constructor),

    # Discord Guild dependant constructors
    ("Channel", _channel_constructor),
    ("Member", _member_constructor),
    ("Role", _role_constructor)
]

# Add constructors
for key, constructor in CONSTRUCTORS:
    yaml.FullLoader.add_constructor(f'!{key}', constructor)

# Load the config
with open("config.yml", encoding="UTF-8") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)  # type: Config
