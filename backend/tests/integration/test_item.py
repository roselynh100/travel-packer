import unittest
import usb.core
from fastapi.testclient import TestClient
import sys
from pathlib import Path

sys.path.insert(1, str(Path(__file__).parent.parent.parent))

from app.main import app
from app.state.db import items_store

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
            items=[]
        )
        trips_store["t1"] = Trip(
            trip_id="t1",
            destination="TestCity",
            duration_days=1,
            doing_laundry=False,
            items=[]
        )

    def tearDown(self):
        items_store.clear()
        from app.state.db import trips_store
        trips_store.clear()

    @unittest.skipUnless(scale_available(), "DYMO scale not connected")
    def test_real_scale_read_creates_item(self):
        """Create an item"""

        response = self.client.post("/items/weight?trip_id=realtrip")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["status"], "success")

        weight = data["total_weight_kg"]
        self.assertIsNotNone(weight)
        self.assertGreater(weight, 0.0)

        item_id = data["item"]["item_id"]
        self.assertIn(item_id, items_store)

    @unittest.skipUnless(scale_available(), "DYMO scale not connected")
    def test_real_scale_updates_existing_item(self):
        """Update an item using scale weight reading."""

        from app.models import Item
        item = Item(item_id="i1")
        items_store["i1"] = item

        from app.state.db import trips_store
        trips_store["t1"].items.append("i1")

        response = self.client.post("/items/weight?trip_id=t1&item_id=i1")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["item"]["item_id"], "i1")

        updated = items_store["i1"]
        self.assertIsNotNone(updated.weight_kg)
        self.assertGreater(updated.weight_kg, 0.0)

    @unittest.skipUnless(scale_available(), "DYMO scale not connected")
    def test_real_scale_association_with_trip(self):
        """Ensure scale readings associate item to the trip."""

        response = self.client.post("/items/weight?trip_id=t1")
        self.assertEqual(response.status_code, 200)

        item_id = response.json()["item"]["item_id"]

        from app.state.db import trips_store
        self.assertIn(item_id, trips_store["t1"].items)

if __name__ == '__main__':
    unittest.main()
