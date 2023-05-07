#! /usr/bin/python -u

import random
import asyncio

from xrpc import App, log, StdIOApp

app = App()


@app.method()
async def db_select(sql: str, params):
    #log("inside: db_select")
    await asyncio.sleep(random.randint(50,250)/1000.0)
    return {
        "meta": {
            "rows": 1,
            "cols":["id", "title", "author", "publisher", "pub_year"],
        },
        "items": [
            [123, "alice in wonderland", "me", "myself", 2019],
        ],
    }

def main():
    stdio_app = StdIOApp(app)
    asyncio.run(stdio_app.loop())

if __name__ == "__main__":
    main()

