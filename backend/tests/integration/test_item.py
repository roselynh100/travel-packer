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
        from uuid import uuid4
        
        # Note: item_id must be provided due to current implementation
        new_item_id = str(uuid4())
        response = self.client.post(f"/items/weight?trip_id=realtrip&item_id={new_item_id}")
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

if __name__ == '__main__':
    unittest.main()
