"""Run with `python app.py`. Standard-library HTTP server and JSON REST API."""

import json
import sqlite3
from functools import lru_cache
import threading
from datetime import date
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import analytics
import store

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "web"
RESEARCH_LOCK = threading.Lock()


@lru_cache(maxsize=2)
def cached_research(snapshot):
    """Cache by canonical record content; any CRUD change invalidates the key."""
    import pandas as pd
    from src.analysis import research_bundle
    records = json.loads(snapshot)
    frame = pd.DataFrame(records, columns=['date', *store.COLUMNS])
    return research_bundle(frame)


class Handler(BaseHTTPRequestHandler):
    """Keep transport/routing here; calculations and persistence live elsewhere."""

    def respond(self, status, payload):
        body = json.dumps(payload, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def read_json(self):
        size = int(self.headers.get("Content-Length", "0"))
        if size <= 0 or size > 65536:
            raise ValueError("JSON body must be between 1 byte and 64 KB.")
        try:
            return json.loads(self.rfile.read(size))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ValueError("Invalid JSON body.") from None

    def route(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if not path.startswith("/api/"):
            if self.command != "GET":
                return self.respond(405, {"error": "Method not allowed."})
            return self.static(path)

        try:
            if path == "/api/health" and self.command == "GET":
                return self.respond(200, {"status": "ok"})
            if path == "/api/research" and self.command == "GET":
                snapshot = json.dumps(store.list_rows(), sort_keys=True)
                with RESEARCH_LOCK:
                    result = cached_research(snapshot)
                return self.respond(200, result)
            if path == "/api/observations" and self.command == "POST":
                return self.respond(201, store.create(self.read_json()))
            if path == "/api/observations" and self.command == "GET":
                args = parse_qs(parsed.query)
                start, end = args.get("start", [None])[0], args.get("end", [None])[0]
                for value in (start, end):
                    if value and date.fromisoformat(value).isoformat() != value:
                        raise ValueError("Use YYYY-MM-DD for date filters.")
                if start and end and start > end:
                    raise ValueError("Start date must not exceed end date.")
                rows = analytics.enriched(store.list_rows(start, end))
                return self.respond(200, {"observations": rows, "summary": analytics.summary(rows),
                                          "quality": analytics.quality(rows), "monthly": analytics.monthly(rows)})
            if path == "/api/forecast" and self.command == "GET":
                args = parse_qs(parsed.query)
                days = int(args.get("days", [14])[0])
                lookback = int(args.get("lookback", [60])[0])
                if not 1 <= days <= 90 or not 5 <= lookback <= 180:
                    raise ValueError("Days must be 1–90 and lookback 5–180.")
                rows = analytics.enriched(store.list_rows())
                return self.respond(200, analytics.forecast(rows, days, lookback))
            parts = path.strip("/").split("/")
            if len(parts) == 3 and parts[:2] == ["api", "observations"]:
                try:
                    row_id = int(parts[2])
                except ValueError:
                    raise ValueError("Observation ID must be an integer.") from None
                if self.command == "GET":
                    result = store.get_row(row_id)
                elif self.command == "PUT":
                    result = store.update(row_id, self.read_json())
                elif self.command == "DELETE":
                    result = store.delete(row_id)
                else:
                    return self.respond(405, {"error": "Method not allowed."})
                if not result:
                    return self.respond(404, {"error": "Observation not found."})
                return self.respond(200, result if self.command != "DELETE" else {"deleted": row_id})
            return self.respond(404, {"error": "Endpoint not found."})
        except (ValueError, TypeError) as exc:
            return self.respond(400, {"error": str(exc)})
        except sqlite3.IntegrityError:
            return self.respond(409, {"error": "An observation already exists for that date."})
        except Exception:
            import traceback
            traceback.print_exc()
            return self.respond(500, {"error": "The analysis could not be completed. Check the terminal for details."})

    def static(self, path):
        # Explicit allowlist avoids directory traversal and accidental data exposure.
        files = {"/": ("index.html", "text/html"),
                 "/app.js": ("app.js", "text/javascript"),
                 "/styles.css": ("styles.css", "text/css")}
        if path not in files:
            return self.respond(404, {"error": "Page not found."})
        name, mime = files[path]
        data = (STATIC / name).read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self): self.route()
    def do_POST(self): self.route()
    def do_PUT(self): self.route()
    def do_DELETE(self): self.route()


if __name__ == "__main__":
    import argparse
    import os
    parser = argparse.ArgumentParser(description="UAC Analytics dashboard and REST API")
    parser.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 8501)))
    args = parser.parse_args()
    store.initialize()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Dashboard: http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()

