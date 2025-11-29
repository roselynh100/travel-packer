import sys
import unittest
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.models import RecommendedItem, Trip
from machine_learning.item_groups import ACCESSORIES, CLOTHING, TOILETRIES

# UPDATE: Import the functions to be tested
from machine_learning.poc_decision_model import (
    baseline_list_algorithm,
    get_base_items,
    get_weather_items,
    get_work_items,
)


class TestBaselineAlgorithm(unittest.TestCase):

    def setUp(self):
        """Run before every test."""
        self.dummy_trip = Trip(
            destination="Test City", duration_days=3, doing_laundry=False
        )

    def test_get_base_items(self):
        """
        Test that get_base_items returns the exact combination of
        CLOTHING + ACCESSORIES + TOILETRIES from item_groups.py.
        """
        items = get_base_items()

        # Calculate expected length dynamically based on the real lists
        expected_len = len(CLOTHING) + len(ACCESSORIES) + len(TOILETRIES)

        self.assertEqual(len(items), expected_len)

        # Verify specific items from your lists appear in the result
        item_names = [i.item_name for i in items]
        self.assertIn("Shirt", item_names)  # From CLOTHING
        self.assertIn("Sunglasses", item_names)  # From ACCESSORIES
        self.assertIn("Toothbrush", item_names)  # From TOILETRIES

    def test_get_work_items_positive(self):
        """Test that 'work' in activities triggers laptop recommendations."""
        items = get_work_items("Business Work")

        item_names = [i.item_name for i in items]
        self.assertIn("Laptop", item_names)
        self.assertIn("Laptop Charger", item_names)

    def test_get_work_items_negative(self):
        """Test that non-work activities return an empty list."""
        items = get_work_items("Relaxing at the beach")
        self.assertEqual(items, [])

    def test_get_weather_items_cold(self):
        """Test that temp < 10 triggers a coat."""
        items = get_weather_items(5.0)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].item_name, "Coat")

    def test_get_weather_items_warm(self):
        """Test that temp >= 10 returns no weather items."""
        self.assertEqual(get_weather_items(25.0), [])

    def test_baseline_list_algorithm_integration(self):
        """
        Test the full packing list generation using real item data.
        """
        trip = Trip(
            destination="New York",
            duration_days=4,
            doing_laundry=False,
            activities="Work Conference",  # Triggers work items
            lowest_temp=0.0,  # Triggers cold weather items
        )

        results = baseline_list_algorithm(trip)
        item_names = [i.item_name for i in results]

        # 1. Check for Base Items (from item_groups.py)
        self.assertIn("Socks", item_names)
        self.assertIn("Toothpaste", item_names)

        # 2. Check for Logic Items
        self.assertIn("Laptop", item_names)  # From Work logic
        self.assertIn("Coat", item_names)  # From Weather logic

        # 3. Check Total Count
        # Base items (4+2+2 = 8) + Work (2) + Weather (1) = 11 items total
        expected_count = len(CLOTHING) + len(ACCESSORIES) + len(TOILETRIES) + 2 + 1
        self.assertEqual(len(results), expected_count)


if __name__ == "__main__":
    unittest.main()
