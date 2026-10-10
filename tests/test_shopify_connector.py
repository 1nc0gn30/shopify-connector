import json
import os
import sys
import threading
import time
import unittest
import urllib.request
from http.server import HTTPServer
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent.parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from shopify_connector.client import ShopifyClient
from shopify_connector.mcp_server import ShopifyMcpServer, MCP_TOOLS_DEFINITIONS
from shopify_connector.seo_engine import audit_listing, calculate_margins
from shopify_connector.server import ShopifyConnectorServer
from shopify_connector.transpiler import transpile_etsy_to_shopify

TEST_PORT = 18113


class TestShopifyClient(unittest.TestCase):
    """Test suite for ShopifyClient core logic and offline simulator."""

    def setUp(self):
        self.client = ShopifyClient()

    def test_simulation_mode_and_shop_info(self):
        self.assertFalse(self.client.is_configured())
        info = self.client.get_shop_info()
        self.assertEqual(info["currency"], "USD")
        self.assertIn("Simulated", info["name"])
        self.assertGreaterEqual(info["product_count"], 4)

    def test_search_products(self):
        all_prods = self.client.search_products()
        self.assertGreaterEqual(len(all_prods), 4)

        # Keyword match
        mugs = self.client.search_products("ceramic mug")
        self.assertGreaterEqual(len(mugs), 1)
        self.assertIn("Mug", mugs[0]["title"])

        # Tag match
        cottage = self.client.search_products("cottagecore")
        self.assertGreaterEqual(len(cottage), 2)

    def test_get_product_by_id(self):
        prod = self.client.get_product("gid://shopify/Product/901827401")
        self.assertIsNotNone(prod)
        self.assertEqual(prod["handle"], "grandmas-wildflower-garden-heavyweight-sweatshirt")
        self.assertGreaterEqual(len(prod["variants"]), 4)

    def test_create_draft_product(self):
        new_prod = self.client.create_draft_product({
            "title": "Autumn Oak Leaf Linen Apron",
            "price": "38.00",
            "tags": ["linen apron", "gardener", "cottagecore kitchen"],
            "productType": "Kitchen & Linen",
        })
        self.assertTrue(new_prod["success"])
        self.assertEqual(new_prod["product"]["title"], "Autumn Oak Leaf Linen Apron")
        self.assertEqual(new_prod["product"]["status"], "DRAFT")
        self.assertIn("mutation productCreate", new_prod["graphql_mutation"])

    def test_get_locations(self):
        locs = self.client.get_locations()
        self.assertGreaterEqual(len(locs), 2)
        self.assertTrue(any("Printify" in l["name"] for l in locs))


class TestSeoAndMarginEngine(unittest.TestCase):
    """Test suite for SEO auditing and profit margin calculations."""

    def test_seo_audit_high_score(self):
        title = "Grandma's Wildflower Garden Sweatshirt — Cozy Cottagecore Fleece"
        desc = "Heavyweight organic cotton blend crewneck sweatshirt printed with delicate botanical wildflowers. Crafted with double-needle stitching, pill-resistant fleece, and relaxed unisex fit. Machine wash cold inside out. Perfect thoughtful birthday gift for grandmothers, gardeners, and nature lovers."
        tags = ["cottagecore", "grandma gift", "wildflower sweatshirt", "botanical crewneck", "gardener apparel", "mother's day", "floral sweater", "comfy fleece"]
        handle = "grandmas-wildflower-garden-sweatshirt"

        res = audit_listing(title, desc, tags, handle)
        self.assertGreaterEqual(res["score"], 85)
        self.assertIn(res["grade"], ["A", "A+"])
        self.assertTrue(res["is_ready_for_publish"])

    def test_seo_audit_penalties(self):
        # Empty title and zero tags
        res = audit_listing("", "", [])
        self.assertLess(res["score"], 50)
        self.assertEqual(res["grade"], "F")
        self.assertFalse(res["is_ready_for_publish"])

    def test_margin_calculations(self):
        # $44.95 retail, $17.50 POD base cost, Basic Shopify (2.9% + 30¢)
        res = calculate_margins(retail_price=44.95, pod_cost=17.50, plan="basic")
        self.assertEqual(res["gross_revenue"], 44.95)
        self.assertEqual(res["pod_production_cost"], 17.50)
        self.assertEqual(res["shopify_processing_fee"], 1.60)
        self.assertEqual(res["net_profit"], 25.85)
        self.assertAlmostEqual(res["profit_margin_percent"], 57.5, delta=0.5)
        self.assertTrue(res["is_profitable"])

    def test_margin_with_ads_and_shipping(self):
        res = calculate_margins(
            retail_price=30.00,
            pod_cost=12.00,
            shipping_charged=5.00,
            shipping_cost=4.50,
            plan="shopify",
            include_ads=True
        )
        self.assertEqual(res["gross_revenue"], 35.00)
        self.assertGreater(res["ad_attribution_cost"], 0)
        self.assertTrue(res["is_profitable"])


class TestEtsyTranspiler(unittest.TestCase):
    """Test suite for Etsy-to-Shopify payload transpilation."""

    def test_transpile_etsy_payload(self):
        etsy_input = {
            "title": "Personalized Grandma Garden Sweatshirt | Botanical Wildflower Crewneck Sweater",
            "price": 42.00,
            "tags": "grandma gift, wildflower sweater, cottagecore crewneck, gardener gift, botanical art",
            "description": "• 50% cotton, 50% polyester\n• Pre-shrunk fleece knit\n• Air jet yarn for softer feel and reduced pilling",
            "vendor": "YourDigitalSpace",
            "category": "Apparel",
        }
        res = transpile_etsy_to_shopify(etsy_input)
        self.assertEqual(res["source"], "etsy_listing_kit")
        self.assertIn("Personalized Grandma Garden Sweatshirt", res["shopify_product"]["title"])
        self.assertIn("<ul>", res["shopify_product"]["bodyHtml"])
        self.assertEqual(res["variant_count"], 5)  # S, M, L, XL, 2XL
        self.assertIn("mutation productCreate", res["graphql_mutation"])


class TestMcpServer(unittest.TestCase):
    """Test suite for Shopify MCP Server JSON-RPC protocol."""

    def setUp(self):
        self.server = ShopifyMcpServer()

    def test_mcp_initialize(self):
        req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        res = self.server.handle_request(req)
        self.assertEqual(res["id"], 1)
        self.assertEqual(res["result"]["serverInfo"]["name"], "shopify-connector")

    def test_mcp_tools_list(self):
        req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        res = self.server.handle_request(req)
        self.assertEqual(len(res["result"]["tools"]), len(MCP_TOOLS_DEFINITIONS))

    def test_mcp_call_calculate_margins(self):
        req = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "shopify_calculate_margins",
                "arguments": {"retail_price": 50.00, "pod_cost": 20.00}
            }
        }
        res = self.server.handle_request(req)
        data = json.loads(res["result"]["content"][0]["text"])
        self.assertEqual(data["gross_revenue"], 50.00)
        self.assertTrue(data["is_profitable"])


class TestServerIntegration(unittest.TestCase):
    """Test suite for Shopify Connector HTTP REST server."""

    @classmethod
    def setUpClass(cls):
        client = ShopifyClient()
        cls.server = ShopifyConnectorServer("127.0.0.1", TEST_PORT, client, "/tmp")
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        time.sleep(0.15)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def test_health_endpoint(self):
        url = f"http://127.0.0.1:{TEST_PORT}/health"
        with urllib.request.urlopen(url, timeout=2.0) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode())
            self.assertEqual(data["status"], "ok")
            self.assertEqual(data["service"], "shopify-connector")
            self.assertEqual(data["port"], 8113)

    def test_stats_and_products_endpoints(self):
        stats_url = f"http://127.0.0.1:{TEST_PORT}/api/stats"
        with urllib.request.urlopen(stats_url, timeout=2.0) as resp:
            data = json.loads(resp.read().decode())
            self.assertIn("active_mcp_tools", data)
            self.assertGreaterEqual(data["total_products"], 4)

        prods_url = f"http://127.0.0.1:{TEST_PORT}/api/products?q=sweatshirt"
        with urllib.request.urlopen(prods_url, timeout=2.0) as resp:
            data = json.loads(resp.read().decode())
            self.assertGreaterEqual(data["count"], 1)

    def test_post_audit_and_profit(self):
        # Audit
        audit_url = f"http://127.0.0.1:{TEST_PORT}/api/audit"
        req = urllib.request.Request(
            audit_url,
            data=json.dumps({"title": "Test Title For Shopify Product Audit", "tags": ["gift", "apparel"]}).encode(),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            data = json.loads(resp.read().decode())
            self.assertIn("score", data)

        # Profit
        profit_url = f"http://127.0.0.1:{TEST_PORT}/api/profit"
        req = urllib.request.Request(
            profit_url,
            data=json.dumps({"retail_price": 40.0, "pod_cost": 15.0}).encode(),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            data = json.loads(resp.read().decode())
            self.assertIn("net_profit", data)

    def test_export_endpoint(self):
        export_url = f"http://127.0.0.1:{TEST_PORT}/api/export?format=json"
        with urllib.request.urlopen(export_url, timeout=2.0) as resp:
            data = json.loads(resp.read().decode())
            self.assertIn("products", data)


if __name__ == "__main__":
    unittest.main()
