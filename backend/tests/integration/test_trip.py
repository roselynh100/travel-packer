import datetime
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.path.insert(1, str(Path(__file__).parent.parent.parent))

from app.main import app
from app.models import Airline, BagType, Item, Location, Trip
from app.state.db import items_store, trips_store
from constants import MYCLIMATE_API_PASSWORD, MYCLIMATE_API_USERNAME

# TO-DO: currently, im using just the weight to recommend what to remove, so when the actual
# packing recommendation algo is in place, we'll need to update these test cases


def _trip_dates(duration_days: int) -> tuple[datetime.datetime, datetime.datetime]:
    today = datetime.date.today()
    start_dt = datetime.datetime.combine(today, datetime.time(hour=9))
    end_dt = start_dt + datetime.timedelta(days=duration_days - 1)
    return start_dt, end_dt


def _integration_trip(
    trip_id: str,
    destination_city: str,
    destination_country: str,
    destination_airport_code: str,
    duration_days: int,
    doing_laundry: bool,
) -> Trip:
    start_dt, end_dt = _trip_dates(duration_days)
    return Trip(
        trip_id=trip_id,
        origin_details=Location(city="Home", country="US", airport_code="JFK"),
        destination_details=Location(
            city=destination_city,
            country=destination_country,
            airport_code=destination_airport_code,
        ),
        start_date=start_dt,
        end_date=end_dt,
        doing_laundry=doing_laundry,
        bag_type=BagType.carry_on,
        airline=Airline.air_canada,
        items=[],
        activities=[],
    )


def myclimate_credentials_available() -> bool:
    return MYCLIMATE_API_USERNAME not in {"", "KEY"} and MYCLIMATE_API_PASSWORD not in {
        "",
        "KEY",
    }


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

        trip = _integration_trip(
            trip_id="tripX",
            destination_city="Tokyo",
            destination_country="Japan",
            destination_airport_code="HND",
            duration_days=6,
            doing_laundry=False,
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

        trip = _integration_trip(
            trip_id="tripY",
            destination_city="Paris",
            destination_country="France",
            destination_airport_code="CDG",
            duration_days=5,
            doing_laundry=True,
        )
        trips_store["tripY"] = trip

        item_a = Item(item_id="a", weight_kg=1.0)
        item_a.trips.append("tripY")
        item_b = Item(item_id="b", weight_kg=0.5)
        item_b.trips.append("tripY")

        items_store["a"] = item_a
        items_store["b"] = item_b

        trip.items = ["a", "b"]

        response = self.client.get("/trips/tripY/recommendations")
        self.assertEqual(response.status_code, 200)


class TestTripEmissionsIntegration(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        trips_store.clear()

    def tearDown(self):
        trips_store.clear()

    @unittest.skipUnless(
        myclimate_credentials_available(),
        "MYCLIMATE_API_USERNAME and MYCLIMATE_API_PASSWORD must be configured in constants.py",
    )
    def test_emissions_jfk_to_lax(self):
        trip = _integration_trip(
            trip_id="trip-emissions-jfk-lax",
            destination_city="Los Angeles",
            destination_country="US",
            destination_airport_code="LAX",
            duration_days=2,
            doing_laundry=False,
        )
        trips_store[trip.trip_id] = trip

        with (
            patch(
                "helpers.trip_helpers.MYCLIMATE_API_USERNAME",
                MYCLIMATE_API_USERNAME,
            ),
            patch(
                "helpers.trip_helpers.MYCLIMATE_API_PASSWORD",
                MYCLIMATE_API_PASSWORD,
            ),
        ):
            response = self.client.post(f"/trips/{trip.trip_id}/emissions")

        print(
            f"JFK -> LAX response status={response.status_code}, body={response.text}"
        )

        self.assertEqual(response.status_code, 200, response.text)

        data = response.json()
        print(f"JFK -> LAX emissions_per_kg: {data['emissions_per_kg']}")
        self.assertIsInstance(data["emissions_per_kg"], (int, float))
        self.assertGreater(data["emissions_per_kg"], 0.0)


if __name__ == "__main__":
    unittest.main()
