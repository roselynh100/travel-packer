import datetime
import math
import sys
import unittest
from collections import Counter
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.models import Activity, Airline, BagType, Location, RecommendedItem, Trip
from machine_learning.generator import (
    CATEGORIES,
    baseline_list_algorithm,
    get_conditional_items,
    get_dynamic_clothes,
)


class TestBaselineAlgorithm(unittest.TestCase):

    def setUp(self):
        """Set up common data for tests."""
        self.default_dest = Location(city="London", country="UK", airport_code="LHR")
        self.base_date = datetime.datetime(2027, 2, 14)

    def _create_trip(
        self,
        days=4,
        activities=None,
        lowest_temp=None,
        highest_temp=None,
        precipitation_percentage=0.0,
        doing_laundry=False,
    ):
        """Helper method to generate a Trip object for testing based on duration."""
        end_date = self.base_date + datetime.timedelta(days=days - 1)

        return Trip(
            origin_details=self.default_dest,
            destination_details=self.default_dest,
            start_date=self.base_date,
            end_date=end_date,
            doing_laundry=doing_laundry,
            bag_type=BagType.carry_on,
            airline=Airline.air_canada,
            activities=activities or [],
            lowest_temp=lowest_temp,
            highest_temp=highest_temp,
            precipitation_percentage=precipitation_percentage,
        )

    def _count_items(self, items_list: list) -> dict:
        """Helper to count occurrences of item names in a list of RecommendedItems."""
        names = [item.item_name for item in items_list]
        return dict(Counter(names))

    # --- DYNAMIC CLOTHES TESTS ---

    def test_get_dynamic_clothes_short_trip_cold(self):
        """Test a 4-day trip in cold weather (pants)."""
        trip = self._create_trip(days=4, lowest_temp=10.0)
        items = self._count_items(get_dynamic_clothes(trip))

        self.assertEqual(items.get(CATEGORIES[1], 0), 4)  # 4 tops
        self.assertEqual(items.get(CATEGORIES[3], 0), 2)  # 2 pants (4/2)
        self.assertEqual(items.get(CATEGORIES[2], 0), 0)  # 0 shorts
        self.assertEqual(items.get(CATEGORIES[4], 0), 1)  # 1 pair of shoes (<= 4 days)
        self.assertEqual(items.get(CATEGORIES[5], 0), 1)  # 1 toiletries

    def test_get_dynamic_clothes_long_trip_hot_no_laundry(self):
        """Test a 10-day trip in hot weather without laundry."""
        trip = self._create_trip(days=10, lowest_temp=25.0, doing_laundry=False)
        items = self._count_items(get_dynamic_clothes(trip))

        self.assertEqual(items.get(CATEGORIES[1], 0), 10)  # 10 tops
        self.assertEqual(items.get(CATEGORIES[2], 0), 5)  # 5 shorts
        self.assertEqual(items.get(CATEGORIES[3], 0), 0)  # 0 pants
        self.assertEqual(items.get(CATEGORIES[4], 0), 2)  # 2 pairs of shoes (> 4 days)

    def test_get_dynamic_clothes_laundry_cap(self):
        """Test a 14-day trip with laundry (should cap at 7 days)."""
        trip = self._create_trip(days=14, lowest_temp=15.0, doing_laundry=True)
        items = self._count_items(get_dynamic_clothes(trip))

        self.assertEqual(items.get(CATEGORIES[1], 0), 7)  # Capped at 7 tops
        self.assertEqual(
            items.get(CATEGORIES[3], 0), 4
        )  # Capped at 4 pants (ceil(7/2))
        self.assertEqual(items.get(CATEGORIES[4], 0), 2)  # 2 pairs of shoes

    def test_get_dynamic_clothes_warm_with_work(self):
        """Test a warm trip that includes work (should have 1 pant, rest shorts)."""
        # 6 days total = 3 bottoms. Since it's warm + work -> 1 pant, 2 shorts.
        trip = self._create_trip(days=6, lowest_temp=22.0, activities=[Activity.work])
        items = self._count_items(get_dynamic_clothes(trip))

        self.assertEqual(items.get(CATEGORIES[3], 0), 1)  # 1 pair of pants
        self.assertEqual(items.get(CATEGORIES[2], 0), 2)  # 2 pairs of shorts

    def test_get_dynamic_clothes_warm_with_formal(self):
        """Test a warm trip that includes formal (should have 1 pant, rest shorts)."""
        # 3 days total = 2 bottoms (ceil(3/2)). Warm + formal -> 1 pant, 1 short.
        trip = self._create_trip(days=3, lowest_temp=22.0, activities=[Activity.formal])
        items = self._count_items(get_dynamic_clothes(trip))

        self.assertEqual(items.get(CATEGORIES[3], 0), 1)  # 1 pair of pants
        self.assertEqual(items.get(CATEGORIES[2], 0), 1)  # 1 pair of shorts

    # --- CONDITIONAL ITEMS TESTS ---

    def test_get_conditional_items_work(self):
        """Rule: Electronics (ID 6) should appear if Activity.work is in activities."""
        trip = self._create_trip(activities=[Activity.work], lowest_temp=5.0)
        items = [i.item_name for i in get_conditional_items(trip)]
        self.assertIn(CATEGORIES[6], items)

    def test_get_conditional_items_weather_cold(self):
        """Rule: Jackets (ID 7) should appear if low_temp < 0."""
        trip = self._create_trip(lowest_temp=-5.0)
        items = [i.item_name for i in get_conditional_items(trip)]
        self.assertIn(CATEGORIES[7], items)

    def test_get_conditional_items_water_activities(self):
        """Rule: Swimsuit (8) and Flip flops (12) for beach, swimming, or surfing."""
        water_activities = [Activity.beach, Activity.swimming, Activity.surfing]

        for activity in water_activities:
            with self.subTest(activity=activity):
                trip = self._create_trip(activities=[activity], lowest_temp=25.0)
                items = [i.item_name for i in get_conditional_items(trip)]
                self.assertIn(CATEGORIES[8], items)
                self.assertIn(CATEGORIES[12], items)  # Changed ID from 13 to 12

    def test_get_conditional_items_skiing(self):
        """Rule: Snow pants (9) and Skis (10) for skiing."""
        trip = self._create_trip(activities=[Activity.skiing], lowest_temp=-5.0)
        items = [i.item_name for i in get_conditional_items(trip)]
        self.assertIn(CATEGORIES[9], items)  # Snow pants
        self.assertIn(CATEGORIES[10], items)  # Skis
        self.assertNotIn(CATEGORIES[11], items)  # No snowboard

    def test_get_conditional_items_snowboarding(self):
        """Rule: Snow pants (9) and Snowboard (11) for snowboarding."""
        trip = self._create_trip(activities=[Activity.snowboarding], lowest_temp=-5.0)
        items = [i.item_name for i in get_conditional_items(trip)]
        self.assertIn(CATEGORIES[9], items)  # Snow pants
        self.assertIn(CATEGORIES[11], items)  # Snowboard
        self.assertNotIn(CATEGORIES[10], items)  # No skis

    def test_get_conditional_items_umbrella_rain(self):
        """Rule: Umbrella (13) for high precipitation and > 0 lowest temps."""
        trip = self._create_trip(lowest_temp=5.0, precipitation_percentage=0.6)
        items = [i.item_name for i in get_conditional_items(trip)]
        self.assertIn(CATEGORIES[13], items)  # Changed ID from 14 to 13

    def test_get_conditional_items_umbrella_snow(self):
        """Rule: No umbrella (13) if precipitation is high but temps are below freezing."""
        trip = self._create_trip(lowest_temp=-5.0, precipitation_percentage=0.8)
        items = [i.item_name for i in get_conditional_items(trip)]
        self.assertNotIn(CATEGORIES[13], items)  # Changed ID from 14 to 13

    # --- INTEGRATION & BOUNDARY TESTS ---

    def test_baseline_list_algorithm_integration(self):
        """Full integration: 5-day hot trip + Work + Swimming + Rain."""
        trip = self._create_trip(
            days=5,
            activities=[Activity.work, Activity.swimming],
            lowest_temp=20.0,
            precipitation_percentage=0.9,
            doing_laundry=False,
        )

        results = baseline_list_algorithm(trip)
        items = self._count_items(results)

        # Dynamic expectations (5 days, >18 lowest temp, work activity):
        self.assertEqual(items.get(CATEGORIES[1], 0), 5)  # 5 tops
        self.assertEqual(items.get(CATEGORIES[3], 0), 1)  # 1 pants (for work)
        self.assertEqual(items.get(CATEGORIES[2], 0), 2)  # 2 shorts (remaining bottoms)
        self.assertEqual(items.get(CATEGORIES[4], 0), 2)  # 2 shoes (>4 days)
        self.assertEqual(items.get(CATEGORIES[5], 0), 1)  # 1 toiletries

        # Conditional expectations:
        self.assertEqual(items.get(CATEGORIES[6], 0), 1)  # 1 Electronics (Work)
        self.assertEqual(items.get(CATEGORIES[8], 0), 1)  # 1 Swimsuit
        self.assertEqual(items.get(CATEGORIES[12], 0), 1)  # 1 Flip Flops
        self.assertEqual(items.get(CATEGORIES[13], 0), 1)  # 1 Umbrella (Rain)

    def test_boundary_conditions(self):
        """Test the exact cutoffs for temperatures and precipitation."""
        # 0.0 lowest temp: Neither jacket (<0) nor umbrella (>0)
        trip_zero_low = self._create_trip(lowest_temp=0.0, precipitation_percentage=0.6)
        items_zero_low = [i.item_name for i in get_conditional_items(trip_zero_low)]
        self.assertNotIn(CATEGORIES[7], items_zero_low)
        self.assertNotIn(CATEGORIES[13], items_zero_low)

        # 18.0 lowest temp: Exactly 18 should not trigger shorts (>18)
        trip_18_low = self._create_trip(days=4, lowest_temp=18.0)
        items_18_low = self._count_items(get_dynamic_clothes(trip_18_low))
        self.assertEqual(items_18_low.get(CATEGORIES[2], 0), 0)  # No shorts
        self.assertTrue(items_18_low.get(CATEGORIES[3], 0) > 0)  # Expect pants

        # 0.5 precipitation: Exactly 0.5 should not trigger umbrella (>0.5)
        trip_precip = self._create_trip(lowest_temp=15.0, precipitation_percentage=0.5)
        items_precip = [i.item_name for i in get_conditional_items(trip_precip)]
        self.assertNotIn(CATEGORIES[13], items_precip)


if __name__ == "__main__":
    unittest.main()
