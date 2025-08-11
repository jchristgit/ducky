import asyncio
import datetime
import io
import operator
import random
from typing import Set

import discord
from discord.ext import commands

from . import db
from . import league


@commands.check
def may_invoke(ctx: commands.Context) -> bool:
    allowed = ctx.message.author.id in (
        170929033981329408,  # Cas
        162000660626276353,  # Fanushkah
        265739617532116992,  # Marcus
        107951056813559808,  # Blitze
        80838982283304960,  # Jab
        247821704431140864,  # Mouse
        241751185101553664,  # Venm
    )
    if not allowed:
        print("rejecting disallowed user %s", ctx.message.author)
    return allowed


def go_for_phrase() -> str:
    return random.choice(
        # this will take a while, go...
        (
            # healthy
            'on a walk',
            'ventilate your room',
            'stand up and walk for a moment',
            'cook some food',
            'hydrate yourself',

            # friendly
            'grab a coffee',
            'make some tea',
            'watch the sky',
            'read the news',
            'get a snack',
            'eat something',
            'admire the sun',
            'call a friend and ask how they\'re doing',
            'text a friend and ask how they\'re doing',
            'find some new music',

            # less friendly
            'for a piss',
            'outside',

            # revealing intentions
            'submit to your robot overlords',
            'pray to bolt',
        )
    )


class MasteryTable(commands.Cog):
    """Mastery table management."""

    def __init__(self, dsn: str, lol_api: league.LolApi) -> None:
        self.dsn = dsn
        self.builds_running: Set[int] = set()
        self.lol_api = lol_api

    @commands.guild_only()
    @commands.check_any(commands.is_owner(), may_invoke)
    @commands.group()
    async def summoner(self, ctx: commands.Context) -> None:
        """Summoner management."""

    @commands.guild_only()
    @commands.check_any(commands.is_owner(), may_invoke)
    @summoner.command(name='add')
    async def summoner_add(
        self, ctx: commands.Context, region: str, *, name_with_tagline: str
    ) -> None:
        """Add a summoner to the mastery sidebar."""

        name, tagline = name_with_tagline.split("#")
        puuid = self.lol_api.account_puuid(name, tagline)
        success = await db.add_summoner(
            region, name, tagline, puuid, ctx.message.guild.id, dsn=self.dsn,
        )
        if success:
            print(
                f"{ctx.message.author} added {name_with_tagline} on {region} for {ctx.message.guild.name}"
            )
            await ctx.channel.send(":ok_hand: summoner added")
        else:
            await ctx.channel.send(":x: summoner already added")

    @commands.guild_only()
    @commands.check_any(commands.is_owner(), may_invoke)
    @summoner.command(name='remove')
    async def summoner_remove(
        self, ctx: commands.Context, region: str, *, name_with_tagline: str
    ) -> None:
        """Remove a summoner to the mastery sidebar."""

        name, tagline = name_with_tagline.split("#")
        puuid = self.lol_api.account_puuid(name, tagline)
        removed = await db.remove_summoner(puuid, ctx.message.guild.id, dsn=self.dsn)
        if removed:
            await ctx.channel.send(":ok_hand: summoner removed")
        else:
            await ctx.channel.send(":x: unknown summoner")

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
            async with db.db_cursor(self.dsn) as cursor:
                await cursor.execute(
                    "SELECT entry_id, id FROM champions WHERE guild_id = %s",
                    (ctx.message.guild.id,),
                )
                champion_row = await cursor.fetchone()
                if champion_row is None:
                    await ctx.channel.send(":x: guild champion must be configured first")
                    return None

                await cursor.execute(
                    (
                        "SELECT entry_id, puuid, upper(platform::text), name, tagline "
                        "FROM summoners "
                        "WHERE guild_id = %s"
                    ),
                    (ctx.message.guild.id,),
                )
                summoners = await cursor.fetchall()
                if not summoners:
                    await ctx.channel.send(":x: no summoners added")
                    return None

                await ctx.channel.send(f":ok: starting build for {len(summoners)} summoners")

                if len(summoners) >= 20:
                    await ctx.channel.send(
                        f":information_source: this will take a while, why not go {go_for_phrase()}?"
                    )

                masteries = []
                loop = asyncio.get_event_loop()
                for (entry_id, puuid, platform, name, tagline) in summoners:
                    mastery = await loop.run_in_executor(
                        None,
                        lambda: self.lol_api.champion_mastery(
                            # cough
                            region_or_platform=platform,
                            puuid=puuid,
                            champion_id=champion_row[1],
                        )
                    )
                    summoner_name = f"{name}#{tagline}"
                    points = mastery["championPoints"]

                    # Do not add users with score of 0
                    if points:
                        last_playtime = datetime.datetime.fromtimestamp(mastery["lastPlayTime"] / 1000)
                        masteries.append((summoner_name, platform.upper(), points))

                        query = (
                            """
                            INSERT INTO summoner_champion_masteries
                                (champion_entry, summoner_entry, score, last_change)
                            VALUES
                                (%s, %s, %s, %s)
                            ON CONFLICT
                                (champion_entry, summoner_entry)
                            DO UPDATE SET
                                last_change = EXCLUDED.last_change,
                                score = EXCLUDED.score
                            """
                        )

                        await cursor.execute(
                            query,
                            (champion_row[0], entry_id, points, last_playtime),
                        )

                    else:
                        # Remove users who never played the champion
                        await cursor.execute("DELETE FROM summoners WHERE entry_id = %s", (entry_id,))
                        await ctx.channel.send(
                            f":information_source: player `{name}` on "
                            f"`{platform}` never played configured champion, "
                            "automatically dropped from table"
                        )
                        print(f"auto-drop {name} on {platform} (eid={entry_id})")

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
            await ctx.channel.send(":receipt: build done", file=table)

        except Exception:
            await ctx.channel.send(
                f":warning: sorry, something crashed. congratulations <@{ctx.bot.owner_id}>"
            )
            raise

        finally:
            self.builds_running.remove(ctx.message.guild.id)

    @commands.guild_only()
    @commands.check_any(commands.is_owner(), may_invoke)
    @table.command(name='old')
    async def table_old(self, ctx: commands.Context, minscore: int, *, age: str = '2 weeks') -> None:
        """Find old summoners in the mastery table.

        This uses cached information in the database, and should thus
        ideally be used after a table build when the cache has been
        refreshed.

        The command takes two arguments:
        - `minscore` determines the minimum score that a user should have.
          Users with a score higher than the number included here will not
          be shown in the response.
        - `age` should be the age of entries in the database. By default,
          summoners that have not played the champion in the past two weeks
          are returned.
        """

        async with db.db_cursor(self.dsn) as cursor:
            await cursor.execute(
                """
                SELECT
                    summoners.puuid,
                    summoners.name,
                    summoners.tagline,
                    upper(summoners.platform::text),
                    summoner_champion_masteries.score,
                    now() AT TIME ZONE 'utc' - summoner_champion_masteries.last_change AS delta
                FROM
                    champions,
                    summoners,
                    summoner_champion_masteries
                WHERE
                    champions.guild_id = %s
                    AND summoner_champion_masteries.champion_entry = champions.entry_id
                    AND summoner_champion_masteries.summoner_entry = summoners.entry_id
                    AND summoner_champion_masteries.score < %s
                    AND (now() AT TIME ZONE 'utc') - summoner_champion_masteries.last_change > %s::interval
                ORDER BY
                    delta DESC
                """,
                (ctx.guild.id, minscore, age),
            )
            summoners = await cursor.fetchall()

        if summoners:
            await ctx.channel.send(
                f":information_source: {len(summoners)} summoners fetched, "
                f"resolving IDs and displaying top {min(len(summoners), 8)}"
            )

            entries = []
            async with ctx.typing():
                for (_puuid, name, tagline, platform, score, delta) in summoners[:8]:
                    interval_head, *_tail = str(delta).split(', ')
                    entries.append(
                        f"- {platform} player `{name}#{tagline}` "
                        f" at `{score:,}` points, changed {interval_head} ago"
                    )

                await ctx.channel.send("\n".join(entries))
            await ctx.channel.send(":ok_hand: listing complete")

        else:
            await ctx.channel.send(
                f":information_source: no summoners matching query found"
            )
            return

    @commands.guild_only()
    @commands.check_any(commands.is_owner(), may_invoke)
    @table.command(name='below')
    async def table_below(self, ctx: commands.Context, score: int) -> None:
        """Find summoners below the given score."""

        command = ctx.bot.get_command('table old')
        await ctx.invoke(command, minscore=score, age='1 second')
