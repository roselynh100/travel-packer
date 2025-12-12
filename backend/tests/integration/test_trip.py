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
        """Algorithm returns items recommended to be removed"""

        trip = Trip(
            trip_id="tripX",
            destination="Tokyo",
            duration_days=6,
            doing_laundry=False
        )
        trips_store["tripX"] = trip

        i1 = Item(item_id="a", weight_kg=4.2)
        i1.trips.append("tripX")

        items_store["a"] = i1

        trip.items = ["a"]

        resp = self.client.get("/trips/tripX/item/a/packing-decision")

        # TO-DO: add finer test cases once we have more set-in-stone removal logic
        self.assertEqual(resp.status_code, 200)


    def test_integration_no_items_to_remove(self):
        """Algorithm returns empty when nothing needs to be removed"""

        trip = Trip(
            trip_id="tripY",
            destination="Paris",
            duration_days=5,
            doing_laundry=True
        )
        trips_store["tripY"] = trip

        item_a = Item(item_id="a", weight_kg=1.0)
        item_a.trips.append("tripY")
        item_b = Item(item_id="b", weight_kg=0.5)
        item_b.trips.append("tripY")

        items_store["a"] = item_a
        items_store["b"] = item_b

        trip.items = ["a", "b"]

        response = self.client.get("/trips/tripY/wrecommendations")
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
