#!/usr/bin/env python3
"""
Antigravity Storage Cleaner - Local Web Server
Provides a lightweight HTTP REST API and serves the modern Web UI dashboard.
Zero external dependencies (uses standard library http.server).
"""

import os
import sys
import json
import argparse
import webbrowser
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from cleaner_core import AntigravityScanner, AntigravityCleaner, format_size

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(CURRENT_DIR, "web")

scanner = AntigravityScanner()
cleaner = AntigravityCleaner(scanner)

class CleanerRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Concise logging
        sys.stderr.write(f"[Server] {args[0]} - {args[1]}\n")

    def send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors_headers()
        self.end_headers()

    def send_json(self, status_code: int, data: dict):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/ping":
            self.send_json(200, {"status": "ok", "app": "Antigravity Storage Cleaner"})
            return

        elif path == "/api/scan":
            query = parse_qs(parsed.query)
            active_id = query.get("active_id", [None])[0]
            try:
                res = scanner.scan_all(current_session_id=active_id)
                self.send_json(200, {"success": True, "data": res})
            except Exception as e:
                self.send_json(500, {"success": False, "error": str(e)})
            return

        # Serve static files from web/
        if path == "/" or path == "/index.html":
            file_path = os.path.join(WEB_DIR, "index.html")
        else:
            file_path = os.path.join(WEB_DIR, path.lstrip("/"))

        if os.path.exists(file_path) and os.path.isfile(file_path):
            content_type = "text/html; charset=utf-8"
            if file_path.endswith(".css"): content_type = "text/css"
            elif file_path.endswith(".js"): content_type = "application/javascript"
            elif file_path.endswith(".json"): content_type = "application/json"
            elif file_path.endswith(".svg"): content_type = "image/svg+xml"

            try:
                with open(file_path, "rb") as f:
                    body = f.read()
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_json(500, {"error": f"Error reading file: {e}"})
        else:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        try:
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            payload = json.loads(post_data.decode("utf-8")) if post_data else {}
        except Exception:
            payload = {}

        dry_run = bool(payload.get("dry_run", False))
        use_recycle_bin = bool(payload.get("use_recycle_bin", True))

        if path == "/api/clean-safe":
            try:
                res = cleaner.clean_safe_items(dry_run=dry_run, use_recycle_bin=use_recycle_bin)
                self.send_json(200, res)
            except Exception as e:
                self.send_json(500, {"success": False, "error": str(e)})

        elif path == "/api/delete-convo":
            cid = payload.get("conversation_id")
            if not cid:
                self.send_json(400, {"success": False, "error": "Missing conversation_id"})
                return
            try:
                res = cleaner.delete_conversation(cid, dry_run=dry_run, use_recycle_bin=use_recycle_bin)
                self.send_json(200, res)
            except Exception as e:
                self.send_json(500, {"success": False, "error": str(e)})

        elif path == "/api/slim-convo":
            cid = payload.get("conversation_id")
            if not cid:
                self.send_json(400, {"success": False, "error": "Missing conversation_id"})
                return
            try:
                res = cleaner.slim_conversation(cid, dry_run=dry_run, use_recycle_bin=use_recycle_bin)
                self.send_json(200, res)
            except Exception as e:
                self.send_json(500, {"success": False, "error": str(e)})

        elif path == "/api/vacuum":
            try:
                res = cleaner.vacuum_databases()
                self.send_json(200, res)
            except Exception as e:
                self.send_json(500, {"success": False, "error": str(e)})

        else:
            self.send_response(404)
            self.end_headers()

def run_server(port: int = 9922, open_browser: bool = True):
    server_address = ("127.0.0.1", port)
    try:
        httpd = ThreadingHTTPServer(server_address, CleanerRequestHandler)
    except OSError as e:
        print(f"[Server Error] Cannot bind to port {port}: {e}. Trying port {port+1}...")
        port += 1
        server_address = ("127.0.0.1", port)
        httpd = ThreadingHTTPServer(server_address, CleanerRequestHandler)

    url = f"http://localhost:{port}"
    print(f"🚀 Antigravity Cleaner Dashboard is active at: {url}")
    print("Press Ctrl+C to stop the server.")

    if open_browser:
        webbrowser.open(url)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped.")
        httpd.server_close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Antigravity Cleaner Server")
    parser.add_argument("--port", type=int, default=9922, help="Port to listen on (default: 9922)")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically")
    args = parser.parse_args()
    run_server(port=args.port, open_browser=not args.no_browser)
