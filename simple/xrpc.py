#! /usr/bin/python -u

import sys
import os
import json
import asyncio
import types

from uuid import uuid4


def log(*msgs, sep=" ", end="\n"):
    """similar to print, but uses stderr"""
    line = (sep.join(["{}".format(msg) for msg in msgs]))+end
    sys.stderr.write(line)
    sys.stderr.flush()

class App:
    def __init__(self, name=None, strip_prefix="action_"):
        if not name:
            name = os.path.basename(sys.argv[0])
        self.name = name
        self.strip_prefix = strip_prefix
        self.methods = {}

    def method(self, name: str=None):
        def decor(func):
            nonlocal name
            if name is None:
                # name = self.name + "." + func.__name__
                name = func.__name__
                if name.startswith(self.strip_prefix):
                    name = name[len(self.strip_prefix):]
            self.methods[name] = func
            return func
        return decor

    def call(self, name, **kwargs):
        if "." in name:
            name = name.rsplit(".", 1)[-1]
        return self.methods[name](**kwargs)

class XRpcError(RuntimeError):
    def __init__(self, codename, message, req_id=None, **kwargs):
        super().__init__(message)
        self.codename = codename
        self.xtra = kwargs
        self.req_id = req_id
    
    @classmethod
    def as_error_dict(cls, e: Exception, req_id: str = None) -> dict:
        # TODO: trace if in debug mode ...etc
        err = {"message":str(e), "codename": getattr(e, "codename", e.__class__.__name__)}
        ret = {"error":err}
        if req_id: ret["id"] = req_id
        return ret

    @classmethod
    def from_error_dict(cls, error_dict: dict) -> Exception:
        if not error_dict or "error" not in error_dict:
            return None
        err: dict = error_dict["error"]
        req_id: dict = error_dict.get("id")
        # only pass codename and message, the setattr known attributes
        e = XRpcError(req_id=req_id, **err)
        return e

class StdIOApp:
    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter

    def __init__(self, app: App):
        self.app = app
        self.invokes = {}
        self.balance = 0
        

    async def _connect_stdin_stdout(self):
        loop = asyncio.get_event_loop()
        self._loop = loop
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)
        w_transport, w_protocol = await loop.connect_write_pipe(asyncio.streams.FlowControlMixin, sys.stdout)
        writer = asyncio.StreamWriter(w_transport, w_protocol, reader, loop)
        self.reader = reader
        self.writer = writer

    async def call(self, id: str, method: str, **params):
        self.balance += 1
        try:
            res = await self.app.call(method, **params)
            ret = {"id": id, "result": res}
        except Exception as e:
            ret = XRpcError.as_error_dict(e, id)
        ret_b = json.dumps(ret, ensure_ascii=False).encode("utf-8")+b"\n"
        self.writer.write(ret_b)
        self.balance -= 1

    async def invoke(self, method, params, id=""):
        if not id:
            if id=="":
                id = str(uuid4())
            else:
                id = None
        if method=="_ping":
            return {"response":"pong"} # TODO: add from and at
        req = {"id": id, "method": method, "params": params}
        req_b = json.dumps(req, ensure_ascii=False).encode("utf-8")+b"\n"
        self.writer.write(req_b)
        future = self._loop.create_future()
        self.invokes[id] = future
        res = await future
        del self.invokes[id]
        if "error" in res:
            raise XRpcError.from_error_dict(res)
        return res

    def _handle_incoming_result(self, parsed):
        id = parsed["id"]
        future: asyncio.Future = self.invokes[id]
        result = parsed.get("result")
        error = parsed.get("error")
        if error is not None:
            e = XRpcError.from_error_dict(parsed)
            future.set_exception(e)
            return
        # TODO: should it be entire parsed not just result? should we have invoke_raw
        future.set_result(result)

    def _handle_one(self, parsed):
        if "method" not in parsed:
            return self._handle_incoming_result(parsed)
        id = parsed["id"]
        method = parsed["method"]
        params = parsed["params"]
        asyncio.create_task(self.call(id, method, **params))

    async def loop(self):
        old_tasks =asyncio.all_tasks()
        await self._connect_stdin_stdout()
        reader = self.reader
        while True:
            line = await reader.readline()
            if not line:
                if reader.at_eof(): break
                continue
            parsed = json.loads(line)
            self._handle_one(parsed)
        # drain
        tasks = asyncio.all_tasks()
        tasks.difference_update(old_tasks)
        if len(tasks):
            await asyncio.wait(tasks)


