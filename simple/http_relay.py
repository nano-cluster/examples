#! /usr/bin/python -u

import random
import json
import argparse
import os
import asyncio

from aiohttp import web, WSMsgType


from xrpc import App, log, StdIOApp, XRpcError
from http_auth import MyBasicAuthMiddleware
# consider web.HTTPException
#class HttpJsonError(web.HTTPException):
#    pass

# used to interface with stdio rpc
rpc_app = App("http_relay")
stdio_app = StdIOApp(rpc_app)

routes = web.RouteTableDef()

def get_http_error(e, req_id):
    res = XRpcError.as_error_dict(e, req_id)
    status_code = 500
    return web.json_response(res, status=status_code)

@routes.post('/xrpc/{method_path:.*}')
async def post_handler(request: web.Request):
    method_path = request.match_info['method_path']
    parsed = await request.json()
    req_id = parsed.get("id")
    if method_path:
        if "method" in parsed:
            raise web.HTTPError("bad request: method in path and body")
        parsed["method"] = method_path
    if "method" not in parsed:
        raise web.HTTPError("bad request: missing method")
    log("calling: ...")
    try:
        res = await stdio_app.invoke(**parsed)
        log("got res: ", res)
        return web.json_response({"id": req_id, "result": res})
    except Exception as e:
        log("got error: ", e)
        return get_http_error(e, req_id)
    

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
            req_id = parsed.get("id")
            try:
                ret = await stdio_app.invoke(**parsed)
                res = {"id": req_id, "result": ret}
            except Exception as e:
                res = XRpcError.as_error_dict(e, req_id)
            # res_b = json.dumps(res).encode("utf-8")+b"\n"
            # await ws.send_bytes(res_b)
            res_str = json.dumps(res)+"\n"
            await ws.send_str(res_str)
        elif msg.type == WSMsgType.ERROR:
            log('ws connection closed with exception %s' %
                  ws.exception())
    log('websocket connection closed')
    return ws

auth = MyBasicAuthMiddleware()
app = web.Application(middlewares=[auth])
app.add_routes(routes)
app.add_routes([web.get('/ws', websocket_handler)])

async def amain():
    await stdio_app.loop()

def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument(
        "--port",
        type=int,
        default=3000,
        help="specify http port to use",
    )
    parser.add_argument(
        "--basic-auth",
        metavar="AUTH_BASE64",
        action="append",
        help="add a basic auth user, --basic-auth YWRtaW46YWRtaW4=",
    )
    parser.add_argument(
        "--static",
        metavar="PREFIX=PATH",
        action="append",
        help="add static directory to be served, --static /=./public --static assets=build/assets",
    )
    args = parser.parse_args()
    auth_ls = args.basic_auth or []
    for basic_auth_item in auth_ls:
        log("auth:", basic_auth_item)
        auth.add(basic_auth_item)
    static_ls = args.static or []
    for prefix_w_path in static_ls:
        prefix, path = prefix_w_path.split("=", 1) if "=" in prefix_w_path else (prefix_w_path, prefix_w_path)
        prefix = "/" + prefix.strip('/')
        if prefix == "/": prefix=""
        for item in os.listdir(path):
            item_path = f'{path}/{item}'
            if item=="index.html":
                app.router.add_get(f"{prefix}/", lambda request: web.FileResponse(item_path))
            elif os.path.isdir(item_path):
                log(f"adding prefix='{prefix}/{item}' path='{path}/{item}'")
                app.router.add_static(f'{prefix}/{item}', path=item_path)
            else:
                log(f"** WW** skip adding prefix='{prefix}/{item}' path='{path}/{item}'")


    loop = asyncio.get_event_loop()
    loop.create_task(amain())
    port = args.port
    web.run_app(app, port=port, loop=loop, print=log)

if __name__ == "__main__":
    main()

