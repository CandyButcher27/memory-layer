import http.client
import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

UPSTREAM = "api.anthropic.com"
PORT = int(sys.argv[1])
LOG = sys.argv[2]
DROP = {"host", "accept-encoding", "connection", "content-length", "transfer-encoding"}


def usage_of(body: bytes) -> dict:
    usage = {}
    for line in body.splitlines():
        line = line.strip()
        if line.startswith(b"data:"):
            line = line[5:].strip()
        if not line.startswith(b"{"):
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        for u in (ev.get("usage"), (ev.get("message") or {}).get("usage")):
            if isinstance(u, dict):
                usage.update({k: v for k, v in u.items() if isinstance(v, int)})
    return usage


class Proxy(BaseHTTPRequestHandler):
    def forward(self) -> None:
        body = self.rfile.read(int(self.headers.get("content-length") or 0))
        headers = {k: v for k, v in self.headers.items() if k.lower() not in DROP}
        headers["accept-encoding"] = "identity"
        conn = http.client.HTTPSConnection(UPSTREAM, timeout=600)
        conn.request(self.command, self.path, body, headers)
        resp = conn.getresponse()
        self.send_response(resp.status)
        for k, v in resp.getheaders():
            if k.lower() not in DROP:
                self.send_header(k, v)
        self.end_headers()
        seen = bytearray()
        while chunk := resp.read1(65536):
            seen += chunk
            self.wfile.write(chunk)
            self.wfile.flush()
        try:
            model = json.loads(body).get("model", "") if body else ""
        except json.JSONDecodeError:
            model = ""
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": time.time(), "path": self.path, "status": resp.status, "model": model,
                                "ua": self.headers.get("user-agent", ""), "usage": usage_of(bytes(seen))}) + "\n")

    do_POST = do_GET = forward

    def log_message(self, *args) -> None:
        pass


if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", PORT), Proxy).serve_forever()
