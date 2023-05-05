#! /usr/bin/python -u

import asyncio

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    AsyncConnection,
    # async_sessionmaker,
    # AsyncSession,
)
from sqlalchemy.sql import text

from xrpc import App, log, StdIOApp

# used to interface with stdio rpc
app = App("db")
stdio_app = StdIOApp(app)

# async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(engine, expire_on_commit=False)
# async with async_session() as session:
#     async with session.begin():
#         query = session.query(myTable)
#         result = await session.execute(query)
#         column_names = query.statement.columns.keys()

async def get_engine(name) -> AsyncEngine:
    # conn_str = "postgresql+asyncpg://scott:tiger@localhost/test"
    conn_str = "sqlite+aiosqlite:///database.db"
    engine = create_async_engine(conn_str)
    return engine

@app.method()
async def execute(sql, params=None, connection=None):
    """
    execute a database query like INSERT or UPDATE
    pass params via `params` to avoid SQL injection
    """
    if not params:
        params = {}
    meta = {}
    engine = await get_engine(connection)
    async with engine.begin() as con:
        conn: AsyncConnection = con
        result = await conn.execute(text(sql), params)
        meta = {
            "rowcount": getattr(result, "rowcount", None),
            "lastrowid": getattr(result, "lastrowid", None),
        }
    await engine.dispose()
    return {"meta": meta}

@app.method()
async def fetch_all(sql, params=None, connection=None, kv=False):
    """
    fetch rows from a database query like SELECT statement
    set kv to True to return rows as key-value mapping instead of list
    you had better use list to avoid repeating keys with every row and is useful with panads

```
    res = pd.DataFrame(rows, columns=meta["columns"])
```
    """
    if not params:
        params = {}
    meta = {}
    engine = await get_engine(connection)
    async with engine.begin() as con:
        conn: AsyncConnection = con
        result = await conn.execute(text(sql), params)
        log(result._metadata)
        meta = {
            "columns": list(result._metadata.keys),
        }
        items = [ dict(i) if kv else tuple(i) for i in result.fetchall() ]
    await engine.dispose()
    log("** fetch_all: ", meta, items)
    return {"meta": meta, "items": items}

@app.method()
async def fetch_one(sql, params=None, connection=None, kv=False):
    """
    fetch a single row from a database query like SELECT statement
    set kv to True to return rows as key-value mapping instead of list

```
    res = pd.DataFrame(rows, columns=meta["columns"])
```
    """
    if not params:
        params = {}
    meta = {}
    engine = await get_engine(connection)
    async with engine.begin() as con:
        conn: AsyncConnection = con
        result = await conn.execute(text(sql), params)
        log(result._metadata)
        meta = {
            "columns": list(result._metadata.keys),
        }
        item = result.fetchone()
        if item is not None:
            item = dict(item) if kv else tuple(item)
    await engine.dispose()
    log("** fetch_one: ", meta, item)
    return {"meta": meta, "item": item}




def main():
    asyncio.run(stdio_app.loop())

if __name__ == "__main__":
    main()

