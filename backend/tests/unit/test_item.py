import unittest
import sys
from pathlib import Path
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
import json

sys.path.insert(1, str(Path(__file__).parent.parent.parent))

from app.main import app
from app.routes.item import item_store


class TestReadWeight(unittest.TestCase):
    """Test cases for the read_weight endpoint."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = TestClient(app)
        item_store.clear()
        # Also clear trips store to avoid test interference
        from app.routes.trip import trips_store
        trips_store.clear()

    def tearDown(self):
        """Clean up after each test."""
        item_store.clear()
        from app.routes.trip import trips_store
        trips_store.clear()

    @patch('app.routes.item.get_weight')
    def test_read_weight_create_new_item(self, mock_get_weight):
        """Test creating a new item with weight reading."""
        mock_get_weight.return_value = json.dumps({
            "total_weight_kg": 0.5
        })

        from app.routes.trip import trips_store
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
        self.assertIn(item_id, item_store)

    @patch('app.routes.item.get_weight')
    def test_read_weight_update_existing_item(self, mock_get_weight):
        """Test updating an existing item's weight."""
        from app.models import Item
        existing_item = Item(item_id="existing-item-123", name="Test Item", weight_kg=0.3)
        item_store["existing-item-123"] = existing_item

        from app.routes.trip import trips_store
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
        updated_item = item_store["existing-item-123"]
        self.assertEqual(updated_item.weight_kg, 0.7)
        self.assertEqual(updated_item.name, "Test Item")  # Other fields preserved

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

        from app.routes.trip import trips_store
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


if __name__ == '__main__':
    unittest.main()

