from discord.ext import commands


__all__ = [
    'auto_help'
]


async def _call_help(ctx: commands.Context):
    await ctx.send_help(ctx.command.parent)


def auto_help(func):
    """Automatically registers a help command for this group."""
    if not isinstance(func, commands.Group):
        raise TypeError('Auto help can only be applied to groups.')
    cmd = commands.Command(_call_help, name='help', hidden=True)
    func.add_command(cmd)
    return func
