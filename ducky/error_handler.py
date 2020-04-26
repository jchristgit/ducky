from typing import Any

from discord.ext import commands


class ErrorHandler(commands.Cog):
    pass
    # @commands.Cog.listener()
    # async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> Any:
    #     if isinstance(error, commands.BadArgument):
    #         await ctx.channel.send(f"error: ``{error}``")
    #     else:
    #         return await ctx.bot.on_command_error(ctx, error)
