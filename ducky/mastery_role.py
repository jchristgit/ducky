import discord
from discord.ext import commands

from .db import db_cursor
from .league import LolApi


@commands.check
def is_bardians(ctx: commands.Context) -> bool:
    return ctx.message.guild is not None and ctx.message.guild.id == 172226206375084032


def find_matching_role(score: int) -> int:
    if score >= 5_000_000:
        return 1000812021085900891
    elif score >= 4_000_000:
        return 695832731090681937
    elif score >= 3_000_000:
        return 396411228890726402
    elif score >= 2_000_000:
        return 302850833488412682
    elif score >= 1_500_000:
        return 226864391050625024
    elif score >= 1_000_000:
        return 172782735910240257
    elif score >= 750_000:
        return 172782699679973376
    elif score >= 500_000:
        return 172782680713199616
    elif score >= 250_000:
        return 172782658454159361
    elif score >= 100_000:
        return 172782642062688258
    elif score >= 50_000:
        return 172782614749380608
    return 238774473531064322


class MasteryRole(commands.Cog):
    def __init__(self, dsn: str, lol_api: LolApi) -> None:
        self.dsn = dsn
        self.lol_api = lol_api

    @commands.command()
    @commands.guild_only()
    @commands.check(is_bardians)
    async def masteryrole(
        self, ctx: commands.Context, region: str, *, name_with_tagline: str
    ) -> None:
        """Assign a role for your mastery score."""

        async with db_cursor(self.dsn) as cursor:
            await cursor.execute(
                "SELECT id FROM champions WHERE guild_id = %s", (ctx.message.guild.id,)
            )
            champion_row = await cursor.fetchone()
            if champion_row is None:
                await ctx.channel.send(":x: no champion configured for this guild")
                return

        if "#" not in name_with_tagline:
            await ctx.channel.send(":no_entry_sign: please send your name together with your tagline, e.g. `+masteryrole EUW Ducky#Bot`")
            return

        name, tagline = name_with_tagline.split("#")
        puuid = self.lol_api.account_puuid(name, tagline)
        mastery = self.lol_api.champion_mastery(region, puuid, champion_row[0])["championPoints"]
        matching_role = find_matching_role(mastery)
        print(
            f"giving {ctx.message.author} role {matching_role} for "
            f"{mastery:,} points on {name_with_tagline!r} in {region}"
        )
        await ctx.message.author.add_roles(
            discord.Object(id=matching_role),
            reason=f"mastery score of {mastery:,} on {name_with_tagline} in {region}",
        )
        await ctx.send(":ok_hand: role added!")
