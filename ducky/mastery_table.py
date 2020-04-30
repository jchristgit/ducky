import asyncio
import contextlib
import functools
import io
import operator
from typing import Set

import aiopg
import cassiopeia
import discord
import psycopg2.errors
from cassiopeia import Champion, Region, Platform, Summoner
from discord.ext import commands

from .converters import as_region
from .db import db_cursor


@commands.check
def may_invoke(ctx: commands.Context) -> bool:
    allowed = ctx.message.author.id in (
        170929033981329408,  # Cas
        162000660626276353,  # Fanushkah
        265739617532116992,  # Marcus
        107951056813559808,  # Blitze
        80838982283304960,  # Jab
        247821704431140864,  # Mouse
    )
    if not allowed:
        print("rejecting disallowed user %s", ctx.message.author)
    return allowed


class MasteryTable(commands.Cog):
    """Mastery table management."""

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        self.builds_running: Set[int] = set()

    @commands.guild_only()
    @commands.check_any(commands.is_owner(), may_invoke)
    @commands.group()
    async def summoner(self, ctx: commands.Context) -> None:
        """Summoner management."""

    @commands.guild_only()
    @commands.check_any(commands.is_owner(), may_invoke)
    @summoner.command(name='add')
    async def summoner_add(
        self, ctx: commands.Context, region: as_region, *, name: str
    ) -> None:
        """Add a summoner to the mastery sidebar."""

        summoner = Summoner(region=region, name=name)
        summoner_id = await asyncio.get_event_loop().run_in_executor(
            None, lambda: summoner.id
        )  # noblock event loop
        async with db_cursor(self.dsn) as cursor:
            try:
                await cursor.execute(
                    "INSERT INTO summoners (guild_id, id, platform) VALUES (%s, %s, %s)",
                    (
                        ctx.message.guild.id,
                        summoner_id,
                        region.platform.value.casefold(),
                    ),
                )
            except psycopg2.errors.UniqueViolation:
                await ctx.channel.send("summoner already added")
            else:
                print(
                    f"{ctx.message.author} added {name} on {region.value} for {ctx.message.guild.name}"
                )
                await ctx.channel.send("summoner added")

    @commands.guild_only()
    @commands.check_any(commands.is_owner(), may_invoke)
    @commands.group()
    async def table(self, ctx: commands.Context) -> None:
        """Table building."""

    @commands.guild_only()
    @commands.check_any(commands.is_owner(), may_invoke)
    @table.command(name='build')
    async def table_build(self, ctx: commands.Context) -> None:
        """Build the mastery table."""

        if ctx.message.guild.id in self.builds_running:
            await ctx.channel.send("build already running")
            return

        self.builds_running.add(ctx.message.guild.id)

        try:
            async with db_cursor(self.dsn) as cursor:
                await cursor.execute(
                    "SELECT id FROM champions WHERE guild_id = %s",
                    (ctx.message.guild.id,),
                )
                champion_row = await cursor.fetchone()
                if champion_row is None:
                    await ctx.channel.send("guild champion must be configured first")
                    return None

                await cursor.execute(
                    "SELECT id, upper(platform::text) FROM summoners WHERE guild_id = %s",
                    (ctx.message.guild.id,),
                )
                summoners = await cursor.fetchall()
                if not summoners:
                    await ctx.channel.send("no summoners added")
                    return None

            await ctx.channel.send(f"starting build for {len(summoners)} summoners")
            champion = Champion(
                id=champion_row[0], region=Platform(summoners[0][1]).region
            )
            masteries = []
            loop = asyncio.get_event_loop()
            for (id_, platform) in summoners:
                region = Platform(platform).region
                summoner = Summoner(id=id_, region=region)
                masterygetter = functools.partial(
                    cassiopeia.get_champion_mastery,
                    champion=champion,
                    summoner=summoner,
                    region=region,
                )
                mastery = await loop.run_in_executor(None, masterygetter)
                summoner_name = await loop.run_in_executor(None, lambda: summoner.name)
                masteries.append((summoner_name, region.value, mastery.points))

            sorted_masteries = sorted(
                masteries, key=operator.itemgetter(2), reverse=True
            )
            head = [
                r'\# | Name | Region | Points',
                '---:|------|--------|-------',
            ]
            for position, (name, region, points) in enumerate(
                sorted_masteries, start=1
            ):
                head.append(f'{position} | {name} | {region} | {points:,}')

            output = io.BytesIO('\n'.join(head).encode())
            table = discord.File(fp=output, filename='table.txt')
            await ctx.channel.send("build done", file=table)

        finally:
            self.builds_running.remove(ctx.message.guild.id)
