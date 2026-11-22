#!/usr/bin/env python3
"""Serve demo-godot/export/web with COOP/COEP headers (threads variant requires
cross-origin isolation). Usage: python3 serve_web.py [port, default 8931].
Serves export/web/ relative to this script. Stop with Ctrl-C / kill."""
import http.server
import functools
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
WEB = HERE / "export" / "web"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8931


class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        super().end_headers()

    def log_message(self, fmt, *args):
        sys.stderr.write("[serve] " + fmt % args + "\n")


httpd = http.server.ThreadingHTTPServer(
    ("127.0.0.1", PORT), functools.partial(Handler, directory=str(WEB))
)
print(f"[serve] http://127.0.0.1:{PORT}/  (COOP/COEP on)", flush=True)
httpd.serve_forever()
