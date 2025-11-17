import unittest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

sys.path.insert(1, str(Path(__file__).parent.parent.parent))

from app.main import app
from app.state.db import items_store, trips_store
from app.models import Trip, Item

# TO-DO: currently, im using just the weight to recommend what to remove, so when the actual
# packing recommendation algo is in place, we'll need to update these test cases

class TestPackingRecommendationIntegration(unittest.TestCase):
    """Integration tests using the real packing_algorithm."""

    def setUp(self):
        self.client = TestClient(app)
        items_store.clear()
        trips_store.clear()

    def tearDown(self):
        items_store.clear()
        trips_store.clear()

    def test_integration_recommends_heavy_items(self):
        """Algorithm returns list of items recommended to be removed"""

        trip = Trip(
            trip_id="tripX",
            destination="Tokyo",
            duration_days=6,
            doing_laundry=False
        )
        trips_store["tripX"] = trip

        heavy = Item(item_id="a", item_name="Boots", weight_kg=4.2)
        light = Item(item_id="b", item_name="Towel", weight_kg=0.4)
        items_store["a"] = heavy
        items_store["b"] = light
        trip.items = ["a", "b"]

        response = self.client.post("/trips/tripX/packing-recommendation")
        self.assertEqual(response.status_code, 200)

        result = response.json()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["item_id"], "a")

    def test_integration_no_items_to_remove(self):
        """Algorithm returns empty when nothing needs to be removed"""

        trip = Trip(
            trip_id="tripY",
            destination="Paris",
            duration_days=5,
            doing_laundry=True
        )
        trips_store["tripY"] = trip

        items_store["a"] = Item(item_id="a", item_name="Shirt", weight_kg=1.0)
        items_store["b"] = Item(item_id="b", item_name="Shorts", weight_kg=0.5)
        trip.items = ["a", "b"]

        response = self.client.post("/trips/tripY/packing-recommendation")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

if __name__ == '__main__':
    unittest.main()

