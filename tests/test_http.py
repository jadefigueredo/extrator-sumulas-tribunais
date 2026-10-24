import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer

from sumulas.http import FetchError, HttpClient


@pytest.fixture
async def flaky_server():
    calls = {"flaky": 0, "missing": 0}

    async def flaky(request):
        calls["flaky"] += 1
        if calls["flaky"] < 3:
            return web.Response(status=503)
        return web.Response(body=b"%PDF-ok")

    async def missing(request):
        calls["missing"] += 1
        return web.Response(status=404)

    app = web.Application()
    app.router.add_get("/flaky", flaky)
    app.router.add_get("/missing", missing)
    async with TestServer(app) as server:
        yield server, calls


async def test_retries_transient_errors(flaky_server):
    server, calls = flaky_server
    async with HttpClient(backoff_base=0) as client:
        body = await client.get_bytes(str(server.make_url("/flaky")))

    assert body == b"%PDF-ok"
    assert calls["flaky"] == 3


async def test_does_not_retry_client_errors(flaky_server):
    server, calls = flaky_server
    async with HttpClient(backoff_base=0) as client:
        with pytest.raises(FetchError, match="HTTP 404"):
            await client.get_bytes(str(server.make_url("/missing")))

    assert calls["missing"] == 1


async def test_gives_up_after_max_attempts(flaky_server):
    server, calls = flaky_server
    async with HttpClient(backoff_base=0, max_attempts=2) as client:
        with pytest.raises(FetchError, match="HTTP 503"):
            await client.get_bytes(str(server.make_url("/flaky")))

    assert calls["flaky"] == 2


async def test_connection_error_becomes_fetch_error():
    async with HttpClient(backoff_base=0, max_attempts=2) as client:
        with pytest.raises(FetchError):
            await client.get_bytes("http://127.0.0.1:9/nada")
