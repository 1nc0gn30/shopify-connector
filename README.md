# 🛍️ Shopify Connector for Antigravity & Sovereign AI Agents

[![Audit](https://img.shields.io/badge/guardrail-100%25%20passed-emerald)](https://shopify.nullai.tech)
[![MCP Protocol](https://img.shields.io/badge/MCP-2024--11--05-blue)](https://modelcontextprotocol.io)
[![Python](https://img.shields.io/badge/python-3.10%2B-gold)](https://python.org)
[![Zero Pip](https://img.shields.io/badge/dependencies-0%20external-purple)](https://nullai.tech)

Autonomous **Shopify GraphQL Admin API** and Print-on-Demand (POD) sync engine for **Google Antigravity** AI agents. Exposes 7 Model Context Protocol (MCP) tools for catalog search, listing SEO audits, real-time fee & profit modeling across Shopify tiers, 1-click Etsy listing kit transpilation, and draft product creation.

---

## ⚡ 7 Model Context Protocol (MCP) Tools

When registered in `~/.gemini/config/mcp_config.json`, Antigravity gains immediate access to:

1. `shopify_search_products`: Catalog search by query and tag filter with inventory metrics.
2. `shopify_audit_listing`: Title (≤70 chars), description, and tag search visibility auditor (0–100 score).
3. `shopify_calculate_margins`: Precise net margin calculator across Basic ($39/mo), Shopify ($105/mo), and Advanced ($399/mo) plans with ad CAC modeling.
4. `shopify_transpile_etsy`: 1-click Etsy listing kit transpiler generating Shopify GraphQL `productCreate` mutations and variants.
5. `shopify_create_draft_product`: Programmatic draft product creation via GraphQL.
6. `shopify_get_shop_info`: Storefront profile, currency, plan, and fulfillment details.
7. `shopify_inventory_check`: Stock levels, SKU tracking, and restock warning checks.

---

## 🚀 Quick Start

### 1. Antigravity MCP Setup
Add to `~/.gemini/config/mcp_config.json`:
```json
{
  "mcpServers": {
    "shopify-connector": {
      "command": "/home/zoth/NullAITech/shopify-connector/bin/shopify-connector",
      "args": ["mcp"],
      "env": {
        "PYTHONPATH": "/home/zoth/NullAITech/shopify-connector/src"
      }
    }
  }
}
```

### 2. Run CLI Operations
```bash
# Calculate net margins for a $42.00 botanical sweatshirt ($16.20 POD cost, $8.00 Ad CAC):
./bin/shopify-connector profit --retail 42.00 --cost 16.20 --shipping 4.50 --plan basic --cac 8.00

# Audit a Shopify product title and tags:
./bin/shopify-connector audit --title "Wildflower Botanical Oversized Sweatshirt" --tags "botanical,cottagecore,floral sweatshirt"

# Transpile an Etsy listing into a Shopify GraphQL mutation:
./bin/shopify-connector transpile --title "Cottagecore Crewneck" --tags "floral,gift" --price 45.00

# Launch Web Cockpit & REST API on port 8113:
./bin/shopify-connector serve --port 8113
```

---

## 🏛️ Ecosystem Architecture & Interop

- **Port**: `8113`
- **Etsy POD Forge Bridging**: Consumes listing kits from `etsy-pod-forge` (:8107) and `etsy-connector` (:8108) and formats them into Shopify GraphQL variables with full size variant matrices.
- **Zero Pip Invariant**: 100% Python standard library (`urllib.request`, `http.server`, `json`, `dataclasses`).

---

## 📜 Attribution & License
Engineered by **Neal Frazier Tech** ([@1nc0gn30](https://github.com/1nc0gn30)) • [NullAI Platform](https://nullai.tech)

## Network exposure

The server binds to `127.0.0.1` by default. To reach it from other devices,
opt in explicitly with `--host 0.0.0.0` (or set `ZOTH_BIND_HOST=0.0.0.0`; an IP
in `HOST` is also honoured, a plain hostname is ignored) and only on a trusted
network.
