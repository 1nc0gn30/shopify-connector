"""Shopify GraphQL Admin API Client & Offline Simulator.

Engineered by Neal Frazier Tech (@1nc0gn30) • NullAI Platform.
100% Python Standard Library — Zero External Dependencies.
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional


# Deterministic high-converting simulation dataset for offline / demo mode
SIMULATED_PRODUCTS: List[Dict[str, Any]] = [
    {
        "id": "gid://shopify/Product/901827401",
        "title": "Grandma's Wildflower Garden Heavyweight Sweatshirt",
        "handle": "grandmas-wildflower-garden-heavyweight-sweatshirt",
        "status": "ACTIVE",
        "vendor": "YourDigitalSpace",
        "productType": "Apparel & Sweatshirts",
        "tags": ["cottagecore", "grandma gift", "wildflower", "botanical", "spring garden", "gardener"],
        "totalInventory": 184,
        "variants": [
            {"id": "gid://shopify/ProductVariant/819201", "title": "Sand / S", "price": "44.95", "sku": "YDS-WF-SND-S", "inventoryQuantity": 35},
            {"id": "gid://shopify/ProductVariant/819202", "title": "Sand / M", "price": "44.95", "sku": "YDS-WF-SND-M", "inventoryQuantity": 52},
            {"id": "gid://shopify/ProductVariant/819203", "title": "Sand / L", "price": "44.95", "sku": "YDS-WF-SND-L", "inventoryQuantity": 48},
            {"id": "gid://shopify/ProductVariant/819204", "title": "Sand / XL", "price": "44.95", "sku": "YDS-WF-SND-XL", "inventoryQuantity": 49},
        ],
        "images": [
            {"id": "gid://shopify/ProductImage/77101", "url": "https://images.unsplash.com/photo-1578632767115-351597cf2477", "altText": "Front view of Grandma Wildflower Garden botanical sweatshirt in soft sand"}
        ],
        "seo": {
            "title": "Grandma's Wildflower Garden Heavyweight Sweatshirt | Soft Cottagecore Gift",
            "description": "Premium cozy fleece sweatshirt featuring delicate wildflower illustration. Perfect thoughtful birthday or Mother's Day keepsake."
        },
        "createdAt": "2026-10-01T12:00:00Z"
    },
    {
        "id": "gid://shopify/Product/901827402",
        "title": "Sovereign Meadow Cottagecore Botanical Ceramic Mug 15oz",
        "handle": "sovereign-meadow-cottagecore-botanical-ceramic-mug-15oz",
        "status": "ACTIVE",
        "vendor": "YourDigitalSpace",
        "productType": "Home & Drinkware",
        "tags": ["coffee mug", "cottagecore", "tea lover", "wildflower mug", "ceramic gift", "botanical art"],
        "totalInventory": 340,
        "variants": [
            {"id": "gid://shopify/ProductVariant/819210", "title": "15oz / Glossy White", "price": "21.95", "sku": "YDS-MUG-15-WHT", "inventoryQuantity": 340}
        ],
        "images": [
            {"id": "gid://shopify/ProductImage/77102", "url": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd", "altText": "Sovereign meadow ceramic mug on wooden table"}
        ],
        "seo": {
            "title": "Sovereign Meadow Cottagecore Ceramic Mug 15oz | Dishwasher Safe",
            "description": "Generous 15oz ceramic mug printed with hand-sketched field flora and botanical typography. Microwave & dishwasher safe."
        },
        "createdAt": "2026-10-02T14:30:00Z"
    },
    {
        "id": "gid://shopify/Product/901827403",
        "title": "Heirloom Seed Packet Farmers Market Canvas Tote Bag",
        "handle": "heirloom-seed-packet-farmers-market-canvas-tote-bag",
        "status": "ACTIVE",
        "vendor": "YourDigitalSpace",
        "productType": "Accessories & Bags",
        "tags": ["canvas tote", "farmers market", "seed packet", "gardener tote", "eco shopping", "reusable"],
        "totalInventory": 112,
        "variants": [
            {"id": "gid://shopify/ProductVariant/819220", "title": "Natural / One Size", "price": "28.50", "sku": "YDS-TOTE-NAT-OS", "inventoryQuantity": 112}
        ],
        "images": [
            {"id": "gid://shopify/ProductImage/77103", "url": "https://images.unsplash.com/photo-1544816155-12df9643f363", "altText": "Heavyweight canvas tote bag with vintage heirloom seed artwork"}
        ],
        "seo": {
            "title": "Heirloom Seed Packet Canvas Tote Bag | Heavyweight 12oz Cotton",
            "description": "Reinforced gusseted organic cotton tote bag with vintage seed packet typography. Holds up to 30 lbs of farmers market produce."
        },
        "createdAt": "2026-10-03T09:15:00Z"
    },
    {
        "id": "gid://shopify/Product/901827404",
        "title": "Coastal Salt Marsh Watercolor Giclée Canvas Gallery Wrap 16x20",
        "handle": "coastal-salt-marsh-watercolor-giclee-canvas-gallery-wrap-16x20",
        "status": "DRAFT",
        "vendor": "YourDigitalSpace",
        "productType": "Art & Wall Decor",
        "tags": ["wall art", "canvas wrap", "watercolor", "coastal marsh", "virginia beach", "cottage decor"],
        "totalInventory": 45,
        "variants": [
            {"id": "gid://shopify/ProductVariant/819230", "title": "16x20 / 1.25in Stretched", "price": "68.00", "sku": "YDS-ART-1620-STR", "inventoryQuantity": 45}
        ],
        "images": [
            {"id": "gid://shopify/ProductImage/77104", "url": "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119", "altText": "Coastal salt marsh watercolor canvas framed on serene living room wall"}
        ],
        "seo": {
            "title": "Coastal Salt Marsh Watercolor Canvas 16x20 | Archival Giclée",
            "description": "Museum-grade stretched canvas gallery wrap with fade-resistant pigment inks. Hand-stretched in USA with mounting hardware included."
        },
        "createdAt": "2026-10-04T16:45:00Z"
    }
]


class ShopifyClient:
    """Zero-dependency Shopify GraphQL Admin API client and local engine."""

    def __init__(
        self,
        shop_domain: Optional[str] = None,
        access_token: Optional[str] = None,
        api_version: str = "2024-01"
    ):
        self.shop_domain = (
            shop_domain
            or os.environ.get("SHOPIFY_SHOP_DOMAIN")
            or os.environ.get("SHOPIFY_STORE")
            or ""
        ).replace("https://", "").replace("http://", "").strip("/")
        
        self.access_token = (
            access_token
            or os.environ.get("SHOPIFY_ACCESS_TOKEN")
            or os.environ.get("SHOPIFY_API_KEY")
            or ""
        )
        self.api_version = api_version
        self.is_live = bool(self.shop_domain and self.access_token)
        self._local_catalog = list(SIMULATED_PRODUCTS)

    def is_configured(self) -> bool:
        """Return True if real Shopify store credentials are set."""
        return self.is_live

    def get_shop_info(self) -> Dict[str, Any]:
        """Fetch shop name, currency, and plan."""
        if not self.is_live:
            return {
                "name": "YourDigitalSpace (Simulated Store)",
                "domain": "yourdigitalspace.myshopify.com",
                "currency": "USD",
                "country": "US",
                "plan": "Shopify Advanced (Simulation)",
                "live": False,
                "product_count": len(self._local_catalog),
            }

        query = """
        {
          shop {
            name
            myshopifyDomain
            currencyCode
            billingAddress {
              countryCodeV2
            }
            plan {
              displayName
            }
          }
        }
        """
        data = self._graphql_request(query)
        shop = data.get("data", {}).get("shop", {})
        return {
            "name": shop.get("name", self.shop_domain),
            "domain": shop.get("myshopifyDomain", self.shop_domain),
            "currency": shop.get("currencyCode", "USD"),
            "country": shop.get("billingAddress", {}).get("countryCodeV2", "US"),
            "plan": shop.get("plan", {}).get("displayName", "Shopify Store"),
            "live": True,
            "product_count": len(self._local_catalog),
        }

    def search_products(self, query: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        """Search products by title, tag, or vendor."""
        if not self.is_live:
            q_lower = query.lower().strip()
            results = []
            for p in self._local_catalog:
                if not q_lower:
                    results.append(p)
                    continue
                match = (
                    q_lower in p["title"].lower()
                    or q_lower in p["handle"].lower()
                    or any(q_lower in t.lower() for t in p.get("tags", []))
                    or q_lower in p.get("vendor", "").lower()
                    or q_lower in p.get("productType", "").lower()
                )
                if match:
                    results.append(p)
            return results[:limit]

        gql_query = """
        query($query: String, $first: Int!) {
          products(first: $first, query: $query) {
            edges {
              node {
                id
                title
                handle
                status
                vendor
                productType
                tags
                totalInventory
                variants(first: 10) {
                  edges {
                    node {
                      id
                      title
                      price
                      sku
                      inventoryQuantity
                    }
                  }
                }
                images(first: 3) {
                  edges {
                    node {
                      id
                      url
                      altText
                    }
                  }
                }
                seo {
                  title
                  description
                }
                createdAt
              }
            }
          }
        }
        """
        variables = {"query": query or None, "first": limit}
        res = self._graphql_request(gql_query, variables)
        edges = res.get("data", {}).get("products", {}).get("edges", [])
        output = []
        for edge in edges:
            node = edge.get("node", {})
            variants = [v["node"] for v in node.get("variants", {}).get("edges", [])]
            images = [img["node"] for img in node.get("images", {}).get("edges", [])]
            output.append({
                "id": node.get("id"),
                "title": node.get("title"),
                "handle": node.get("handle"),
                "status": node.get("status"),
                "vendor": node.get("vendor"),
                "productType": node.get("productType"),
                "tags": node.get("tags", []),
                "totalInventory": node.get("totalInventory", 0),
                "variants": variants,
                "images": images,
                "seo": node.get("seo", {}),
                "createdAt": node.get("createdAt"),
            })
        return output

    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve full details for a product by ID or handle."""
        for p in self._local_catalog:
            if p["id"] == product_id or p["handle"] == product_id or str(product_id) in p["id"]:
                return p
        return None

    def create_draft_product(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new product draft in store or local registry."""
        new_id = f"gid://shopify/Product/{int(time.time())}"
        title = input_data.get("title", "Untitled Product")
        handle = input_data.get("handle") or title.lower().replace(" ", "-").replace("'", "").replace('"', "")
        
        tags = input_data.get("tags", [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",") if t.strip()]

        variants = input_data.get("variants") or [
            {
                "id": f"gid://shopify/ProductVariant/{int(time.time()) + 1}",
                "title": "Default Title",
                "price": str(input_data.get("price", "29.95")),
                "sku": input_data.get("sku", f"SKU-{int(time.time())}"),
                "inventoryQuantity": 50,
            }
        ]

        product_record = {
            "id": new_id,
            "title": title,
            "handle": handle,
            "status": "DRAFT",
            "vendor": input_data.get("vendor", "YourDigitalSpace"),
            "productType": input_data.get("productType", "General Merchandise"),
            "tags": tags,
            "totalInventory": sum(v.get("inventoryQuantity", 0) for v in variants),
            "variants": variants,
            "images": input_data.get("images", []),
            "seo": input_data.get("seo", {"title": title, "description": input_data.get("description", "")}),
            "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }

        self._local_catalog.insert(0, product_record)

        if not self.is_live:
            return {
                "success": True,
                "product": product_record,
                "mode": "simulation",
                "graphql_mutation": self.generate_product_create_mutation(product_record)
            }

        # Real GraphQL Product Create Mutation
        mutation = """
        mutation productCreate($input: ProductInput!) {
          productCreate(input: $input) {
            product {
              id
              title
              handle
              status
            }
            userErrors {
              field
              message
            }
          }
        }
        """
        payload_input = {
            "title": title,
            "handle": handle,
            "status": "DRAFT",
            "vendor": product_record["vendor"],
            "productType": product_record["productType"],
            "tags": tags,
        }
        res = self._graphql_request(mutation, {"input": payload_input})
        errors = res.get("data", {}).get("productCreate", {}).get("userErrors", [])
        if errors:
            return {"success": False, "errors": errors, "product": product_record}
        
        prod = res.get("data", {}).get("productCreate", {}).get("product", {})
        product_record["id"] = prod.get("id", new_id)
        return {"success": True, "product": product_record, "mode": "live"}

    def get_locations(self) -> List[Dict[str, Any]]:
        """Return fulfillment locations."""
        return [
            {"id": "gid://shopify/Location/101", "name": "Primary Warehouse (US East)", "active": True},
            {"id": "gid://shopify/Location/102", "name": "Printify Fulfillment Hub", "active": True},
            {"id": "gid://shopify/Location/103", "name": "West Coast Depot", "active": True},
        ]

    def generate_product_create_mutation(self, product: Dict[str, Any]) -> str:
        """Generate formatted GraphQL mutation string for developer inspect."""
        vars_json = json.dumps({
            "input": {
                "title": product["title"],
                "handle": product["handle"],
                "status": product["status"],
                "vendor": product["vendor"],
                "productType": product["productType"],
                "tags": product["tags"],
                "seo": product.get("seo", {})
            }
        }, indent=2)
        return (
            "mutation productCreate($input: ProductInput!) {\n"
            "  productCreate(input: $input) {\n"
            "    product {\n"
            "      id\n"
            "      title\n"
            "      handle\n"
            "      status\n"
            "    }\n"
            "    userErrors {\n"
            "      field\n"
            "      message\n"
            "    }\n"
            "  }\n"
            "}\n\n"
            f"# Variables:\n{vars_json}"
        )

    def _graphql_request(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a Shopify Admin GraphQL HTTP POST request."""
        url = f"https://{self.shop_domain}/admin/api/{self.api_version}/graphql.json"
        body = json.dumps({"query": query, "variables": variables or {}}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "X-Shopify-Access-Token": self.access_token,
                "User-Agent": "NullAI-Shopify-Connector/1.0.0",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=8.0) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            return {"errors": [{"message": str(e)}], "data": {}}
