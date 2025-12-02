import unittest
import sys
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
import json

sys.path.insert(1, str(Path(__file__).parent.parent.parent))

from app.main import app
from app.state.db import items_store, trips_store
from app.models import Item, ItemUpdate, CVResult, BoundingBox, Dimensions


class TestItemEndpoints(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        items_store.clear()
        trips_store.clear()

    def tearDown(self):
        items_store.clear()
        trips_store.clear()

    def test_get_item_success(self):
        item = Item(item_id="123", weight_kg=1.2)
        items_store["123"] = item

        response = self.client.get("/items/123")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["weight_kg"], 1.2)

    def test_get_item_not_found(self):
        response = self.client.get("/items/doesnt-exist")
        self.assertEqual(response.status_code, 404)

    def test_patch_item_partial_update(self):
        original = Item(
            item_id="abc",
            weight_kg=0.3,
            cv_result=CVResult(
                item_name="Shirt",
                class_name="clothing",
                confidence_score=0.8,
                bounding_boxes=[BoundingBox(x_min=1, y_min=1, x_max=2, y_max=2)],
                dimensions=Dimensions(length=1, width=1)
            )
        )
        items_store["abc"] = original

        response = self.client.patch("/items/abc", json={"weight_kg": 2.0})
        self.assertEqual(response.status_code, 200)

        updated = response.json()
        self.assertEqual(updated["weight_kg"], 2.0)
        self.assertEqual(updated["cv_result"]["item_name"], "Shirt")

    def test_patch_item_set_field_to_null(self):
        original = Item(item_id="def", weight_kg=1.5)
        items_store["def"] = original

        response = self.client.patch("/items/def", json={"weight_kg": None})
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["weight_kg"])

    def test_patch_item_not_found(self):
        response = self.client.patch("/items/missing", json={"weight_kg": 2.0})
        self.assertEqual(response.status_code, 404)

    def test_delete_item_success(self):
        items_store["x1"] = Item(item_id="x1")

        response = self.client.delete("/items/x1")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("x1", items_store)

    def test_delete_item_removes_from_trip(self):
        from app.models import Trip

        trips_store["t1"] = Trip(
            trip_id="t1",
            destination="Paris",
            duration_days=5,
            doing_laundry=False,
            items=["x1"]
        )

        item = Item(item_id="x1")
        item.trips.append("t1")
        items_store["x1"] = item

        response = self.client.delete("/items/x1")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("x1", trips_store["t1"].items)


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
        mock_yolo.return_value = [CVResult(
            item_name="Shoes",
            class_name="shoe",
            confidence_score=0.85,
            bounding_boxes=[BoundingBox(x_min=10.1, y_min=20.2, x_max=50.5, y_max=80.8)],
            dimensions=Dimensions(length=1, width=1)
        )]

        test_image = ("img.jpg", b"fake", "image/jpeg")

        response = self.client.post("/items/detect", files={"image": test_image})

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["cv_result"]["item_name"], "Shoes")
        self.assertEqual(data["cv_result"]["class_name"], "shoe")
        self.assertEqual(data["cv_result"]["confidence_score"], 0.85)
        self.assertEqual(data["cv_result"]["bounding_boxes"][0]["x_min"], 10.1)

    @patch("app.routes.item.detect_objects_yolo")
    def test_detect_updates_existing_item(self, mock_yolo):
        items_store["abc"] = Item(item_id="abc")

        mock_yolo.return_value = [CVResult(
            item_name="Backpack",
            class_name="backpack",
            confidence_score=0.95,
            bounding_boxes=[BoundingBox(x_min=0, y_min=0, x_max=100, y_max=100)],
            dimensions=Dimensions(length=1, width=1)
        )]

        test_image = ("img.jpg", b"fake", "image/jpeg")
        response = self.client.post("/items/detect?item_id=abc", files={"image": test_image})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(items_store["abc"].cv_result.item_name, "Backpack")

    @patch("app.routes.item.detect_objects_yolo")
    def test_detect_invalid_yolo_output(self, mock_yolo):
        mock_yolo.return_value = None

        test_image = ("img.png", b"fake", "image/png")
        response = self.client.post("/items/detect", files={"image": test_image})

        self.assertEqual(response.status_code, 500)
        self.assertIn("Invalid YOLO output", response.text)

    @patch("app.routes.item.detect_objects_yolo")
    def test_detect_empty_yolo_output(self, mock_yolo):
        mock_yolo.return_value = []

        test_image = ("img.png", b"fake", "image/png")
        response = self.client.post("/items/detect", files={"image": test_image})

        self.assertEqual(response.status_code, 500)
        self.assertIn("Invalid YOLO output", response.text)


if __name__ == "__main__":
    unittest.main()
