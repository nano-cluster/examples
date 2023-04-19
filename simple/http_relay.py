#! /usr/bin/python -u

import random
import json
import asyncio

from aiohttp import web, WSMsgType

from xrpc import App, log, StdIOApp

# used to interface with stdio rpc
rpc_app = App("http_relay")
stdio_app = StdIOApp(rpc_app)

routes = web.RouteTableDef()

@routes.post('/xrpc/{method_path:.*}')
async def post_handler(request: web.Request):
    method_path = request.match_info['method_path']
    parsed = await request.json()
    if method_path:
        if "method" in parsed:
            raise web.HTTPError("bad request: method in path and body")
        parsed["method"] = method_path
    if "method" not in parsed:
        raise web.HTTPError("bad request: missing method")
    log("calling: ...")
    res = await stdio_app.invoke(**parsed)
    log("got res: ", res)
    return web.json_response(res)

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    async for msg in ws:
        if msg.type == WSMsgType.TEXT:
            data = msg.data
            # TODO: is this really needed
            if msg.data == 'close':
                await ws.close()
            try: parsed = json.loads(data)
            except json.JSONDecodeError:
                parsed = None
            if not parsed: continue
            # TODO: we need invoke_raw
            res = await stdio_app.invoke(**parsed)
            res_b = json.dumps(res).encode("utf-8")+b"\n"
            await ws.send_str(res_b)
        elif msg.type == WSMsgType.ERROR:
            log('ws connection closed with exception %s' %
                  ws.exception())
    log('websocket connection closed')
    return ws

app = web.Application()
app.add_routes(routes)
app.add_routes([web.get('/ws', websocket_handler)])

async def amain():
    await stdio_app.loop()

def main():
    loop = asyncio.get_event_loop()
    loop.create_task(amain())
    port = 3000
    web.run_app(app, port=port, loop=loop, print=log)

if __name__ == "__main__":
    main()

