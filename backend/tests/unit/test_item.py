import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

sys.path.insert(1, str(Path(__file__).parent.parent.parent))

from app.main import app
from app.models import BoundingBox, CVResult, Dimensions, Item
from app.state.db import items_store
from constants import SERPAPI_API_KEY, SERPAPI_SEARCH_URL


def _item_with_cv(item_id: str, item_name: str) -> Item:
    cv = CVResult(
        item_name=item_name,
        class_name="bag",
        confidence_score=0.9,
        bounding_boxes=[BoundingBox(x_min=1, y_min=2, x_max=3, y_max=4)],
        dimensions=Dimensions(length=10.0, width=5.0, height=2.0),
    )
    return Item(item_id=item_id, cv_result=cv)


class TestGetItemPrice(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        items_store.clear()

    def tearDown(self):
        items_store.clear()

    @patch("app.routes.item.requests.get")
    def test_get_item_price_success(self, mock_get):
        items_store["i1"] = _item_with_cv("i1", "Backpack")

        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "shopping_results": [
                {"title": "Travel Backpack", "extracted_price": 49.99},
                {"title": "Hiking Pack", "extracted_price": 89.5},
            ]
        }
        mock_get.return_value = mock_response

        response = self.client.get(
            "/items/i1/price", params={"country": "united states", "limit": 1}
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["item_name"], "Travel Backpack")
        self.assertEqual(data[0]["price"], 49.99)
        self.assertEqual(data[0]["currency"], "USD")

        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], SERPAPI_SEARCH_URL)
        self.assertEqual(kwargs["params"]["q"], "Backpack")
        self.assertEqual(kwargs["params"]["gl"], "us")
        self.assertEqual(kwargs["params"]["hl"], "en")
        self.assertEqual(kwargs["params"]["api_key"], SERPAPI_API_KEY)

    def test_get_item_price_missing_cv(self):
        items_store["i1"] = Item(item_id="i1")

        response = self.client.get(
            "/items/i1/price", params={"country": "United States"}
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn("no cv result", response.text.lower())

    def test_get_item_price_unknown_country(self):
        items_store["i1"] = _item_with_cv("i1", "Backpack")

        response = self.client.get("/items/i1/price", params={"country": "Atlantis"})
        self.assertEqual(response.status_code, 404)
        self.assertIn("country not found", response.text.lower())

    def test_get_item_price_country_missing_currency(self):
        items_store["i1"] = _item_with_cv("i1", "Backpack")

        response = self.client.get("/items/i1/price", params={"country": "Antarctica"})
        self.assertEqual(response.status_code, 404)
        self.assertIn("currency", response.text.lower())

    @patch("app.routes.item.requests.get")
    def test_get_item_price_no_results(self, mock_get):
        items_store["i1"] = _item_with_cv("i1", "Backpack")

        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"shopping_results": []}
        mock_get.return_value = mock_response

        response = self.client.get(
            "/items/i1/price", params={"country": "United States"}
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn("no price results", response.text.lower())


if __name__ == "__main__":
    unittest.main()
