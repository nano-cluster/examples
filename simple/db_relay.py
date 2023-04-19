#! /usr/bin/python -u

import asyncio

from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncConnection
from sqlalchemy.sql import text

from xrpc import App, log, StdIOApp

# used to interface with stdio rpc
app = App("db")
stdio_app = StdIOApp(app)



async def get_engine(name) -> AsyncEngine:
    # conn_str = "postgresql+asyncpg://scott:tiger@localhost/test"
    conn_str = "sqlite+aiosqlite:///database.db"
    engine = create_async_engine(conn_str)
    return engine

@app.method()
async def fetch_all(sql, params=None, connection=None):
    if not params:
        params = {}
    engine = await get_engine(connection)
    async with engine.begin() as con:
        conn: AsyncConnection = con
        result = await conn.execute(text(sql), params)
        items = [ dict(i) for i in result.fetchall() ]
    await engine.dispose()
    log("** fetch_all: ", items)
    return {"items": items}

def main():
    asyncio.run(stdio_app.loop())

if __name__ == "__main__":
    main()

