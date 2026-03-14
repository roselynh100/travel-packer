import json
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

sys.path.insert(1, str(Path(__file__).parent.parent.parent))

from app.main import app
from app.models import BoundingBox, CVResult, Dimensions, Item
from app.state.db import items_store, trips_store
from constants import SERPAPI_SEARCH_URL


def _item_with_cv(item_id: str) -> Item:
    cv = CVResult(
        item_name="bag",
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

    @patch("app.routes.item.SERPAPI_API_KEY", "test_key")
    @patch("helpers.trip_helpers.requests.get")
    def test_get_item_price_success(self, mock_get):
        items_store["i1"] = _item_with_cv("i1")

        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            "shopping_results": [
                {
                    "title": "Travel Backpack",
                    "source": "Walmart",
                    "extracted_price": 49.99,
                },
                {"title": "Hiking Pack", "source": "MEC", "extracted_price": 89.5},
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
        self.assertEqual(data[0]["source"], "Walmart")
        self.assertEqual(data[0]["price"], 49.99)
        self.assertEqual(data[0]["currency"], "USD")

        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], SERPAPI_SEARCH_URL)
        self.assertEqual(kwargs["params"]["q"], "bag")
        self.assertEqual(kwargs["params"]["gl"], "us")
        self.assertEqual(kwargs["params"]["hl"], "en")
        self.assertEqual(kwargs["params"]["api_key"], "test_key")

    @patch("app.routes.item.SERPAPI_API_KEY", "test_key")
    def test_get_item_price_missing_cv(self):
        items_store["i1"] = Item(item_id="i1")

        response = self.client.get(
            "/items/i1/price", params={"country": "United States"}
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn("no cv result", response.text.lower())

    @patch("app.routes.item.SERPAPI_API_KEY", "test_key")
    def test_get_item_price_unknown_country(self):
        items_store["i1"] = _item_with_cv("i1")

        response = self.client.get("/items/i1/price", params={"country": "Atlantis"})
        self.assertEqual(response.status_code, 404)
        self.assertIn("country not found", response.text.lower())

    @patch("app.routes.item.SERPAPI_API_KEY", "test_key")
    def test_get_item_price_country_missing_currency(self):
        items_store["i1"] = _item_with_cv("i1")

        response = self.client.get("/items/i1/price", params={"country": "Antarctica"})
        self.assertEqual(response.status_code, 404)
        self.assertIn("currency", response.text.lower())

    @patch("app.routes.item.SERPAPI_API_KEY", "test_key")
    @patch("helpers.trip_helpers.requests.get")
    def test_get_item_price_no_results(self, mock_get):
        items_store["i1"] = _item_with_cv("i1")

        mock_response = Mock()
        mock_response.ok = True
        mock_response.json.return_value = {"shopping_results": []}
        mock_get.return_value = mock_response

        response = self.client.get(
            "/items/i1/price", params={"country": "United States"}
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn("no price results", response.text.lower())

    @patch("app.routes.item.SERPAPI_API_KEY", "test_key")
    @patch("helpers.trip_helpers.requests.get")
    def test_get_item_price_v2_success(self, mock_get):
        items_store["i1"] = _item_with_cv("i1")

        origin_response = Mock()
        origin_response.ok = True
        origin_response.json.return_value = {
            "shopping_results": [
                {
                    "title": "Travel Backpack US",
                    "source": "Target",
                    "extracted_price": 50.0,
                }
            ]
        }

        destination_response = Mock()
        destination_response.ok = True
        destination_response.json.return_value = {
            "shopping_results": [
                {
                    "title": "Travel Backpack CA",
                    "source": "Canadian Tire",
                    "extracted_price": 80.0,
                }
            ]
        }

        exchange_response = Mock()
        exchange_response.ok = True
        exchange_response.json.return_value = {
            "cad": {
                "usd": 0.75,
            }
        }

        mock_get.side_effect = [
            origin_response,
            destination_response,
            exchange_response,
        ]

        response = self.client.get(
            "/items/i1/price/v2",
            params={
                "origin_country": "United States",
                "destination_country": "Canada",
                "limit": 1,
            },
        )
        self.assertEqual(response.status_code, 200, response.text)

        data = response.json()
        self.assertEqual(data["origin_currency"], "USD")
        self.assertEqual(data["destination_currency"], "CAD")
        self.assertEqual(data["exchange_rate"], 0.75)
        self.assertEqual(data["origin_prices"][0]["price"], 50.0)
        self.assertEqual(
            data["destination_prices_in_origin_currency"][0]["price"], 60.0
        )
        self.assertEqual(
            data["destination_prices_in_origin_currency"][0]["currency"], "USD"
        )

        self.assertEqual(mock_get.call_count, 3)
        self.assertEqual(mock_get.call_args_list[0].args[0], SERPAPI_SEARCH_URL)
        self.assertEqual(mock_get.call_args_list[0].kwargs["params"]["gl"], "us")
        self.assertEqual(mock_get.call_args_list[1].kwargs["params"]["gl"], "ca")
        self.assertIn("/cad.json", mock_get.call_args_list[2].args[0])


class TestReadWeight(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        items_store.clear()
        trips_store.clear()

    @patch("app.routes.item.get_weight")
    def test_read_weight_create_new_item(self, mock_get_weight):
        mock_get_weight.return_value = json.dumps({"total_weight_kg": 0.5})

        response = self.client.post(f"/items/weight")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["weight_kg"], 0.5)
        self.assertIsNotNone(response.json()["item_id"])

    @patch("app.routes.item.get_weight")
    def test_read_weight_update_existing_item(self, mock_get_weight):
        items_store["i1"] = Item(item_id="i1", weight_kg=0.3)

        mock_get_weight.return_value = json.dumps({"total_weight_kg": 0.7})

        response = self.client.post("/items/weight?item_id=i1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(items_store["i1"].weight_kg, 0.7)

    @patch("app.routes.item.get_weight")
    def test_read_weight_scale_error(self, mock_get_weight):
        mock_get_weight.return_value = json.dumps({"error": "Scale not detected"})

        response = self.client.post("/items/weight")
        self.assertEqual(response.status_code, 500)


class TestDetectEndpoint(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        items_store.clear()
        trips_store.clear()

    @patch("app.routes.item.detect_objects_yolo")
    def test_detect_creates_new_item(self, mock_yolo):
        """Test creating a new item via image detection."""
        mock_yolo.return_value = (
            [
                CVResult(
                    item_name="Shoes",
                    confidence_score=0.85,
                    bounding_boxes=[
                        BoundingBox(x_min=10.1, y_min=20.2, x_max=50.5, y_max=80.8)
                    ],
                    dimensions=Dimensions(length=1, width=1),
                )
            ],
            b"fake_annotated_jpeg_bytes",
        )

        test_image = ("img.jpg", b"fake", "image/jpeg")

        response = self.client.post("/items/detect", files={"image": test_image})

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["item"]["cv_result"]["item_name"], "Shoes")
        self.assertEqual(data["item"]["cv_result"]["confidence_score"], 0.85)
        self.assertEqual(data["item"]["cv_result"]["bounding_boxes"][0]["x_min"], 10.1)
        self.assertIn("annotated_image", data)
        self.assertIsNotNone(data["annotated_image"])

    @patch("app.routes.item.detect_objects_yolo")
    def test_detect_updates_existing_item(self, mock_yolo):
        items_store["abc"] = Item(item_id="abc")

        mock_yolo.return_value = (
            [
                CVResult(
                    item_name="Backpack",
                    confidence_score=0.95,
                    bounding_boxes=[
                        BoundingBox(x_min=0, y_min=0, x_max=100, y_max=100)
                    ],
                    dimensions=Dimensions(length=1, width=1),
                )
            ],
            b"fake_annotated",
        )

        test_image = ("img.jpg", b"fake", "image/jpeg")
        response = self.client.post(
            "/items/detect?item_id=abc", files={"image": test_image}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(items_store["abc"].cv_result.item_name, "Backpack")

    @patch("app.routes.item.detect_objects_yolo")
    def test_detect_invalid_yolo_output(self, mock_yolo):
        mock_yolo.return_value = (None, b"")

        test_image = ("img.png", b"fake", "image/png")
        response = self.client.post("/items/detect", files={"image": test_image})

        self.assertEqual(response.status_code, 500)
        self.assertIn("Invalid YOLO output", response.text)

    @patch("app.routes.item.detect_objects_yolo")
    def test_detect_empty_yolo_output(self, mock_yolo):
        mock_yolo.return_value = ([], b"")

        test_image = ("img.png", b"fake", "image/png")
        response = self.client.post("/items/detect", files={"image": test_image})

        self.assertEqual(response.status_code, 500)
        self.assertIn("Invalid YOLO output", response.text)


if __name__ == "__main__":
    unittest.main()
