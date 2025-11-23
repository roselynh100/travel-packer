import unittest
import sys
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient

sys.path.insert(1, str(Path(__file__).parent.parent.parent))

from app.main import app
from app.state.db import items_store, trips_store
from app.models import Trip, Item, RecommendedItem

class TestPackingRecommendationEndpoint(unittest.TestCase):
    """Unit tests for the packing recommendation endpoint"""

    def setUp(self):
        self.client = TestClient(app)
        items_store.clear()
        trips_store.clear()

    def tearDown(self):
        items_store.clear()
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
        items_store["a"] = i1
        items_store["b"] = i2
        trip.items = ["a", "b"]

        mock_algo.return_value = [i1.model_dump()]

        response = self.client.post("/trips/trip1/removal-recommendations")
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

        items_store["x"] = Item(item_id="x", item_name="Hat", weight_kg=0.5)
        trip.items = ["x"]

        mock_algo.return_value = []

        response = self.client.post("/trips/t2/removal-recommendations")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_recommendation_trip_not_found(self):
        """Should return 404 if trip doesn't exist."""

        response = self.client.post("/trips/unknown/removal-recommendations")
        self.assertEqual(response.status_code, 404)

    @patch("app.routes.trip.packing_algorithm")
    def test_recommendation_ignores_missing_items(self, mock_algo):
        """Trip references an item not present in items_store."""

        trip = Trip(
            trip_id="trip3",
            destination="NYC",
            duration_days=4,
            doing_laundry=False
        )
        trips_store["trip3"] = trip

        # Trip references one real & one missing item
        real_item = Item(item_id="real", item_name="Laptop", weight_kg=2.5)
        items_store["real"] = real_item
        trip.items = ["real", "ghost123"]

        mock_algo.return_value = [real_item.model_dump()]

        response = self.client.post("/trips/trip3/removal-recommendations")
        self.assertEqual(response.status_code, 200)

        # Should only pass existing items to algorithm
        mock_algo.assert_called_once()
        args = mock_algo.call_args[0][0]
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0].item_id, "real")

class TestUpdatingTrip(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        trips_store.clear()

        self.trip_id = "t1"
        self.initial_trip = Trip(
            trip_id=self.trip_id,
            destination="Tokyo",
            duration_days=5,
            doing_laundry=False,
            items=["item1", "item2"],
        )
        trips_store[self.trip_id] = self.initial_trip

    def tearDown(self):
        trips_store.clear()

    def test_update_trip_omits_items_keeps_existing(self):
        """If `items` is omitted, existing list should be preserved."""

        payload = {
            "destination": "Kyoto",
            "duration_days": 7,
            "doing_laundry": True
        }

        response = self.client.put(f"/trips/{self.trip_id}", json=payload)
        self.assertEqual(response.status_code, 200)

        updated = response.json()

        self.assertEqual(updated["items"], ["item1", "item2"])

        self.assertEqual(updated["destination"], "Kyoto")
        self.assertEqual(updated["duration_days"], 7)
        self.assertEqual(updated["doing_laundry"], True)

    def test_update_trip_sets_items_to_empty_list(self):
        """If client sends items=[], the list should become empty."""

        from app.state.db import trips_store
        trips_store[self.trip_id].items = ["itemA"]

        payload = {
            "destination": "Osaka",
            "duration_days": 3,
            "doing_laundry": False,
            "items": []   # Explicit empty
        }

        response = self.client.put(f"/trips/{self.trip_id}", json=payload)
        self.assertEqual(response.status_code, 200)

        updated = response.json()

        self.assertEqual(updated["items"], [])

        self.assertEqual(updated["destination"], "Osaka")
        self.assertEqual(updated["duration_days"], 3)

class TestTripRecommendations(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        trips_store.clear()

    def tearDown(self):
        trips_store.clear()

    def test_trip_not_found(self):
        """POST /trips/{id}/recommendations returns 404 when trip doesn't exist."""
        response = self.client.post("/trips/does-not-exist/recommendations")
        self.assertEqual(response.status_code, 404)
        self.assertIn("Trip not found", response.text)

    @patch("app.routes.trip.generate_recommendation_list")
    def test_recommendations_success(self, mock_gen):
        """Valid trip should return recommendations."""
        trips_store["t1"] = Trip(
            trip_id="t1",
            destination="Tokyo",
            duration_days=7,
            doing_laundry=True,
            activities="lots of walking and sightseeing"
        )

        mock_gen.return_value = [
            RecommendedItem(item_name="Walking Shoes"),
            RecommendedItem(item_name="Water Bottle"),
        ]

        response = self.client.post("/trips/t1/recommendations")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["item_name"], "Walking Shoes")
        self.assertEqual(data[1]["item_name"], "Water Bottle")

    @patch("app.routes.trip.generate_recommendation_list")
    def test_recommendations_empty_list(self, mock_gen):
        """If algorithm returns empty list, endpoint returns empty list."""
        trips_store["t1"] = Trip(
            trip_id="t1",
            destination="Paris",
            duration_days=4,
            doing_laundry=False,
            activities="fine dining"
        )

        mock_gen.return_value = []

        response = self.client.post("/trips/t1/recommendations")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    @patch("app.routes.trip.generate_recommendation_list")
    def test_recommendations_forwards_correct_fields(self, mock_gen):
        """Ensure correct trip fields are passed to the generator."""
        trips_store["t1"] = Trip(
            trip_id="t1",
            destination="Banff",
            duration_days=3,
            doing_laundry=False,
            activities="hiking"
        )

        mock_gen.return_value = [RecommendedItem(item_name="Hiking Boots")]

        response = self.client.post("/trips/t1/recommendations")
        self.assertEqual(response.status_code, 200)

        mock_gen.assert_called_once()
        # Verify the trip object passed has the correct fields
        called_trip = mock_gen.call_args[0][0]
        self.assertEqual(called_trip.destination, "Banff")
        self.assertEqual(called_trip.duration_days, 3)
        self.assertEqual(called_trip.doing_laundry, False)
        self.assertEqual(called_trip.activities, "hiking")

    @patch("app.routes.trip.generate_recommendation_list")
    def test_recommendations_invalid_algorithm_output(self, mock_gen):
        """If the algorithm returns invalid data, endpoint should error."""
        trips_store["t1"] = Trip(
            trip_id="t1",
            destination="London",
            duration_days=5,
            doing_laundry=True,
            activities=None
        )

        mock_gen.return_value = None
        response = self.client.post("/trips/t1/recommendations")
        self.assertEqual(response.status_code, 500)
        self.assertIn("list", response.text.lower())


if __name__ == '__main__':
    unittest.main()

