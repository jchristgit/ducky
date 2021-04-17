from typing import Any

from discord.ext import commands


class ErrorHandler(commands.Cog):
    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> Any:
        if isinstance(error, commands.MissingPermissions):
            await ctx.channel.send("sorry, but you are not allowed to run this command")
        else:
            return await ctx.bot.on_command_error(ctx, error)
