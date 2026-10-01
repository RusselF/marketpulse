import httpx
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

URL = "https://quotes.toscrape.com/js/"

# 1) httpx + BeautifulSoup: hanya melihat HTML mentah dari server
html = httpx.get(URL, timeout=10).text
soup = BeautifulSoup(html, "html.parser")
print("httpx + BS4  ->", len(soup.select("div.quote")), "quotes")

# 2) Playwright: browser sungguhan menjalankan JavaScript lebih dulu
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto(URL)
    page.wait_for_selector("div.quote")  # tunggu elemen muncul, bukan sleep asal
    print("playwright   ->", len(page.query_selector_all("div.quote")), "quotes")
    browser.close()