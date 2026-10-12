"""Web server: python app.py  ->  http://localhost:8081"""
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import db_bot

INDEX = (db_bot.BASE / "static" / "index.html").read_bytes()
PORT = 8081


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, INDEX, "text/html; charset=utf-8")
        elif self.path == "/api/config":
            self._send(200, json.dumps({"model": db_bot.MODEL,
                                        "strategies": list(db_bot.STRATEGIES)}).encode())
        else:
            self._send(404, b"{}")

    def do_POST(self):
        if self.path != "/api/ask":
            return self._send(404, b"{}")
        data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
        q = (data.get("question") or "").strip()
        strat = data.get("strategy", "zero_shot")
        if not q or strat not in db_bot.STRATEGIES:
            return self._send(400, json.dumps({"error": "Bad question or strategy"}).encode())
        self._send(200, json.dumps(db_bot.ask(q, strat), default=str).encode())

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    db_bot.build_db()
    print(f"Model: {db_bot.MODEL}\nOpen http://localhost:{PORT}")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
