import unittest
import sys
from pathlib import Path
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
import json

sys.path.insert(1, str(Path(__file__).parent.parent.parent))

from app.main import app
from app.state.db import items_store, trips_store


class TestReadWeight(unittest.TestCase):
    """Test cases for the read_weight endpoint."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
        items_store.clear()
        # Also clear trips store to avoid test interference
        trips_store.clear()

    def tearDown(self):
        """Clean up after each test."""
        items_store.clear()
        trips_store.clear()

    @patch('app.routes.item.get_weight')
    def test_read_weight_create_new_item(self, mock_get_weight):
        """Test creating a new item with weight reading."""
        mock_get_weight.return_value = json.dumps({
            "total_weight_kg": 0.5
        })

        from app.models import Trip
        test_trip = Trip(trip_id="test-trip-123", destination="Paris", duration_days=5, doing_laundry=False)
        trips_store["test-trip-123"] = test_trip

        response = self.client.post(
            "/items/weight?trip_id=test-trip-123"
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["total_weight_kg"], 0.5)
        self.assertIn("item", data)
        self.assertIn("item_id", data["item"])
        
        item_id = data["item"]["item_id"]
        self.assertIn(item_id, items_store)

    @patch('app.routes.item.get_weight')
    def test_read_weight_update_existing_item(self, mock_get_weight):
        """Test updating an existing item's weight."""
        from app.models import Item
        existing_item = Item(item_id="existing-item-123", item_name="Test Item", weight_kg=0.3)
        items_store["existing-item-123"] = existing_item

        from app.models import Trip
        test_trip = Trip(trip_id="test-trip-123", destination="Paris", duration_days=5, doing_laundry=False)
        trips_store["test-trip-123"] = test_trip

        mock_get_weight.return_value = json.dumps({
            "total_weight_kg": 0.7
        })

        response = self.client.post(
            "/items/weight?trip_id=test-trip-123&item_id=existing-item-123"
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total_weight_kg"], 0.7)
        
        # Verify item was updated (not replaced)
        updated_item = items_store["existing-item-123"]
        self.assertEqual(updated_item.weight_kg, 0.7)
        self.assertEqual(updated_item.item_name, "Test Item")  # Other fields preserved

    @patch('app.routes.item.get_weight')
    def test_read_weight_scale_error(self, mock_get_weight):
        """Test handling scale errors."""
        mock_get_weight.return_value = json.dumps({
            "error": "Scale not detected"
        })

        response = self.client.post(
            "/items/weight?trip_id=test-trip-123"
        )

        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("detail", data)

    @patch('app.routes.item.get_weight')
    def test_read_weight_associates_with_trip(self, mock_get_weight):
        """Test that item is associated with trip."""
        mock_get_weight.return_value = json.dumps({
            "total_weight_kg": 0.5
        })

        from app.models import Trip
        test_trip = Trip(trip_id="test-trip-123", destination="Paris", duration_days=5, doing_laundry=False)
        trips_store["test-trip-123"] = test_trip

        response = self.client.post(
            "/items/weight?trip_id=test-trip-123"
        )

        self.assertEqual(response.status_code, 200)
        
        # Verify item was added to trip
        item_id = response.json()["item"]["item_id"]
        self.assertIn(item_id, test_trip.items)

    @patch('app.routes.item.get_weight')
    def test_read_weight_trip_not_found(self, mock_get_weight):
        """Test error when trip doesn't exist."""
        mock_get_weight.return_value = json.dumps({
            "total_weight_kg": 0.5
        })

        response = self.client.post(
            "/items/weight?trip_id=non-existent-trip"
        )

        self.assertEqual(response.status_code, 404)

class TestDetectEndpoint(unittest.TestCase):
    """Test cases for the /items/detect endpoint."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
        items_store.clear()
        trips_store.clear()

    def tearDown(self):
        items_store.clear()
        trips_store.clear()

    @patch("app.routes.item.detect_objects_yolo")
    def test_detect_creates_new_item(self, mock_yolo):
        """Test creating a new item via image detection."""
        mock_yolo.return_value = {
            "item_name": "Shoes",
            "class": "shoe",
            "confidence_score": 0.85,
            "bounding_boxes": [
                [10.1, 20.2, 50.5, 80.8]
            ]
        }

        test_image = ("test_image.jpg", b"fake-image-bytes", "image/jpeg")
        response = self.client.post(
            "/items/detect",
            files={"image": test_image}
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data["item_name"], "Shoes")
        self.assertEqual(data["class_name"], "shoe")
        self.assertEqual(data["confidence"], 0.85)
        self.assertEqual(len(data["bounding_boxes"]), 1)

        bbox = data["bounding_boxes"][0]
        self.assertEqual(bbox["x_min"], 10.1)
        self.assertEqual(bbox["y_min"], 20.2)

        # Item should be stored
        item_id = data["item_id"]
        self.assertIn(item_id, items_store)

    @patch("app.routes.item.detect_objects_yolo")
    def test_detect_updates_existing_item(self, mock_yolo):
        """Test updating an existing item."""
        from app.models import Item
        existing_item = Item(
            item_id="abc123",
            item_name="OldName",
            class_name="old_class",
            confidence=0.55,
        )
        items_store["abc123"] = existing_item

        mock_yolo.return_value = {
            "item_name": "Backpack",
            "class": "backpack",
            "confidence_score": 0.95,
            "bounding_boxes": [
                [0, 0, 100, 100]
            ]
        }

        test_image = ("image.jpg", b"bytes", "image/jpeg")
        response = self.client.post(
            "/items/detect?item_id=abc123",
            files={"image": test_image}
        )

        self.assertEqual(response.status_code, 200)
        updated = response.json()

        # Check updated fields
        self.assertEqual(updated["item_name"], "Backpack")
        self.assertEqual(updated["class_name"], "backpack")
        self.assertEqual(updated["confidence"], 0.95)

        # Original fields replaced correctly
        self.assertIn("bounding_boxes", updated)
        self.assertEqual(updated["bounding_boxes"][0]["x_min"], 0)

        # Verify items_store is updated
        stored = items_store["abc123"]
        self.assertEqual(stored.item_name, "Backpack")

    @patch("app.routes.item.detect_objects_yolo")
    def test_detect_associates_with_trip(self, mock_yolo):
        """Test that detection associates an item with a trip."""
        mock_yolo.return_value = {
            "item_name": "Laptop",
            "class": "laptop",
            "confidence_score": 0.98,
            "bounding_boxes": [
                [5, 5, 150, 200]
            ]
        }

        # Create trip
        from app.models import Trip
        trip = Trip(trip_id="trip123", destination="Paris", duration_days=3, doing_laundry=True)
        trips_store["trip123"] = trip

        test_image = ("img.png", b"fake", "image/png")
        response = self.client.post(
            "/items/detect?trip_id=trip123",
            files={"image": test_image}
        )

        self.assertEqual(response.status_code, 200)
        item_id = response.json()["item_id"]

        # Should be associated with trip
        self.assertIn(item_id, trips_store["trip123"].items)

    @patch("app.routes.item.detect_objects_yolo")
    def test_detect_invalid_yolo_output(self, mock_yolo):
        """Test handling missing fields in YOLO output."""
        # Missing bounding_boxes
        mock_yolo.return_value = {
            "item_name": "Shirt",
            "class": "shirt",
            "confidence_score": 0.77 
        }

        test_image = ("test.png", b"img", "image/png")
        response = self.client.post(
            "/items/detect",
            files={"image": test_image}
        )

        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("detail", data)

    @patch("app.routes.item.detect_objects_yolo")
    def test_detect_malformed_bbox(self, mock_yolo):
        """Test handling malformed bounding box formats."""
        mock_yolo.return_value = {
            "item_name": "Bottle",
            "class": "bottle",
            "confidence_score": 0.9,
            "bounding_boxes": [
                [1, 2, 3]  # missing 4th coordinate
            ]
        }

        test_image = ("test.png", b"img", "image/png")
        response = self.client.post(
            "/items/detect",
            files={"image": test_image}
        )

        self.assertEqual(response.status_code, 500)
        self.assertIn("Invalid bounding box", response.text)

if __name__ == '__main__':
    unittest.main()

