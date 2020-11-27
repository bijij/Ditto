import discord

__all__ = (
    'RawMessage',
)

class RawMessage(discord.Message):
    """Stateless Discord Message object.
    Args:
        client (discord.Client): The client which will alter the message.
        channel (discord.TextChannel): The channel the message is in.
        message_id (int): The message's ID.
    """

    def __init__(self, client: discord.Client, channel: discord.TextChannel, message_id: int):
        self._state = client._connection
        self.id = message_id
        self.channel = channel

    def __repr__(self):
        return f'<RawMessage id={self.id} channel={self.channel}>'
