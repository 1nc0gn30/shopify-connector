"""REST API & Glassmorphic Cockpit Server for Shopify Connector.

Serves on Port 8113 with zero external pip dependencies (100% Python standard library).
Engineered by Neal Frazier Tech (@1nc0gn30) • NullAI Platform.
"""

from __future__ import annotations

import json
import mimetypes
import os
import queue
import socketserver
import time
import urllib.parse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional

from .client import ShopifyClient
from .mcp_server import MCP_TOOLS_DEFINITIONS
from .seo_engine import audit_listing, calculate_margins
from .transpiler import transpile_etsy_to_shopify


class ShopifyCockpitHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler for Shopify Connector REST API & Cockpit."""

    server_version = "ShopifyConnector/1.0.0"

    def log_message(self, format: str, *args: Any) -> None:
        """Silence default stdout logging."""
        return

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "SAMEORIGIN")

    def _send_json(self, data: Any, status: int = 200) -> None:
        payload = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(payload)

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        if path == "":
            path = "/"

        # 1. Health Probe
        if path in ("/health", "/api/health"):
            self._send_json({
                "status": "ok",
                "service": "shopify-connector",
                "port": 8113,
                "version": "1.0.0",
                "uptime_seconds": round(time.time() - self.server.start_time, 1),
                "is_configured": self.server.client.is_configured(),
                "shop_domain": self.server.client.shop_domain or "simulation.myshopify.com",
            })
            return

        # 2. Shop Info
        if path == "/api/info":
            info = self.server.client.get_shop_info()
            self._send_json(info)
            return

        # 3. Stats
        if path == "/api/stats":
            stats = dict(self.server.stats)
            stats["active_mcp_tools"] = len(MCP_TOOLS_DEFINITIONS)
            stats["total_products"] = len(self.server.client.search_products("", limit=100))
            stats["is_configured"] = self.server.client.is_configured()
            stats["uptime_seconds"] = round(time.time() - self.server.start_time, 1)
            self._send_json(stats)
            return

        # 4. Products Search
        if path == "/api/products":
            params = urllib.parse.parse_qs(parsed.query)
            q = params.get("q", [""])[0]
            limit = int(params.get("limit", [20])[0])
            products = self.server.client.search_products(q, limit=limit)
            self.server.stats["searches_performed"] += 1
            self.server.broadcast_sse("catalog_search", {"query": q, "count": len(products)})
            self._send_json({"query": q, "count": len(products), "products": products})
            return

        # 5. Export Catalog
        if path == "/api/export":
            params = urllib.parse.parse_qs(parsed.query)
            fmt = params.get("format", ["json"])[0]
            products = self.server.client.search_products("", limit=200)
            if fmt == "csv":
                csv_lines = ["id,title,handle,vendor,productType,status,tags,totalInventory,price"]
                for p in products:
                    tags_str = ";".join(p.get("tags", []))
                    price = p.get("variants", [{}])[0].get("price", "0.00")
                    csv_lines.append(f'"{p.get("id")}","{p.get("title")}","{p.get("handle")}","{p.get("vendor")}","{p.get("productType")}","{p.get("status")}","{tags_str}",{p.get("totalInventory",0)},"{price}"')
                body = "\n".join(csv_lines).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/csv")
                self.send_header("Content-Disposition", 'attachment; filename="shopify_catalog_export.csv"')
                self.send_header("Content-Length", str(len(body)))
                self._send_cors_headers()
                self.end_headers()
                self.wfile.write(body)
                return
            self._send_json({"export_timestamp": time.time(), "count": len(products), "products": products})
            return

        # 6. Live SSE Telemetry Stream
        if path in ("/api/stream", "/api/events"):
            self._handle_sse()
            return

        # 7. Static Asset Serving
        self._serve_static(path)

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")

        content_len = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
        try:
            body = json.loads(post_body)
        except Exception:
            body = {}

        if path == "/api/audit":
            title = body.get("title", "")
            desc = body.get("description", "")
            tags = body.get("tags", [])
            handle = body.get("handle", "")
            res = audit_listing(title, desc, tags, handle)
            self.server.stats["audits_performed"] += 1
            self.server.broadcast_sse("listing_audited", {"title": title, "score": res.get("score")})
            self._send_json(res)
            return

        if path == "/api/profit":
            retail = float(body.get("retail_price", 0))
            pod = float(body.get("pod_cost", 0))
            ship_ch = float(body.get("shipping_charged", 0))
            ship_co = float(body.get("shipping_cost", 0))
            plan = body.get("plan", "basic")
            ads = bool(body.get("include_ads", False))
            res = calculate_margins(retail, pod, ship_ch, ship_co, plan, ads)
            self.server.stats["profit_calculations"] += 1
            self.server.broadcast_sse("margin_calculated", {"retail": retail, "net_profit": res.get("net_profit")})
            self._send_json(res)
            return

        if path == "/api/transpile":
            res = transpile_etsy_to_shopify(body)
            self.server.stats["transpiled_kits"] += 1
            self.server.broadcast_sse("transpilation_complete", {"title": res.get("shopify_product", {}).get("title")})
            self._send_json(res)
            return

        if path == "/api/create-draft":
            res = self.server.client.create_draft_product(body)
            self.server.broadcast_sse("draft_created", {"title": body.get("title")})
            self._send_json(res)
            return

        self._send_json({"error": "Endpoint not found"}, status=404)

    def _handle_sse(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        q = self.server.subscribe_sse()
        init_event = f"data: {json.dumps({'type': 'init', 'message': 'Connected to Shopify Connector Live Stream', 'port': 8113})}\n\n"
        try:
            self.wfile.write(init_event.encode("utf-8"))
            self.wfile.flush()
            while True:
                try:
                    msg = q.get(timeout=10.0)
                    self.wfile.write(msg.encode("utf-8"))
                    self.wfile.flush()
                except queue.Empty:
                    self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            self.server.unsubscribe_sse(q)

    def _serve_static(self, path: str) -> None:
        clean_path = path.lstrip("/")
        if not clean_path or clean_path == "":
            clean_path = "index.html"

        file_path = os.path.join(self.server.public_dir, clean_path)
        if not os.path.exists(file_path) or os.path.isdir(file_path):
            file_path = os.path.join(self.server.public_dir, "index.html")

        if not os.path.exists(file_path):
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"404 Not Found")
            return

        content_type, _ = mimetypes.guess_type(file_path)
        content_type = content_type or "application/octet-stream"

        try:
            with open(file_path, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self._send_cors_headers()
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode("utf-8"))


class ShopifyConnectorServer(socketserver.ThreadingMixIn, HTTPServer):
    """Threaded HTTP Server for Shopify Connector Cockpit."""

    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, host: str, port: int, client: ShopifyClient, public_dir: str):
        self.client = client
        self.public_dir = public_dir
        self.start_time = time.time()
        self.stats = {
            "audits_performed": 0,
            "profit_calculations": 0,
            "transpiled_kits": 0,
            "searches_performed": 0,
        }
        self._sse_subscribers: List[queue.Queue] = []
        super().__init__((host, port), ShopifyCockpitHandler)

    def subscribe_sse(self) -> queue.Queue:
        q = queue.Queue(maxsize=100)
        self._sse_subscribers.append(q)
        return q

    def unsubscribe_sse(self, q: queue.Queue) -> None:
        if q in self._sse_subscribers:
            self._sse_subscribers.remove(q)

    def broadcast_sse(self, event_type: str, data: Dict[str, Any]) -> None:
        payload = json.dumps({"type": event_type, "timestamp": time.time(), "data": data})
        msg = f"data: {payload}\n\n"
        for q in list(self._sse_subscribers):
            try:
                q.put_nowait(msg)
            except queue.Full:
                pass


def run_server(port: int = 8113, public_dir: Optional[str] = None) -> None:
    """Entrypoint to run the server."""
    pub = public_dir or str(Path(__file__).resolve().parent.parent.parent / "public")
    client = ShopifyClient()
    server = ShopifyConnectorServer("0.0.0.0", port, client, pub)
    print(f"[shopify-connector] Cockpit running on http://127.0.0.1:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
