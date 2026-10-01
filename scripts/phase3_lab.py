import json
import time

import httpx
from playwright.sync_api import sync_playwright

BASE = "https://quotes.toscrape.com"


def via_embedded_json() -> list[dict]:
    """Teknik 1: data JSON tertanam di <script>. Cukup httpx, tanpa browser."""
    quotes = []
    with httpx.Client(base_url=BASE, timeout=10) as client:
        for page in range(1, 11):
            html = client.get(f"/js/page/{page}/").text
            marker = "var data = "
            start = html.index(marker) + len(marker)
            data, _ = json.JSONDecoder().raw_decode(html[start:])  # parse JSON sampai selesai
            if not data:
                break
            quotes.extend(data)
    return quotes


def via_json_api() -> list[dict]:
    """Teknik 2: panggil endpoint JSON yang ditemukan di tab Network."""
    quotes, page = [], 1
    with httpx.Client(base_url=BASE, timeout=10) as client:
        while True:
            resp = client.get("/api/quotes", params={"page": page})
            resp.raise_for_status()
            body = resp.json()
            quotes.extend(body["quotes"])
            if not body["has_next"]:
                break
            page += 1
    return quotes


def via_playwright() -> list[dict]:
    """Teknik 3: browser sungguhan, baca DOM hasil render."""
    quotes = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        url = f"{BASE}/js/"
        while url:
            page.goto(url)
            page.wait_for_selector("div.quote")
            quotes.extend(
                page.eval_on_selector_all(
                    "div.quote",
                    """els => els.map(e => ({
                        text: e.querySelector('.text').innerText,
                        author: e.querySelector('.author').innerText,
                        tags: [...e.querySelectorAll('.tag')].map(t => t.innerText),
                    }))""",
                )
            )
            nxt = page.query_selector("li.next > a")
            url = f"{BASE}{nxt.get_attribute('href')}" if nxt else None
        browser.close()
    return quotes


if __name__ == "__main__":
    for fn in (via_embedded_json, via_json_api, via_playwright):
        t0 = time.perf_counter()
        result = fn()
        print(f"{fn.__name__:20} -> {len(result):4} quotes in {time.perf_counter() - t0:5.1f}s")