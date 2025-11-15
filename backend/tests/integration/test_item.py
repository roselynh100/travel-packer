import unittest
import usb.core
from fastapi.testclient import TestClient
import sys
from pathlib import Path

from app.main import app
from app.routes.item import item_store

sys.path.insert(1, str(Path(__file__).parent.parent.parent))

def scale_available():
    """Check if DYMO scale is connected."""
    dev = usb.core.find(idVendor=0x0922, idProduct=0x8009)
    return dev is not None


class TestRealScaleIntegration(unittest.TestCase):
    """Integration tests using the scale"""

    def setUp(self):
        self.client = TestClient(app)
        item_store.clear()
        from app.routes.trip import trips_store
        trips_store.clear()

        from app.models import Trip
        trips_store["realtrip"] = Trip(
            trip_id="realtrip",
            destination="TestCity",
            duration_days=1,
            doing_laundry=False
        )

    def tearDown(self):
        item_store.clear()
        from app.routes.trip import trips_store
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
        self.assertIn(item_id, item_store)

    @unittest.skipUnless(scale_available(), "DYMO scale not connected")
    def test_real_scale_updates_existing_item(self):
        """Update an item using scale weight reading."""

        from app.models import Item
        item = Item(item_id="i1", item_name="Real Item")
        item_store["i1"] = item

        from app.routes.trip import trips_store
        trips_store["t1"].items.append("i1")

        response = self.client.post("/items/weight?trip_id=t1&item_id=i1")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(data["item"]["item_id"], "i1")

        updated = item_store["i1"]
        self.assertIsNotNone(updated.weight_kg)
        self.assertGreater(updated.weight_kg, 0.0)

    @unittest.skipUnless(scale_available(), "DYMO scale not connected")
    def test_real_scale_association_with_trip(self):
        """Ensure scale readings associate item to the trip."""

        response = self.client.post("/items/weight?trip_id=t1")
        self.assertEqual(response.status_code, 200)

        item_id = response.json()["item"]["item_id"]

        from app.routes.trip import trips_store
        self.assertIn(item_id, trips_store["t1"].items)

if __name__ == '__main__':
    unittest.main()
