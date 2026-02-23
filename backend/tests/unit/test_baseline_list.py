import datetime
import sys
import unittest
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.models import Activity, Destination, RecommendedItem, Trip
from machine_learning.generator import (
    CATEGORIES,
    baseline_list_algorithm,
    get_base_items,
    get_conditional_items,
)


class TestBaselineAlgorithm(unittest.TestCase):

    def setUp(self):
        """Set up common data for tests."""
        self.default_dest = Destination(city="London", country="UK")
        # Ensure dates are datetime objects as required by the Trip Pydantic model
        self.start_date = "2027-02-14"
        self.end_date = "2027-02-20"

    def test_get_base_items(self):
        """Verify that categories 1, 3, 4, 5 are always returned."""
        items = get_base_items()
        item_names = [i.item_name for i in items]

        # Now exactly 4: tops, pants, shoes, toiletries
        self.assertEqual(len(items), 4)
        self.assertIn(CATEGORIES[1], item_names)  # tops
        self.assertIn(CATEGORIES[3], item_names)  # pants
        self.assertIn(CATEGORIES[5], item_names)  # toiletries

        # Shorts (2) should NO LONGER be in base items
        self.assertNotIn(CATEGORIES[2], item_names)

    def test_get_conditional_items_work(self):
        """Rule: Electronics (ID 6) should appear if Activity.work is in activities."""
        items = get_conditional_items(activities=[Activity.work], low_temp=5.0)
        item_names = [i.item_name for i in items]
        self.assertIn(CATEGORIES[6], item_names)

    def test_get_conditional_items_weather_cold(self):
        """Rule: Jackets (ID 7) should appear if low_temp < 0."""
        items_cold = get_conditional_items(activities=[], low_temp=-5.0)
        item_names = [i.item_name for i in items_cold]
        self.assertIn(CATEGORIES[7], item_names)
        self.assertNotIn(CATEGORIES[2], item_names)  # No shorts in the cold

    def test_get_conditional_items_weather_warm(self):
        """Rule: Shorts (ID 2) should appear if low_temp > 10."""
        items_warm = get_conditional_items(activities=[], low_temp=15.0)
        item_names = [i.item_name for i in items_warm]
        self.assertIn(CATEGORIES[2], item_names)
        self.assertNotIn(CATEGORIES[7], item_names)  # No jackets in the heat

    def test_baseline_list_algorithm_integration(self):
        """Full integration: Base (4) + Work (1) + Warm (1) = 6 total."""
        trip = Trip(
            destination="Miami",
            destination_details=self.default_dest,
            duration_days=4,
            start_date=self.start_date,
            end_date=self.end_date,
            doing_laundry=False,
            activities=[Activity.work],
            lowest_temp=25.0,  # Should trigger electronics and shorts
        )

        results = baseline_list_algorithm(trip)
        item_names = [i.item_name for i in results]

        # 4 Base + 1 Electronics + 1 Shorts = 6
        self.assertEqual(len(results), 6)
        self.assertIn(CATEGORIES[6], item_names)  # Electronics
        self.assertIn(CATEGORIES[2], item_names)  # Shorts

    def test_boundary_conditions(self):
        """Test the exact cutoffs for 0 and 10 degrees."""
        # 0.0 degrees: Neither jacket (<0) nor shorts (>10)
        items_zero = get_conditional_items(activities=[], low_temp=0.0)
        self.assertEqual(len(items_zero), 0)

        # 10.0 degrees: Exactly 10 should not trigger shorts (>10)
        items_ten = get_conditional_items(activities=[], low_temp=10.0)
        self.assertEqual(len(items_ten), 0)


if __name__ == "__main__":
    unittest.main()
