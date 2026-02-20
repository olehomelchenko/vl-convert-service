"""Standalone HTTP server for vl-convert-service (Docker / non-Vercel deployment)."""

import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit, parse_qsl

import vl_convert as vlc

ALLOWED_BASE_URLS = ["https://vega.github.io/vega-datasets/"]

vlc.register_font_directory(str(Path("fonts").absolute()))


class Router(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(fmt % args, flush=True)

    def query_params(self):
        return dict(parse_qsl(urlsplit(self.path).query))

    def read_body(self):
        n = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(n).decode() if n else None

    def ok(self, content, content_type):
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(content if isinstance(content, bytes) else content.encode())

    def err(self, msg, code=400):
        self.send_response(code)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(msg.encode())

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "X-Requested-With, Content-Type")
        self.end_headers()

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/api/version":
            self.ok(vlc.__version__, "text/plain")
        elif path == "/test":
            self.ok('{"ok": true}', "application/json")
        else:
            self.err("Not found", 404)

    def do_POST(self):
        path = urlsplit(self.path).path
        qp = self.query_params()
        body = self.read_body()
        if not body:
            self.err("POST body is required")
            return

        vl_version = qp.get("vl_version") or None
        theme = qp.get("theme") or None
        scale = float(qp.get("scale", 1))

        try:
            if path == "/api/vl2svg":
                result = vlc.vegalite_to_svg(body, vl_version=vl_version, theme=theme, allowed_base_urls=ALLOWED_BASE_URLS)
                self.ok(result, "image/svg+xml")
            elif path == "/api/vl2png":
                result = vlc.vegalite_to_png(body, vl_version=vl_version, theme=theme, scale=scale, allowed_base_urls=ALLOWED_BASE_URLS)
                self.ok(result, "image/png")
            elif path == "/api/vl2pdf":
                result = vlc.vegalite_to_pdf(body, vl_version=vl_version, theme=theme, scale=scale, allowed_base_urls=ALLOWED_BASE_URLS)
                self.ok(result, "application/pdf")
            elif path == "/api/vl2vg":
                result = vlc.vegalite_to_vega(body, vl_version=vl_version, allowed_base_urls=ALLOWED_BASE_URLS)
                self.ok(result, "application/json")
            elif path == "/api/vg2svg":
                result = vlc.vega_to_svg(body, allowed_base_urls=ALLOWED_BASE_URLS)
                self.ok(result, "image/svg+xml")
            elif path == "/api/vg2png":
                result = vlc.vega_to_png(body, scale=scale, allowed_base_urls=ALLOWED_BASE_URLS)
                self.ok(result, "image/png")
            elif path == "/api/vg2pdf":
                result = vlc.vega_to_pdf(body, scale=scale, allowed_base_urls=ALLOWED_BASE_URLS)
                self.ok(result, "application/pdf")
            else:
                self.err("Not found", 404)
        except Exception as e:
            self.err(f"conversion failed: {e}")


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    server = HTTPServer(("0.0.0.0", port), Router)
    print(f"vl-convert-service running on port {port}", flush=True)
    server.serve_forever()
