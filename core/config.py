from __future__ import annotations

import os
import pathlib

import discord
import yaml

from typing import Any, Type, TypeVar, TYPE_CHECKING, Union

try:
    import dotenv
    dotenv.load_dotenv()
except ImportError:
    pass

from utils.objects import RawMessage

if TYPE_CHECKING:
    from .bot import Bot


class Object(discord.Object):
    yaml_tag = u'!Object'

    def _func(self, id):
        return discord.Object(id)

    def __init__(self, bot: Bot, *ids: int):
        self._bot = bot
        self._ids = ids
        super().__init__(ids[-1])

    def __getattribute__(self, name: str) -> Any:
        if name in ('_bot', '_ids', '_func', 'id', 'created_at'):
            return object.__getattribute__(self, name)
        return getattr(self._func(*self._ids), name)

    def __repr__(self) -> str:
        try:
            callable = self._func(*self.ids).__repr__
        except AttributeError:
            callable = super().__repr__
        return callable()


class Emoji(Object):
    yaml_tag = u'!Emoji'

    def _func(self, id):
        return self._bot.get_emoji(id)


class Guild(Object):
    yaml_tag = u'!Guild'

    def _func(self, id):
        return self._bot.get_guild(id)


class User(Object):
    yaml_tag = u'!User'

    def _func(self, id):
        return self._bot.get_user(id)


class Channel(Object):
    yaml_tag = u'!Channel'

    def _func(self, guild_id, channel_id):
        return self._bot.get_guild(guild_id).get_channel(channel_id)


class Member(Object):
    yaml_tag = u'!Member'

    def _func(self, guild_id, user_id):
        return self._bot.get_guild(guild_id).get_member(user_id)


class Role(Object):
    yaml_tag = u'!Role'

    def _func(self, guild_id, role_id):
        return self._bot.get_guild(guild_id).get_role(role_id)


class Message(Object):
    yaml_tag = u'!Message'

    def _func(self, guild_id, channel_id, message_id):
        return RawMessage(self._bot, self._bot.get_guild(guild_id).get_channel(channel_id), message_id)


def _env_var_constructor(loader: yaml.Loader, node: yaml.Node) -> str:
    if node.id == 'scalar':
        value = loader.construct_scalar(node)
        key = str(value)

    else:
        raise TypeError('Expected a string')

    return str(os.getenv(key))


class Config(yaml.YAMLObject):
    yaml_tag = u'!Config'

    def __init__(self, **kwargs):
        for name, value in kwargs:
            setattr(self, name, value)

    def __repr__(self):
        return f'<Config {" ".join(f"{key}={repr(value)}" for key, value in self.__dict__.items())}>'

    @classmethod
    def from_file(cls, bot: Bot, file: Union[pathlib.Path, str]) -> Config:

        class BotLoader(yaml.FullLoader):
            ...

        T = TypeVar('T', bound=Object)

        def generate_constructor(type: Type[T]):

            def constructor(loader: yaml.Loader, node: yaml.Node) -> T:
                ids = [int(x) for x in loader.construct_scalar(node).split()]
                return type(bot, *ids)

            return constructor

        for type in (Object, Emoji, Guild, User, Channel, Member, Role, Message):
            BotLoader.add_constructor(type.yaml_tag, generate_constructor(type))

        BotLoader.add_constructor(cls.yaml_tag, cls.from_yaml)
        BotLoader.add_constructor('!ENV', _env_var_constructor)

        with open(file, encoding='UTF-8') as f:
            return yaml.load(f, Loader=BotLoader)
