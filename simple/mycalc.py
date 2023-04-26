#! /usr/bin/python -u

import random
import asyncio

from xrpc import App, log, StdIOApp

app = App("mycalc")
stdio_app = StdIOApp(app)

@app.method()
async def num_add(a: int, b: int):
    log("inside: add")
    await asyncio.sleep(random.randint(50,250)/1000.0)
    return {"value": a+b}

@app.method()
async def num_sub(a: int, b: int):
    log("inside: sub")
    await asyncio.sleep(random.randint(50,250)/1000.0)
    return {"value": a-b}


def main():
    asyncio.run(stdio_app.loop())

if __name__ == "__main__":
    main()

