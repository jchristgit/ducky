import contextlib

import aiopg

from .league import region_to_platform


@contextlib.asynccontextmanager
async def db_cursor(dsn: str) -> aiopg.Cursor:
    conn = await aiopg.connect(dsn, echo=True)
    try:
        cursor = await conn.cursor()
        yield cursor
    finally:
        cursor.close()
        conn.close()


async def add_summoner(region: str, name: str, tagline: str, puuid: str, guild_id: int, *, dsn) -> bool:
    """Add the given summoner. Return `True` on success, else `False` on conflict."""

    async with db_cursor(dsn) as cursor:
        platform = region_to_platform(region)
        if platform is None:
            raise ValueError(f"Unknown platform {platform!r}")

        await cursor.execute(
            (
                "INSERT INTO summoners (guild_id, platform, name, tagline, puuid) "
                "VALUES (%s, %s, %s, %s, %s) "
                "ON CONFLICT (guild_id, puuid, platform) "
                "DO NOTHING"
            ),
            (
                guild_id, platform.casefold(), name, tagline, puuid,
            ),
        )
        return bool(cursor.rowcount)


async def remove_summoner(puuid: str, guild_id: int, *, dsn) -> bool:
    """Remove the given summoner. Return `True` on success, else `False` if unknown."""

    async with db_cursor(dsn) as cursor:
        await cursor.execute(
            "DELETE FROM summoners WHERE guild_id = %s AND puuid = %s",
            (guild_id, puuid),
        )
        return bool(cursor.rowcount)
