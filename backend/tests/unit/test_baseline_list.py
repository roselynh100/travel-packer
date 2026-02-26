import datetime
import sys
import unittest
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.models import Activity, Airline, BagType, Destination, RecommendedItem, Trip
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

    def _create_trip(
        self, activities=None, lowest_temp=None, precipitation_percentage=0.0
    ):
        """Helper method to generate a Trip object for testing."""
        return Trip(
            destination="Test City",
            destination_details=self.default_dest,
            duration_days=4,
            start_date=self.start_date,
            end_date=self.end_date,
            doing_laundry=False,
            bag_type=BagType.carry_on,
            airline=Airline.air_canada,
            activities=activities or [],
            lowest_temp=lowest_temp,
            precipitation_percentage=precipitation_percentage,
        )

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
        trip = self._create_trip(activities=[Activity.work], lowest_temp=5.0)
        items = get_conditional_items(trip)
        item_names = [i.item_name for i in items]
        self.assertIn(CATEGORIES[6], item_names)

    def test_get_conditional_items_weather_cold(self):
        """Rule: Jackets (ID 7) should appear if low_temp < 0."""
        trip = self._create_trip(lowest_temp=-5.0)
        items = get_conditional_items(trip)
        item_names = [i.item_name for i in items]
        self.assertIn(CATEGORIES[7], item_names)
        self.assertNotIn(CATEGORIES[2], item_names)  # No shorts in the cold

    def test_get_conditional_items_weather_warm(self):
        """Rule: Shorts (ID 2) should appear if low_temp > 10."""
        trip = self._create_trip(lowest_temp=15.0)
        items = get_conditional_items(trip)
        item_names = [i.item_name for i in items]
        self.assertIn(CATEGORIES[2], item_names)
        self.assertNotIn(CATEGORIES[7], item_names)  # No jackets in the heat

    def test_get_conditional_items_water_activities(self):
        """Rule: Swimsuit (8) and Flip flops (13) for beach, swimming, or surfing."""
        water_activities = [Activity.beach, Activity.swimming, Activity.surfing]

        for activity in water_activities:
            with self.subTest(activity=activity):
                trip = self._create_trip(activities=[activity], lowest_temp=25.0)
                items = get_conditional_items(trip)
                item_names = [i.item_name for i in items]
                self.assertIn(CATEGORIES[8], item_names)
                self.assertIn(CATEGORIES[13], item_names)

    def test_get_conditional_items_skiing(self):
        """Rule: Snow pants (9) and Skis (10) for skiing."""
        trip = self._create_trip(activities=[Activity.skiing], lowest_temp=-5.0)
        items = get_conditional_items(trip)
        item_names = [i.item_name for i in items]
        self.assertIn(CATEGORIES[9], item_names)  # Snow pants
        self.assertIn(CATEGORIES[10], item_names)  # Skis
        self.assertNotIn(CATEGORIES[11], item_names)  # No snowboard

    def test_get_conditional_items_snowboarding(self):
        """Rule: Snow pants (9) and Snowboard (11) for snowboarding."""
        trip = self._create_trip(activities=[Activity.snowboarding], lowest_temp=-5.0)
        items = get_conditional_items(trip)
        item_names = [i.item_name for i in items]
        self.assertIn(CATEGORIES[9], item_names)  # Snow pants
        self.assertIn(CATEGORIES[11], item_names)  # Snowboard
        self.assertNotIn(CATEGORIES[10], item_names)  # No skis

    def test_get_conditional_items_camping(self):
        """Rule: Tent (12) for camping."""
        trip = self._create_trip(activities=[Activity.camping], lowest_temp=15.0)
        items = get_conditional_items(trip)
        item_names = [i.item_name for i in items]
        self.assertIn(CATEGORIES[12], item_names)

    def test_get_conditional_items_umbrella_rain(self):
        """Rule: Umbrella (14) for high precipitation and > 0 temps."""
        trip = self._create_trip(lowest_temp=5.0, precipitation_percentage=0.6)
        items = get_conditional_items(trip)
        item_names = [i.item_name for i in items]
        self.assertIn(CATEGORIES[14], item_names)

    def test_get_conditional_items_umbrella_snow(self):
        """Rule: No umbrella (14) if precipitation is high but temps are below freezing (snowing)."""
        trip = self._create_trip(lowest_temp=-5.0, precipitation_percentage=0.8)
        items = get_conditional_items(trip)
        item_names = [i.item_name for i in items]
        self.assertNotIn(CATEGORIES[14], item_names)

    def test_baseline_list_algorithm_integration(self):
        """Full integration: Base (4) + Work (1) + Warm (1) + Swimming (2) + Umbrella (1) = 9 total."""
        trip = Trip(
            destination="Miami",
            destination_details=self.default_dest,
            duration_days=4,
            start_date=self.start_date,
            end_date=self.end_date,
            doing_laundry=False,
            bag_type=BagType.carry_on,
            airline=Airline.air_canada,
            activities=[Activity.work, Activity.swimming],
            lowest_temp=25.0,
            low_temp=25.0,
            precipitation_percentage=0.9,  # Added to trigger umbrella
        )

        results = baseline_list_algorithm(trip)
        item_names = [i.item_name for i in results]

        # 4 Base + 1 Electronics + 1 Shorts + 1 Swimsuit + 1 Flip Flops + 1 Umbrella = 9
        self.assertEqual(len(results), 9)
        self.assertIn(CATEGORIES[6], item_names)  # Electronics
        self.assertIn(CATEGORIES[2], item_names)  # Shorts
        self.assertIn(CATEGORIES[8], item_names)  # Swimsuit
        self.assertIn(CATEGORIES[13], item_names)  # Flip flops
        self.assertIn(CATEGORIES[14], item_names)  # Umbrella

    def test_boundary_conditions(self):
        """Test the exact cutoffs for temperatures and precipitation."""
        # 0.0 degrees: Neither jacket (<0) nor shorts (>10) nor umbrella (>0)
        trip_zero = self._create_trip(lowest_temp=0.0, precipitation_percentage=0.6)
        items_zero = get_conditional_items(trip_zero)
        self.assertEqual(len(items_zero), 0)

        # 10.0 degrees: Exactly 10 should not trigger shorts (>10)
        trip_ten = self._create_trip(lowest_temp=10.0, precipitation_percentage=0.0)
        items_ten = get_conditional_items(trip_ten)
        self.assertEqual(len(items_ten), 0)

        # 0.5 precipitation: Exactly 0.5 should not trigger umbrella (>0.5)
        trip_precip = self._create_trip(lowest_temp=15.0, precipitation_percentage=0.5)
        items_precip = get_conditional_items(trip_precip)
        item_names = [i.item_name for i in items_precip]
        self.assertNotIn(CATEGORIES[14], item_names)  # No umbrella


if __name__ == "__main__":
    unittest.main()
