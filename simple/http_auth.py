from aiohttp import web, hdrs
from aiohttp.web import middleware

from xrpc import log

@middleware
class MyBasicAuthMiddleware:
    def __init__(self, realm='Restricted'):
        self._realm = realm
        self._allowed = set()

    def add(self, line):
        self._allowed.add(line)

    async def authenticate(self, request: web.Request):
        # hdrs.AUTHORIZATION
        line = request.headers.getone("Authorization", None)
        if not line or " " not in line: return False
        method, token = line.split(" ", 1)
        if method!="Basic": return False
        return token in self._allowed

    def challenge(self):
        return web.Response(
            body=b'',
            status=401,
            reason='UNAUTHORIZED',
            headers={
                hdrs.WWW_AUTHENTICATE: f'Basic realm="{self._realm}"',
                hdrs.CONTENT_TYPE: 'text/html; charset=utf-8',
                hdrs.CONNECTION: 'keep-alive',
            },
        )

    async def __call__(self, request, handler):
        if len(self._allowed)==0:
            return await handler(request)
        if await self.authenticate(request):
            return await handler(request)
        else:
            return self.challenge()
