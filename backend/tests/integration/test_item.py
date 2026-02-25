import os
import sys
import unittest
from pathlib import Path

import usb.core
from fastapi.testclient import TestClient

sys.path.insert(1, str(Path(__file__).parent.parent.parent))

from app.main import app
from app.models import BoundingBox, CVResult, Dimensions, Item
from app.state.db import items_store


def _item_with_cv(item_id: str) -> Item:
    cv = CVResult(
        class_name="bag",
        confidence_score=0.9,
        bounding_boxes=[BoundingBox(x_min=1, y_min=2, x_max=3, y_max=4)],
        dimensions=Dimensions(length=10.0, width=5.0, height=2.0),
    )
    return Item(item_id=item_id, cv_result=cv)


def scale_available():
    """Check if DYMO scale is connected."""
    try:
        dev = usb.core.find(idVendor=0x0922, idProduct=0x8009)
        return dev is not None
    except (usb.core.NoBackendError, Exception):
        return False


class TestRealScaleIntegration(unittest.TestCase):
    """Integration tests using the scale"""

    def setUp(self):
        self.client = TestClient(app)
        items_store.clear()
        from app.state.db import trips_store

        trips_store.clear()

        from app.models import Trip

        trips_store["realtrip"] = Trip(
            trip_id="realtrip",
            destination="TestCity",
            duration_days=1,
            doing_laundry=False,
            items=[],
        )
        trips_store["t1"] = Trip(
            trip_id="t1",
            destination="TestCity",
            duration_days=1,
            doing_laundry=False,
            items=[],
        )

    def tearDown(self):
        items_store.clear()
        from app.state.db import trips_store

        trips_store.clear()

    @unittest.skipUnless(scale_available(), "DYMO scale not connected")
    def test_real_scale_read_creates_item(self):
        """Create an item"""
        from uuid import uuid4

        # Note: item_id must be provided due to current implementation
        new_item_id = str(uuid4())
        response = self.client.post(
            f"/items/weight?trip_id=realtrip&item_id={new_item_id}"
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        # Endpoint now returns Item directly, not a dict with status
        weight = data["weight_kg"]
        self.assertIsNotNone(weight)
        self.assertGreater(weight, 0.0)

        item_id = data["item_id"]
        self.assertEqual(item_id, new_item_id)
        self.assertIn(item_id, items_store)

    @unittest.skipUnless(scale_available(), "DYMO scale not connected")
    def test_real_scale_updates_existing_item(self):
        """Update an item using scale weight reading."""

        from app.models import Item

        item = Item(item_id="i1")
        item.trips.append("t1")
        items_store["i1"] = item

        from app.state.db import trips_store

        trips_store["t1"].items.append("i1")

        response = self.client.post("/items/weight?trip_id=t1&item_id=i1")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        # Endpoint now returns Item directly
        self.assertEqual(data["item_id"], "i1")

        updated = items_store["i1"]
        self.assertIsNotNone(updated.weight_kg)
        self.assertGreater(updated.weight_kg, 0.0)

    @unittest.skipUnless(scale_available(), "DYMO scale not connected")
    def test_real_scale_association_with_trip(self):
        """Ensure scale readings associate item to the trip."""
        from uuid import uuid4

        # Note: item_id must be provided due to current implementation
        new_item_id = str(uuid4())
        response = self.client.post(f"/items/weight?trip_id=t1&item_id={new_item_id}")
        self.assertEqual(response.status_code, 200)

        # Endpoint now returns Item directly
        item_id = response.json()["item_id"]
        self.assertEqual(item_id, new_item_id)

        from app.state.db import trips_store

        self.assertIn(item_id, trips_store["t1"].items)


class TestSerpApiIntegration(unittest.TestCase):
    """Integration test using real SerpAPI endpoint."""

    def setUp(self):
        self.client = TestClient(app)
        items_store.clear()

    def tearDown(self):
        items_store.clear()

    def test_get_item_price_hits_serpapi(self):
        items_store["i1"] = _item_with_cv("i1")

        response = self.client.get(
            "/items/i1/price",
            params={"country": "United States", "limit": 1},
        )
        self.assertEqual(response.status_code, 200, response.text)

        data = response.json()
        print(data)
        self.assertGreaterEqual(len(data), 1)
        self.assertIsInstance(data[0]["item_name"], str)
        self.assertIsInstance(data[0]["source"], str)
        self.assertIsInstance(data[0]["price"], (int, float))
        self.assertEqual(data[0]["currency"], "USD")


if __name__ == "__main__":
    unittest.main()
