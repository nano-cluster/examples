#! /usr/bin/python -u

import sys
import asyncio

import argparse

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
url_by_name = {}
engines_by_name = {}

# async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(engine, expire_on_commit=False)
# async with async_session() as session:
#     async with session.begin():
#         query = session.query(myTable)
#         result = await session.execute(query)
#         column_names = query.statement.columns.keys()

async def get_engine(name) -> AsyncEngine:
    # conn_str = "postgresql+asyncpg://scott:tiger@localhost/test"
    # conn_str = "sqlite+aiosqlite:///database.db"
    if not name:
        name="default"
    engine = engines_by_name.get(name, None)
    if engine is not None:
        return engine
    conn_str = url_by_name[name]
    engine = create_async_engine(conn_str)
    engines_by_name[name] = engine
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
    #log(f"connection {connection}")
    engine = await get_engine(connection)
    async with engine.begin() as con:
        conn: AsyncConnection = con
        result = await conn.execute(text(sql), params)
        meta = {
            "rowcount": getattr(result, "rowcount", None),
            "lastrowid": getattr(result, "lastrowid", None),
        }
    #await engine.dispose()
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
        #log(result._metadata)
        meta = {
            "columns": list(result._metadata.keys),
        }
        items = [ i._asdict() if kv else tuple(i) for i in result.fetchall() ]
    #await engine.dispose()
    #log("** fetch_all: ", meta, items)
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
    #log("db connection", connection)
    engine = await get_engine(connection)
    async with engine.begin() as con:
        conn: AsyncConnection = con
        result = await conn.execute(text(sql), params)
        #log(result._metadata)
        meta = {
            "columns": list(result._metadata.keys),
        }
        item = result.fetchone()
        if item is not None:
            item = dict(item) if kv else tuple(item)
    #await engine.dispose()
    #log("** fetch_one: ", meta, item)
    return {"meta": meta, "item": item}




def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument(
        "-c", "--connection",
        metavar="NAME=URL",
        action="append",
        help="Add named connection string url (can be used multiple times) -c 'default=postgresql+asyncpg://scott:tiger@localhost/test' -c 'db2=sqlite+aiosqlite:///database.db'",
    )
    args = parser.parse_args()
    for name_url in args.connection or []:
        name, url  = name_url.split("=", 1) if "=" in name_url else ("default", name_url)
        url_by_name[name] = url
    if len(url_by_name)==0:
        parser.print_help()
        sys.exit(-1)
    asyncio.run(stdio_app.loop())

if __name__ == "__main__":
    main()

