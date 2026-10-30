"""Command Line Interface for Shopify Connector.

Engineered by Neal Frazier Tech (@1nc0gn30) • NullAI Platform.
100% Python Standard Library — Zero External Dependencies.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from typing import List, Optional

from .client import ShopifyClient
from .mcp_server import ShopifyMcpServer
from .seo_engine import audit_listing, calculate_margins
from .server import run_server
from .transpiler import transpile_etsy_to_shopify


def _default_bind_host() -> str:
    """Bind address: localhost unless explicitly opted in via $ZOTH_BIND_HOST or
    $HOST (IP literal only; zsh sets HOST to the hostname) or --host."""
    import ipaddress
    for var in ("ZOTH_BIND_HOST", "HOST"):
        val = os.environ.get(var, "").strip()
        if val == "localhost":
            return "127.0.0.1"
        if val:
            try:
                ipaddress.ip_address(val)
                return val
            except ValueError:
                pass
    return "127.0.0.1"


# ANSI Formatting
C_GOLD = "\033[38;5;214m"
C_CYAN = "\033[38;5;51m"
C_GREEN = "\033[38;5;48m"
C_RED = "\033[38;5;196m"
C_AMBER = "\033[38;5;208m"
C_DIM = "\033[2m"
C_BOLD = "\033[1m"
C_RESET = "\033[0m"


def print_banner() -> None:
    print(f"{C_GOLD}{C_BOLD}🛍️ SHOPIFY CONNECTOR v2.5.0{C_RESET}")
    print(f"{C_DIM}Shopify GraphQL Admin API & POD Multi-Channel Sync Engine{C_RESET}")
    print(f"{C_DIM}Engineered by Neal Frazier Tech (@1nc0gn30) • NullAI Platform{C_RESET}\n")


def cmd_status(host: str = "127.0.0.1", port: int = 8113, as_json: bool = False) -> int:
    client = ShopifyClient()
    url = f"http://{host}:{port}/health"
    live_info = None
    try:
        with urllib.request.urlopen(url, timeout=2.0) as resp:
            live_info = json.loads(resp.read().decode("utf-8"))
    except Exception:
        pass

    data = {
        "status": "online" if live_info else "standby",
        "service": "shopify-connector",
        "version": "2.5.0",
        "port": port,
        "is_configured": client.is_configured(),
        "shop_domain": client.shop_domain or "simulation.myshopify.com",
        "mode": "live_graphql" if client.is_configured() else "sovereign_offline_simulator",
        "simulated_products_count": len(client.search_products("", limit=100)),
        "daemon": live_info,
    }

    if as_json:
        print(json.dumps(data, indent=2))
        return 0

    print_banner()
    state_color = C_GREEN if live_info else C_AMBER
    print(f"Daemon Status:      {state_color}{data['status'].upper()}{C_RESET} ({url})")
    print(f"Shop Domain:        {C_CYAN}{data['shop_domain']}{C_RESET}")
    print(f"Engine Mode:        {C_GOLD}{data['mode']}{C_RESET}")
    print(f"Configured API:     {C_GREEN if data['is_configured'] else C_AMBER}{data['is_configured']}{C_RESET}")
    print(f"Catalog Products:   {data['simulated_products_count']} active items in catalog")
    print()
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="shopify-connector",
        description="Autonomous Shopify GraphQL Admin API & POD E-Commerce Engine for Antigravity & AI Agents.",
    )
    parser.add_argument("-v", "--version", action="version", version="shopify-connector 2.5.0")
    parser.add_argument("--status", action="store_true", help="Print local service status and configuration")
    parser.add_argument("--json", action="store_true", help="Output status/telemetry as JSON")
    parser.add_argument("--host", default=_default_bind_host(), help="Host interface (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8113, help="Port to bind/check (default: 8113)")

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Command: status
    status_p = subparsers.add_parser("status", help="Check local service and API configuration status")
    status_p.add_argument("--host", default="127.0.0.1", help="Host interface")
    status_p.add_argument("--port", type=int, default=8113, help="Port (default: 8113)")
    status_p.add_argument("--json", action="store_true", help="Output status report as JSON")

    # Command: serve
    serve_p = subparsers.add_parser("serve", help="Run REST API and Glassmorphic Web Cockpit")
    serve_p.add_argument("--port", type=int, default=8113, help="Port to bind server (default: 8113)")
    serve_p.add_argument("--host", default=None, help="Host interface (default: 127.0.0.1 or $ZOTH_BIND_HOST; use 0.0.0.0 only on trusted networks)")

    # Command: mcp
    subparsers.add_parser("mcp", help="Run JSON-RPC 2.0 stdio MCP server for Antigravity & Claude")

    # Command: audit
    audit_p = subparsers.add_parser("audit", help="Audit Shopify product title, tags, and description for SEO")
    audit_p.add_argument("--title", required=True, help="Product title")
    audit_p.add_argument("--tags", default="", help="Comma-separated product tags")
    audit_p.add_argument("--desc", default="", help="Product description copy")
    audit_p.add_argument("--handle", default="", help="URL handle slug")
    audit_p.add_argument("--json", action="store_true", help="Output audit report as JSON")

    # Command: profit
    profit_p = subparsers.add_parser("profit", help="Calculate Shopify processing fees and net profit margin")
    profit_p.add_argument("--retail", type=float, required=True, help="Retail price in USD")
    profit_p.add_argument("--pod", type=float, required=True, help="POD base cost in USD")
    profit_p.add_argument("--shipping", type=float, default=0.0, help="Shipping charged to customer")
    profit_p.add_argument("--plan", choices=["basic", "shopify", "advanced"], default="basic", help="Shopify plan")
    profit_p.add_argument("--ads", action="store_true", help="Include 15% estimated ad conversion CAC")
    profit_p.add_argument("--json", action="store_true", help="Output margin report as JSON")

    # Command: transpile
    trans_p = subparsers.add_parser("transpile", help="Transpile Etsy listing payload to Shopify GraphQL mutation")
    trans_p.add_argument("--title", required=True, help="Etsy listing title")
    trans_p.add_argument("--tags", default="", help="Comma-separated tags")
    trans_p.add_argument("--price", type=float, default=34.95, help="Retail price in USD")
    trans_p.add_argument("--desc", default="", help="Product description")
    trans_p.add_argument("--json", action="store_true", help="Output transpilation bundle as JSON")

    # Command: search
    search_p = subparsers.add_parser("search", help="Search products in catalog")
    search_p.add_argument("--query", default="", help="Search query")
    search_p.add_argument("--limit", type=int, default=10, help="Max results (default: 10)")
    search_p.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args(argv)

    if getattr(args, "status", False) or (getattr(args, "json", False) and not args.command):
        return cmd_status(host=args.host, port=args.port, as_json=True if getattr(args, "json", False) else False)

    cmd = args.command or "serve"

    if cmd == "status":
        return cmd_status(host=args.host, port=args.port, as_json=args.json)

    if cmd == "serve":
        run_server(port=args.port, host=args.host)
        return 0

    if cmd == "mcp":
        server = ShopifyMcpServer()
        server.run_stdio()
        return 0

    if cmd == "audit":
        tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []
        res = audit_listing(args.title, args.desc, tags, args.handle)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print(f"Shopify SEO Audit Score: {res['score']}/100 (Grade: {res['grade']})")
            print(f"Title Length: {res['title_length']} chars | Tags: {res['tag_count']} | Words: {res['word_count']}")
            if res["strengths"]:
                print("\nStrengths:")
                for s in res["strengths"]:
                    print(f"  ✓ {s}")
            if res["deductions"]:
                print("\nRecommended Fixes:")
                for d in res["deductions"]:
                    print(f"  ✗ [-{d['penalty']} pts] {d['message']}")
        return 0

    if cmd == "profit":
        res = calculate_margins(args.retail, args.pod, args.shipping, 0.0, args.plan, args.ads)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print(f"Retail Price:       ${res['retail_price']:.2f}")
            print(f"POD Base Cost:      ${res['pod_production_cost']:.2f}")
            print(f"Shopify Fee:        ${res['shopify_processing_fee']:.2f} ({res['processing_rate']})")
            if res['ad_attribution_cost'] > 0:
                print(f"Ad Spend (15%):     ${res['ad_attribution_cost']:.2f}")
            print("-" * 35)
            print(f"Net Profit:         ${res['net_profit']:.2f}")
            print(f"Profit Margin:      {res['profit_margin_percent']:.1f}%")
        return 0

    if cmd == "transpile":
        tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []
        res = transpile_etsy_to_shopify({
            "title": args.title,
            "tags": tags,
            "price": args.price,
            "description": args.desc,
        })
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print(f"Transpiled '{args.title}' -> Shopify '{res['shopify_product']['title']}'")
            print(f"Variants Generated: {res['variant_count']} | Tags: {res['tag_count']}")
            print("\nGraphQL Mutation Preview:\n" + res["graphql_mutation"][:300] + "...")
        return 0

    if cmd == "search":
        client = ShopifyClient()
        prods = client.search_products(args.query, limit=args.limit)
        if args.json:
            print(json.dumps(prods, indent=2))
        else:
            print(f"Found {len(prods)} products matching '{args.query}':")
            for p in prods:
                price = p.get("variants", [{}])[0].get("price", "N/A")
                print(f"  • [{p['status']}] {p['title']} — ${price} (Inventory: {p.get('totalInventory', 0)})")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
