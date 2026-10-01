import httpx


def make_client(base_url: str = "") -> httpx.Client:
    return httpx.Client(
        base_url=base_url,
        timeout=httpx.Timeout(10.0),
        headers={"User-Agent": "marketpulse/0.1 (learning project)"},
        follow_redirects=True,
    )