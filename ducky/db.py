import contextlib

import aiopg


@contextlib.asynccontextmanager
async def db_cursor(dsn: str) -> aiopg.Cursor:
    conn = await aiopg.connect(dsn, echo=True)
    try:
        cursor = await conn.cursor()
        yield cursor
    finally:
        cursor.close()
        conn.close()
