"""Command Line Interface for Shopify Connector.

Engineered by Neal Frazier Tech (@1nc0gn30) • NullAI Platform.
100% Python Standard Library — Zero External Dependencies.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import List, Optional

from .client import ShopifyClient
from .mcp_server import ShopifyMcpServer
from .seo_engine import audit_listing, calculate_margins
from .server import run_server
from .transpiler import transpile_etsy_to_shopify


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="shopify-connector",
        description="Autonomous Shopify GraphQL Admin API & POD E-Commerce Engine for Antigravity & AI Agents.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Command: serve
    serve_p = subparsers.add_parser("serve", help="Run REST API and Glassmorphic Web Cockpit")
    serve_p.add_argument("--port", type=int, default=8113, help="Port to bind server (default: 8113)")

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
    cmd = args.command or "serve"

    if cmd == "serve":
        run_server(port=args.port)
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
