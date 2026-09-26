import httpx
import pytest

from scraper.client import ClientConfig, Fetcher, RateLimiter, backoff_delay


class FakeClock:
    def __init__(self):
        self.t = 0.0
        self.sleeps = []

    def clock(self):
        return self.t

    def sleep(self, s):
        self.sleeps.append(s)
        self.t += s


def test_rate_limiter_enforces_interval():
    fc = FakeClock()
    rl = RateLimiter(2.0, clock=fc.clock, sleep=fc.sleep)
    assert rl.wait() == 0.0  # first call is free
    fc.t += 0.5
    assert rl.wait() == pytest.approx(1.5)
    fc.t += 5
    assert rl.wait() == 0.0


def test_backoff_grows_and_caps():
    assert backoff_delay(0, 1, 30, jitter=False) == 1
    assert backoff_delay(3, 1, 30, jitter=False) == 8
    assert backoff_delay(10, 1, 30, jitter=False) == 30
    for _ in range(50):
        assert 0.5 <= backoff_delay(0, 1, 30) <= 1.0


def make_fetcher(handler, retries=3):
    sleeps = []
    cfg = ClientConfig(delay=0, max_retries=retries)
    f = Fetcher(cfg, transport=httpx.MockTransport(handler), sleep=sleeps.append)
    return f, sleeps


def test_retries_then_succeeds():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(503)
        return httpx.Response(200, text="ok")

    f, sleeps = make_fetcher(handler)
    assert f.get("https://example.test/").text == "ok"
    assert calls["n"] == 3
    assert len(sleeps) == 2  # two backoff sleeps


def test_gives_up_after_max_retries():
    def handler(request):
        return httpx.Response(429)

    f, _ = make_fetcher(handler, retries=2)
    with pytest.raises(httpx.HTTPStatusError):
        f.get("https://example.test/")


def test_no_retry_on_404():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        return httpx.Response(404)

    f, _ = make_fetcher(handler)
    with pytest.raises(httpx.HTTPStatusError):
        f.get("https://example.test/missing")
    assert calls["n"] == 1


def test_retries_on_transport_error():
    calls = {"n": 0}

    def handler(request):
        calls["n"] += 1
        if calls["n"] == 1:
            raise httpx.ConnectError("boom", request=request)
        return httpx.Response(200, text="ok")

    f, _ = make_fetcher(handler)
    assert f.get("https://example.test/").text == "ok"


def test_sends_user_agent():
    seen = {}

    def handler(request):
        seen["ua"] = request.headers["user-agent"]
        return httpx.Response(200)

    f, _ = make_fetcher(handler)
    f.get("https://example.test/")
    assert seen["ua"].startswith("web-scraper-template")
