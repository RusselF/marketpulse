import httpx

from marketpulse.http_client import ResilientClient


def make(handler, sleep=lambda s: None, **kw):
    return ResilientClient(
        "https://example.test",
        transport=httpx.MockTransport(handler),
        sleep=sleep,
        min_interval=0,
        **kw,
    )


def test_retries_then_succeeds():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(503)
        return httpx.Response(200, json={"ok": True})

    with make(handler) as client:
        resp = client.get("/x")

    assert resp.status_code == 200
    assert calls["n"] == 3


def test_gives_up_after_max_retries():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        return httpx.Response(500)

    with make(handler, max_retries=2) as client:
        resp = client.get("/x")

    assert resp.status_code == 500
    assert calls["n"] == 3  # 1 percobaan awal + 2 retry


def test_no_retry_on_404():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        return httpx.Response(404)

    with make(handler) as client:
        resp = client.get("/x")

    assert resp.status_code == 404
    assert calls["n"] == 1


def test_retries_on_timeout():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        if calls["n"] < 2:
            raise httpx.ConnectTimeout("boom", request=request)
        return httpx.Response(200)

    with make(handler) as client:
        resp = client.get("/x")

    assert resp.status_code == 200
    assert calls["n"] == 2


def test_honors_retry_after():
    sleeps: list[float] = []
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429, headers={"Retry-After": "2"})
        return httpx.Response(200)

    with make(handler, sleep=sleeps.append) as client:
        client.get("/x")

    assert sleeps == [2.0]