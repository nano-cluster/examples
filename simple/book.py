#! /usr/bin/python -u

import random
import math
import asyncio

#import pandas as pd

from xrpc import App, log, StdIOApp

app = App("book")
stdio_app = StdIOApp(app)

@app.method()
async def book_search(q: str, per_page: int=10):
    log("inside: book_search")
    # sleep to simulate slow query
    await asyncio.sleep(random.randint(50,250)/1000.0)
    res = await stdio_app.invoke("db.fetch_one", params={"sql": "select count(*) c from books"})
    book_count = res["item"][0]
    pages = math.ceil(float(book_count)/per_page)
    # key-value
    res = await stdio_app.invoke("db.fetch_all", params={"sql": "select * from books limit 10", "kv": True})
    # res = await stdio_app.invoke("db.fetch_all", params={"sql": "select * from books limit 10", "kv": False})
    log("query res", res)
    items = res["items"]
    #columns = res["meta"]["columns"]
    #df = pd.DataFrame(items, columns=columns)
    #log(df)
    return {
        "meta": {"pages": pages, "count": book_count},
        "items": items,
    }

def main():
    asyncio.run(stdio_app.loop())

if __name__ == "__main__":
    main()

