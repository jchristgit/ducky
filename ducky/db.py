import contextlib

import aiopg
import cassiopeia


@contextlib.asynccontextmanager
async def db_cursor(dsn: str) -> aiopg.Cursor:
    conn = await aiopg.connect(dsn, echo=True)
    try:
        cursor = await conn.cursor()
        yield cursor
    finally:
        cursor.close()
        conn.close()


async def add_summoner(summoner: cassiopeia.Summoner, guild_id: int, *, dsn) -> bool:
    """Add the given summoner. Return `True` on success, else `False` on conflict."""

    async with db_cursor(dsn) as cursor:
        await cursor.execute(
            (
                # the WHERE in the ON CONFLICT clause is unnecessary strictly speaking,
                # but - should this be a write-heavy table - would prevent generating
                # a lot of garbage and causing bloat
                "INSERT INTO summoners (guild_id, platform, name, tagline, puuid) "
                "VALUES (%s, %s, %s, %s, %s) "
                "ON CONFLICT DO UPDATE SET name = %s, tagline = %s "
                "WHERE name != %s OR tagline != %s"
            ),
            (
                guild_id, summoner.region.platform.value.casefold(), summoner.name, summoner.tagline, summoner.puuid,
                summoner.name, summoner.tagline,
                summoner.name, summoner.tagline,
            ),
        )
        return bool(cursor.rowcount)


async def remove_summoner(summoner: cassiopeia.Summoner, guild_id: int, *, dsn) -> bool:
    """Remove the given summoner. Return `True` on success, else `False` if unknown."""

    async with db_cursor(dsn) as cursor:
        await cursor.execute(
            "DELETE FROM summoners WHERE guild_id = %s AND platform = %s AND puuid = %s",
            (guild_id, summoner.region.platform.value.casefold(), summoner.puuid),
        )
        return bool(cursor.rowcount)
