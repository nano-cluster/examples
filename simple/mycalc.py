#! /usr/bin/python -u

import random
import asyncio

from concurrent.futures import ThreadPoolExecutor
from xrpc import App, log, StdIOApp

app = App("mycalc")
stdio_app = StdIOApp(app)

@app.method()
async def rnd_num():
    log("inside: rnd_num()")
    rnd_num = random.randint(50,250)
    if rnd_num%10==0: raise RuntimeError("random error")
    await asyncio.sleep(rnd_num/1000.0)
    return {"value": rnd_num}

@app.method()
async def num_add(a: int, b: int):
    log("inside: add")
    return {"value": a+b}


@app.method()
async def num_sub(a: int, b: int):
    log("inside: sub")
    await asyncio.sleep(random.randint(50,250)/1000.0)
    return {"value": a-b}

def calc_sqsum(values):
    """CPU-bound example"""
    return {"sum": sum(values), "sqsum": sum((v*v for v in values))}

@app.method()
async def sqsum(values):
    return calc_sqsum(values)

pool = ThreadPoolExecutor(16)

@app.method()
async def sqsum_threaded(values):
    loop = asyncio.get_running_loop()
    # NOTE: involves serialization and deser when passing from/to the pool
    result = await loop.run_in_executor(
            pool, calc_sqsum, values)
    return result

def main():
    asyncio.run(stdio_app.loop())

if __name__ == "__main__":
    main()

