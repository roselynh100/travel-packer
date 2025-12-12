import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.path.insert(1, str(Path(__file__).parent.parent.parent))

from app.main import app
from app.models import Item, RecommendedItem, Trip
from app.state.db import items_store, trips_store


class TestRemovalRecommendationEndpoint(unittest.TestCase):
    """Unit tests for the single-item removal recommendation endpoint"""

    def setUp(self):
        self.client = TestClient(app)
        items_store.clear()
        trips_store.clear()

    def tearDown(self):
        items_store.clear()
        trips_store.clear()

    def test_removal_recommendation_success(self):
        """Endpoint should return a valid RemovalRecommendation."""

        trip = Trip(
            trip_id="t1",
            destination="Rome",
            duration_days=3,
            doing_laundry=False,
            items=["i1"],
        )
        trips_store["t1"] = trip

        item = Item(item_id="i1", weight_kg=5.0)
        item.trips.append("t1")
        items_store["i1"] = item

        response = self.client.get("/trips/t1/item/i1/packing-decision")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("status", data)
        self.assertIn("reason", data)

    def test_removal_recommendation_trip_not_found(self):
        """Should return 404 when trip doesn't exist."""

        item = Item(item_id="i1", weight_kg=2.0)
        items_store["i1"] = item

        response = self.client.get("/trips/fake/item/i1/packing-decision")
        self.assertEqual(response.status_code, 404)

    def test_removal_recommendation_item_not_found(self):
        """Should return 404 when item doesn't exist."""

        trip = Trip(
            trip_id="t1",
            destination="Rome",
            duration_days=3,
            doing_laundry=False,
            items=[],
        )
        trips_store["t1"] = trip

        response = self.client.get("/trips/t1/item/nope/packing-decision")
        self.assertEqual(response.status_code, 404)



class TestTripRecommendationsEndpoint(unittest.TestCase):
    """Unit tests for /trips/{trip_id}/recommendations endpoint"""

    def setUp(self):
        self.client = TestClient(app)
        trips_store.clear()

    def tearDown(self):
        trips_store.clear()

    def test_trip_not_found(self):
        """Should return 404 if trip doesn't exist."""
        response = self.client.get("/trips/does-not-exist/recommendations")
        self.assertEqual(response.status_code, 404)
        self.assertIn("Trip not found", response.text)

    @patch("app.routes.trip.baseline_list_algorithm")
    def test_recommendations_success(self, mock_gen):
        """Valid trip should return recommendations."""
        trips_store["t1"] = Trip(
            trip_id="t1",
            destination="Tokyo",
            duration_days=7,
            doing_laundry=True,
            activities="lots of walking",
        )

        mock_gen.return_value = [
            RecommendedItem(item_name="Walking Shoes", priority=1),
            RecommendedItem(item_name="Water Bottle", priority=2),
        ]

        response = self.client.get("/trips/t1/recommendations")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["item_name"], "Walking Shoes")
        self.assertEqual(data[1]["item_name"], "Water Bottle")

        mock_gen.assert_called_once()
        passed_trip = mock_gen.call_args[0][0]
        self.assertEqual(passed_trip.trip_id, "t1")

    @patch("app.routes.trip.baseline_list_algorithm")
    def test_recommendations_empty_list(self, mock_gen):
        """If algorithm returns empty list, endpoint returns empty list."""
        trips_store["t1"] = Trip(
            trip_id="t1",
            destination="Paris",
            duration_days=3,
            doing_laundry=False,
            activities="sightseeing",
        )

        mock_gen.return_value = []

        response = self.client.get("/trips/t1/recommendations")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    @patch("app.routes.trip.baseline_list_algorithm")
    def test_recommendations_invalid_output(self, mock_gen):
        """If algorithm returns invalid output, endpoint should error."""
        trips_store["t1"] = Trip(
            trip_id="t1",
            destination="London",
            duration_days=5,
            doing_laundry=True,
            activities="museums",
        )

        mock_gen.return_value = None

        response = self.client.get("/trips/t1/recommendations")
        self.assertEqual(response.status_code, 500)
        self.assertIn("no recommendations generated", response.text.lower())

    @patch("app.routes.trip.baseline_list_algorithm")
    def test_recommendations_forwards_correct_trip_data(self, mock_gen):
        """Ensure the trip object passed to algorithm contains correct fields."""
        trips_store["t1"] = Trip(
            trip_id="t1",
            destination="Banff",
            duration_days=4,
            doing_laundry=False,
            activities="hiking trails",
        )

        mock_gen.return_value = [RecommendedItem(item_name="Jacket")]

        response = self.client.get("/trips/t1/recommendations")
        self.assertEqual(response.status_code, 200)

        mock_gen.assert_called_once()
        t = mock_gen.call_args[0][0]
        self.assertEqual(t.destination, "Banff")
        self.assertEqual(t.duration_days, 4)
        self.assertEqual(t.doing_laundry, False)
        self.assertEqual(t.activities, "hiking trails")


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

        payload = {"destination": "Kyoto", "duration_days": 7, "doing_laundry": True}

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
            "items": [],  # Explicit empty
        }

        response = self.client.put(f"/trips/{self.trip_id}", json=payload)
        self.assertEqual(response.status_code, 200)

        updated = response.json()

        self.assertEqual(updated["items"], [])

        self.assertEqual(updated["destination"], "Osaka")
        self.assertEqual(updated["duration_days"], 3)

class TestRemoveItemFromTrip(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        trips_store.clear()
        items_store.clear()

    def tearDown(self):
        trips_store.clear()
        items_store.clear()

    def test_remove_item_from_trip_success(self):
        trip = Trip(
            trip_id="t1",
            destination="Rome",
            duration_days=3,
            doing_laundry=False,
            items=["i1"]
        )
        item = Item(item_id="i1", trips=["t1"])

        trips_store["t1"] = trip
        items_store["i1"] = item

        response = self.client.delete("/trips/t1/item/i1")
        self.assertEqual(response.status_code, 200)

        self.assertNotIn("i1", trips_store["t1"].items)
        self.assertNotIn("t1", items_store["i1"].trips)


class TestAddItemToTrip(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        trips_store.clear()
        items_store.clear()

    def tearDown(self):
        trips_store.clear()
        items_store.clear()

    def test_add_item_to_trip_success(self):
        trip = Trip(
            trip_id="t1",
            destination="Paris",
            duration_days=4,
            doing_laundry=False,
            items=[]
        )
        item = Item(item_id="i1", weight_kg=1.0)

        trips_store["t1"] = trip
        items_store["i1"] = item

        response = self.client.post("/trips/t1/item/i1")
        self.assertEqual(response.status_code, 200 or 204)

        self.assertIn("i1", trips_store["t1"].items)
        self.assertIn("t1", items_store["i1"].trips)

    def test_add_item_trip_not_found(self):
        items_store["i1"] = Item(item_id="i1")

        response = self.client.post("/trips/nope/item/i1")
        self.assertEqual(response.status_code, 404)

    def test_add_item_item_not_found(self):
        trips_store["t1"] = Trip(
            trip_id="t1",
            destination="Rome",
            duration_days=3,
            doing_laundry=False
        )

        response = self.client.post("/trips/t1/item/nope")
        self.assertEqual(response.status_code, 404)


class TestRecalculateTripTotals(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        trips_store.clear()
        items_store.clear()

    def tearDown(self):
        trips_store.clear()
        items_store.clear()

    def test_recalculate_totals(self):
        trips_store["t1"] = Trip(
            trip_id="t1",
            destination="Test",
            duration_days=2,
            doing_laundry=False,
            items=["i1", "i2"]
        )

        items_store["i1"] = Item(item_id="i1", weight_kg=2.0, estimated_volume_cm3=10)
        items_store["i2"] = Item(item_id="i2", weight_kg=3.0, estimated_volume_cm3=5)

        response = self.client.post("/trips/t1/recalculate-totals")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["total_weight"], 5.0)
        self.assertEqual(data["total_volume"], 15.0)


if __name__ == "__main__":
    unittest.main()
