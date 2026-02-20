#!/usr/bin/env python3
"""Simple local HTTP router for vl-convert-service (replaces Vercel CLI)."""
from http.server import HTTPServer
from urllib.parse import urlsplit
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from api.vl2svg import handler as vl2svg_handler
from api.vl2png import handler as vl2png_handler
from api.vl2vg import handler as vl2vg_handler
from api.version import handler as version_handler

ROUTES = {
    "/api/vl2svg": vl2svg_handler,
    "/api/vl2png": vl2png_handler,
    "/api/vl2vg": vl2vg_handler,
    "/api/version": version_handler,
}


class Router(vl2svg_handler):
    def do_POST(self):
        path = urlsplit(self.path).path
        route_handler = ROUTES.get(path)
        if route_handler is None:
            self.send_response(404)
            self.end_headers()
            return
        route_handler.do_POST(self)

    def do_GET(self):
        path = urlsplit(self.path).path
        route_handler = ROUTES.get(path)
        if route_handler is None:
            self.send_response(404)
            self.end_headers()
            return
        route_handler.do_GET(self)


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
    server = HTTPServer(("localhost", port), Router)
    print(f"vl-convert-service running on http://localhost:{port}")
    server.serve_forever()
