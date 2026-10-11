"""Live-mode safety for Shopify drafts (no network: the GraphQL transport is mocked)."""
import json, os, sys, unittest
from unittest import mock
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
from shopify_connector.client import ShopifyClient
from shopify_connector.server import _is_local_origin

TOKEN = "shpat_TEST_SECRET_0000"


def live():
    c = ShopifyClient(access_token=TOKEN)
    c.shop_domain, c.access_token, c.is_live = "test-store.myshopify.com", TOKEN, True
    return c


class TestShopifyLiveSafety(unittest.TestCase):
    def setUp(self):
        os.environ.pop("SHOPIFY_ALLOW_LIVE_WRITES", None)

    def test_dry_run_by_default(self):
        c = live()
        with mock.patch.object(c, "_graphql_request") as gql:
            res = c.create_draft_product({"title": "Mug"})
        gql.assert_not_called()
        self.assertTrue(res["dry_run"]); self.assertFalse(res["success"])
        self.assertNotIn(TOKEN, json.dumps(res))

    def test_confirm_sends_and_uses_real_id(self):
        c = live()
        ok = {"data": {"productCreate": {"product": {"id": "gid://shopify/Product/9"}, "userErrors": []}}}
        with mock.patch.object(c, "_graphql_request", return_value=ok) as gql:
            res = c.create_draft_product({"title": "Mug", "confirm": True})
        gql.assert_called_once()
        self.assertTrue(res["success"]); self.assertEqual(res["product"]["id"], "gid://shopify/Product/9")

    def test_transport_error_is_failure_not_fake_success(self):
        c = live()
        with mock.patch.object(c, "_graphql_request", return_value={"errors": [{"message": "401"}], "data": {}}):
            res = c.create_draft_product({"title": "Mug"}, confirm=True)
        self.assertFalse(res["success"])
        self.assertNotIn(res["product"], c._local_catalog)

    def test_origin_helper(self):
        self.assertTrue(_is_local_origin(None)); self.assertTrue(_is_local_origin("http://127.0.0.1:8113"))
        self.assertFalse(_is_local_origin("https://evil.example")); self.assertFalse(_is_local_origin("null"))


if __name__ == "__main__":
    unittest.main()
