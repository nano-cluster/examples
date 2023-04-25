#! /usr/bin/python -u

import random
import asyncio

from xrpc import App, log, StdIOApp

app = App()
stdio_app = StdIOApp(app)

PERIOD_SEC = 5

async def my_loop():
    log(f"periodic calling num_add every {PERIOD_SEC} seconds: ...")
    while(True):
        await asyncio.sleep(PERIOD_SEC)
        a = random.randint(0, 100)
        b = random.randint(0, 100)
        log("periodic calling num_add: ...")
        res = await stdio_app.invoke("mycalc.num_add", params={"a": a, "b": b})
        log("periodic calling num_add: res: ", res)

async def amain():
    tasks = set()
    tasks.add(asyncio.create_task(stdio_app.loop()))
    await asyncio.sleep(1)
    tasks.add(asyncio.create_task(my_loop()))
    await asyncio.wait(tasks)

def main():
    asyncio.run(amain())

if __name__ == "__main__":
    main()

