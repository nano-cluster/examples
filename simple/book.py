#! /usr/bin/python -u

import random
import asyncio

from xrpc import App, log, StdIOApp

app = App("book")
stdio_app = StdIOApp(app)

@app.method()
async def num_add(a: int, b: int):
    log("inside: add")
    await asyncio.sleep(random.randint(50,250)/1000.0)
    return {"sum": a+b}


@app.method()
async def book_search(q: str):
    log("inside: book_search")
    await asyncio.sleep(random.randint(50,250)/1000.0)
    res = await stdio_app.invoke("db.fetch_all", params={"sql": "select * from books"})
    log("query res", res)
    items = res["items"]
    return {
        "meta": {"pages": 5},
        "items": items,
    }

def main():
    
    asyncio.run(stdio_app.loop())

if __name__ == "__main__":
    main()

