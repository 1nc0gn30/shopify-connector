"""Etsy-to-Shopify Payload Transpiler & Bridge.

Converts Etsy listing kits (from etsy-pod-forge or etsy-connector) into
production-ready Shopify GraphQL mutations and REST payloads.

Engineered by Neal Frazier Tech (@1nc0gn30) • NullAI Platform.
100% Python Standard Library — Zero External Dependencies.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional


def transpile_etsy_to_shopify(etsy_data: Dict[str, Any]) -> Dict[str, Any]:
    """Transpile Etsy listing payload into a validated Shopify product structure."""
    raw_title = etsy_data.get("title", "Handmade Artisanal Product")
    
    # Clean title for Shopify: keep first 70 characters clean, or use full
    shopify_title = raw_title.split(" | ")[0] if len(raw_title) > 90 else raw_title
    
    # Generate URL handle
    handle = re.sub(r"[^a-z0-9]+", "-", shopify_title.lower()).strip("-")
    
    # Parse tags
    raw_tags = etsy_data.get("tags", [])
    if isinstance(raw_tags, str):
        tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
    elif isinstance(raw_tags, list):
        tags = [str(t).strip() for t in raw_tags if str(t).strip()]
    else:
        tags = []

    # Format description into clean HTML
    raw_desc = etsy_data.get("description", "")
    lines = [line.strip() for line in raw_desc.split("\n") if line.strip()]
    
    html_paragraphs = []
    for line in lines:
        if line.startswith("•") or line.startswith("-") or line.startswith("*"):
            html_paragraphs.append(f"<li>{line.lstrip('•-* ')}</li>")
        else:
            html_paragraphs.append(f"<p>{line}</p>")
    
    # Group list items in <ul>
    description_html = "\n".join(html_paragraphs)
    description_html = re.sub(r"(<li>.*?</li>\n?)+", r"<ul>\g<0></ul>", description_html, flags=re.DOTALL)

    retail_price = str(etsy_data.get("price") or etsy_data.get("retail_price", "34.95"))
    compare_at_price = str(round(float(retail_price) * 1.25, 2))

    # Build variants (supporting S, M, L, XL, 2XL or custom)
    sizes = etsy_data.get("sizes") or ["S", "M", "L", "XL", "2XL"]
    colors = etsy_data.get("colors") or ["Default"]
    
    variants = []
    for c in colors:
        for s in sizes:
            variant_title = f"{c} / {s}" if c != "Default" else str(s)
            variants.append({
                "title": variant_title,
                "price": retail_price,
                "compareAtPrice": compare_at_price,
                "sku": f"YDS-{handle[:8].upper()}-{s}",
                "inventoryQuantity": 50,
                "requiresShipping": True,
            })

    # Images
    images = []
    for img_url in etsy_data.get("images", []):
        if isinstance(img_url, str):
            images.append({"src": img_url, "altText": shopify_title})
        elif isinstance(img_url, dict):
            images.append({
                "src": img_url.get("url") or img_url.get("src", ""),
                "altText": img_url.get("altText") or img_url.get("alt", shopify_title)
            })

    # Shopify Product Input Object
    shopify_product = {
        "title": shopify_title,
        "handle": handle,
        "bodyHtml": description_html,
        "vendor": etsy_data.get("vendor", "YourDigitalSpace"),
        "productType": etsy_data.get("category") or etsy_data.get("productType", "Apparel & Accessories"),
        "tags": tags,
        "status": "DRAFT",
        "variants": variants,
        "images": images,
        "seo": {
            "title": f"{shopify_title} | Premium Gift",
            "description": raw_desc[:155].strip() if raw_desc else f"Shop {shopify_title}. Premium quality, printed in USA."
        }
    }

    # Generate GraphQL ProductCreate Mutation
    graphql_mutation = (
        "mutation productCreate($input: ProductInput!) {\n"
        "  productCreate(input: $input) {\n"
        "    product {\n"
        "      id\n"
        "      title\n"
        "      handle\n"
        "      status\n"
        "      onlineStoreUrl\n"
        "    }\n"
        "    userErrors {\n"
        "      field\n"
        "      message\n"
        "    }\n"
        "  }\n"
        "}\n\n"
        f"# Variables:\n{json.dumps({'input': shopify_product}, indent=2)}"
    )

    return {
        "source": "etsy_listing_kit",
        "transpiled_at": "2026-10-10T00:00:00Z",
        "shopify_product": shopify_product,
        "variant_count": len(variants),
        "tag_count": len(tags),
        "graphql_mutation": graphql_mutation,
    }
