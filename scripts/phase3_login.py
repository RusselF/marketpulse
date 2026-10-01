import httpx
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

BASE = "https://quotes.toscrape.com"
USER, PASSWORD = "admin", "admin"  # situs latihan menerima nilai apa saja


def login_httpx() -> None:
    with httpx.Client(base_url=BASE, timeout=10, follow_redirects=True) as client:
        # 1) ambil halaman login: server memberi cookie session + token CSRF di form
        resp = client.get("/login")
        soup = BeautifulSoup(resp.text, "html.parser")
        token = soup.select_one("input[name=csrf_token]")["value"]
        print("cookies setelah GET /login:", dict(client.cookies))

        # 2) kirim form; token harus cocok dengan session yang sama
        resp = client.post("/login", data={"csrf_token": token, "username": USER, "password": PASSWORD})
        print("httpx logged in:", "Logout" in resp.text)

        # 3) cookie jar ikut terkirim otomatis di request berikutnya
        page2 = client.get("/page/2/")
        print("masih login di halaman lain:", "Logout" in page2.text)

    # kontras: request tanpa Client tidak membawa cookie
    print("tanpa session:", "Logout" in httpx.get(f"{BASE}/").text)


def login_playwright() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        page.goto(f"{BASE}/login")
        page.fill("#username", USER)
        page.fill("#password", PASSWORD)
        page.click("input[type=submit]")
        page.wait_for_selector("a[href='/logout']")
        print("playwright logged in: True")

        # simpan cookie supaya run berikutnya tidak perlu login ulang
        context.storage_state(path="state.json")
        context.close()

        # context baru yang memakai state tadi sudah langsung login
        context2 = browser.new_context(storage_state="state.json")
        page2 = context2.new_page()
        page2.goto(BASE)
        print("context baru langsung login:", page2.query_selector("a[href='/logout']") is not None)
        browser.close()


if __name__ == "__main__":
    login_httpx()
    login_playwright()