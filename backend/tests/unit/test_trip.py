import unittest
import sys
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient

sys.path.insert(1, str(Path(__file__).parent.parent.parent))

from app.main import app
from app.routes.item import item_store
from app.routes.trip import trips_store
from app.models import Trip, Item

class TestPackingRecommendationEndpoint(unittest.TestCase):
    """Unit tests for the packing recommendation endpoint"""

    def setUp(self):
        self.client = TestClient(app)
        item_store.clear()
        trips_store.clear()

    def tearDown(self):
        item_store.clear()
        trips_store.clear()

    @patch("app.routes.trip.packing_algorithm")
    def test_recommendation_calls_algorithm(self, mock_algo):
        """Endpoint should call packing_algorithm and return its output."""

        trip = Trip(
            trip_id="trip1",
            destination="Rome",
            duration_days=3,
            doing_laundry=False
        )
        trips_store["trip1"] = trip

        i1 = Item(item_id="a", item_name="Boots", weight_kg=4.0)
        i2 = Item(item_id="b", item_name="Socks", weight_kg=0.2)
        item_store["a"] = i1
        item_store["b"] = i2
        trip.items = ["a", "b"]

        mock_algo.return_value = [i1.model_dump()]

        response = self.client.post("/trips/trip1/packing-recommendation")
        self.assertEqual(response.status_code, 200)

        self.assertEqual(response.json(), [i1.model_dump()])

        mock_algo.assert_called_once()
        called_args = mock_algo.call_args[0][0]
        self.assertEqual(len(called_args), 2)

    @patch("app.routes.trip.packing_algorithm")
    def test_recommendation_empty(self, mock_algo):
        """Algorithm returns empty list."""

        trip = Trip(
            trip_id="t2",
            destination="Berlin",
            duration_days=5,
            doing_laundry=True
        )
        trips_store["t2"] = trip

        item_store["x"] = Item(item_id="x", item_name="Hat", weight_kg=0.5)
        trip.items = ["x"]

        mock_algo.return_value = []

        response = self.client.post("/trips/t2/packing-recommendation")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_recommendation_trip_not_found(self):
        """Should return 404 if trip doesn't exist."""

        response = self.client.post("/trips/unknown/packing-recommendation")
        self.assertEqual(response.status_code, 404)

    @patch("app.routes.trip.packing_algorithm")
    def test_recommendation_ignores_missing_items(self, mock_algo):
        """Trip references an item not present in item_store."""

        trip = Trip(
            trip_id="trip3",
            destination="NYC",
            duration_days=4,
            doing_laundry=False
        )
        trips_store["trip3"] = trip

        # Trip references one real & one missing item
        real_item = Item(item_id="real", item_name="Laptop", weight_kg=2.5)
        item_store["real"] = real_item
        trip.items = ["real", "ghost123"]

        mock_algo.return_value = [real_item.model_dump()]

        response = self.client.post("/trips/trip3/packing-recommendation")
        self.assertEqual(response.status_code, 200)

        # Should only pass existing items to algorithm
        mock_algo.assert_called_once()
        args = mock_algo.call_args[0][0]
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0].item_id, "real")

if __name__ == '__main__':
    unittest.main()

