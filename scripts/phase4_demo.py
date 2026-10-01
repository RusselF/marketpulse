import logging
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from marketpulse.http_client import ResilientClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


class Flaky(BaseHTTPRequestHandler):
    hits = 0

    def do_GET(self):
        Flaky.hits += 1
        if Flaky.hits % 3 != 0:  # dua request gagal, yang ketiga sukses
            self.send_response(503)
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok": true}')

    def log_message(self, *args):
        pass


server = HTTPServer(("127.0.0.1", 8099), Flaky)
threading.Thread(target=server.serve_forever, daemon=True).start()

with ResilientClient("http://127.0.0.1:8099") as client:
    for i in range(3):
        resp = client.get("/")
        print(f"request {i + 1}: {resp.status_code}, total hit ke server: {Flaky.hits}")