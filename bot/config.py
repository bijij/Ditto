import os

import discord
import yaml

from bot.utils.tools import RawMessage

_bot: discord.Client = None


def load():
    with open('config.yml', encoding='UTF-8') as f:
        return yaml.load(f, Loader=yaml.FullLoader)


class HiddenRepr(str):
    def __repr__(self):
        return '<str with hidden value>'


class Object(discord.Object):
    def __init__(self, id, func):
        self._func = func
        super().__init__(id)

    def __getattribute__(self, name):
        if name in ['_func', 'id', 'created_at']:
            return object.__getattribute__(self, name)

        return getattr(self._func(), name, None)

    def __repr__(self):
        return getattr(self._func(), '__repr__', super().__repr__)()


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

    return HiddenRepr(os.getenv(key))


def _generate_constructor(func):

    def constructor(loader: yaml.Loader, node: yaml.Node):
        ids = [int(x) for x in loader.construct_scalar(node).split()]
        return Object(ids[-1], lambda: func(*ids))

    return constructor


class Config(yaml.YAMLObject):
    yaml_tag = u'!Config'

    def __init__(self, **kwargs):
        for name, value in kwargs:
            setattr(self, name, value)

    def __reload__(self):
        self.__dict__ = load().__dict__
        _bot.__version__ = self.VERSION

    def __repr__(self):
        return f'<Config {" ".join(f"{key}={repr(value)}" for key, value in self.__dict__.items())}>'


DISCORD_CONSTRUCTORS = [

    # Discord constructors
    ('Emoji', lambda e: _bot.get_emoji(e)),
    ('Guild', lambda g: _bot.get_guild(g)),
    ('User', lambda u: _bot.get_user(u)),

    # Discord Guild dependant constructors
    ('Channel', lambda g, c: _bot.get_guild(g).get_channel(c)),
    ('Member', lambda g, m: _bot.get_guild(g).get_member(m)),
    ('Role', lambda g, r: _bot.get_guild(g).get_role(r)),
    ('Message', lambda g, c, m: RawMessage(_bot, _bot.get_guild(g).get_channel(c), m))

]


# Add constructors
yaml.FullLoader.add_constructor('!Config', Config.from_yaml)
yaml.FullLoader.add_constructor('!ENV', _env_var_constructor)

# Add discord specific constructors
for key, func in DISCORD_CONSTRUCTORS:
    yaml.FullLoader.add_constructor(
        f'!{key}', _generate_constructor(func))

# Load the config
config: Config = load()
