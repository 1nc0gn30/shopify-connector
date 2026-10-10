"""Shopify MCP Server (Model Context Protocol).

Provides standard JSON-RPC 2.0 stdio interface for Antigravity, Claude, and AI Agents.
Engineered by Neal Frazier Tech (@1nc0gn30) • NullAI Platform.
100% Python Standard Library — Zero External Dependencies.
"""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, List, Optional

from .client import ShopifyClient
from .seo_engine import audit_listing, calculate_margins
from .transpiler import transpile_etsy_to_shopify

MCP_TOOLS_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "name": "shopify_search_products",
        "description": "Search active or draft products in the Shopify catalog by title, tag, collection, or vendor.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search term, product title, or tag"},
                "limit": {"type": "integer", "description": "Maximum number of products to return (default: 10)"}
            }
        }
    },
    {
        "name": "shopify_audit_listing",
        "description": "Audit a Shopify product listing for SEO ranking, title length, tag coverage, and mobile readiness (0–100 score).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Product title"},
                "description": {"type": "string", "description": "Product description copy or HTML"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "List of product tags"},
                "handle": {"type": "string", "description": "Product URL slug handle"}
            },
            "required": ["title"]
        }
    },
    {
        "name": "shopify_calculate_margins",
        "description": "Calculate Shopify transaction processing fees, POD production cost, shipping buffers, and net profit margins.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "retail_price": {"type": "number", "description": "Retail price in USD"},
                "pod_cost": {"type": "number", "description": "POD base production cost in USD"},
                "shipping_charged": {"type": "number", "description": "Shipping fee charged to customer"},
                "shipping_cost": {"type": "number", "description": "Actual fulfillment shipping cost"},
                "plan": {"type": "string", "enum": ["basic", "shopify", "advanced"], "description": "Shopify subscription tier"},
                "include_ads": {"type": "boolean", "description": "Include 15% estimated ad conversion cost"}
            },
            "required": ["retail_price", "pod_cost"]
        }
    },
    {
        "name": "shopify_transpile_etsy",
        "description": "Transpile an Etsy POD listing kit into a complete validated Shopify GraphQL productCreate payload.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Etsy listing title"},
                "description": {"type": "string", "description": "Etsy product description"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "13 Etsy search tags"},
                "price": {"type": "number", "description": "Retail price in USD"},
                "vendor": {"type": "string", "description": "Brand / Store vendor name"}
            },
            "required": ["title"]
        }
    },
    {
        "name": "shopify_create_draft_product",
        "description": "Create a new draft product in the Shopify store with variants, tags, and SEO metafields.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Product title"},
                "price": {"type": "number", "description": "Default retail price in USD"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags array"},
                "productType": {"type": "string", "description": "Product category/type"},
                "vendor": {"type": "string", "description": "Vendor name"}
            },
            "required": ["title"]
        }
    },
    {
        "name": "shopify_get_shop_info",
        "description": "Retrieve connected Shopify shop metadata, plan tier, currency, and catalog count.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "shopify_inventory_check",
        "description": "Check fulfillment locations and inventory status across warehouses.",
        "inputSchema": {
            "type": "object",
            "properties": {}
        }
    }
]


class ShopifyMcpServer:
    """JSON-RPC 2.0 stdio MCP server for Shopify."""

    def __init__(self, client: Optional[ShopifyClient] = None):
        self.client = client or ShopifyClient()

    def handle_request(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        method = request.get("method")
        msg_id = request.get("id")

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {
                        "name": "shopify-connector",
                        "version": "1.0.0"
                    },
                    "capabilities": {"tools": {}}
                }
            }

        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {"tools": MCP_TOOLS_DEFINITIONS}
            }

        if method == "tools/call":
            params = request.get("params", {})
            name = params.get("name")
            args = params.get("arguments", {})
            return self._call_tool(msg_id, name, args)

        if msg_id is not None:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"}
            }
        return None

    def _call_tool(self, msg_id: Any, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        try:
            if name == "shopify_search_products":
                query = args.get("query", "")
                limit = int(args.get("limit", 10))
                res = self.client.search_products(query, limit)
                return self._tool_success(msg_id, res)

            if name == "shopify_audit_listing":
                title = args.get("title", "")
                desc = args.get("description", "")
                tags = args.get("tags", [])
                handle = args.get("handle", "")
                res = audit_listing(title, desc, tags, handle)
                return self._tool_success(msg_id, res)

            if name == "shopify_calculate_margins":
                retail = float(args.get("retail_price", 0))
                pod = float(args.get("pod_cost", 0))
                ship_ch = float(args.get("shipping_charged", 0))
                ship_co = float(args.get("shipping_cost", 0))
                plan = args.get("plan", "basic")
                ads = bool(args.get("include_ads", False))
                res = calculate_margins(retail, pod, ship_ch, ship_co, plan, ads)
                return self._tool_success(msg_id, res)

            if name == "shopify_transpile_etsy":
                res = transpile_etsy_to_shopify(args)
                return self._tool_success(msg_id, res)

            if name == "shopify_create_draft_product":
                res = self.client.create_draft_product(args)
                return self._tool_success(msg_id, res)

            if name == "shopify_get_shop_info":
                res = self.client.get_shop_info()
                return self._tool_success(msg_id, res)

            if name == "shopify_inventory_check":
                locs = self.client.get_locations()
                return self._tool_success(msg_id, {"locations": locs, "active_count": len(locs)})

            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Unknown tool: {name}"}
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32000, "message": f"Tool execution failed: {str(e)}"}
            }

    def _tool_success(self, msg_id: Any, data: Any) -> Dict[str, Any]:
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(data, indent=2)
                    }
                ]
            }
        }

    def run_stdio(self) -> None:
        """Run standard stdio loop."""
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
                resp = self.handle_request(req)
                if resp:
                    sys.stdout.write(json.dumps(resp) + "\n")
                    sys.stdout.flush()
            except Exception as e:
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": f"Parse error: {str(e)}"}
                }
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()
