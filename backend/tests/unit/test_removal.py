import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.models import (
    Activity,
    Airline,
    BagType,
    BoundingBox,
    CVResult,
    Destination,
    Dimensions,
    Item,
    RemovalRecommendationReason,
    RemovalRecommendationStatus,
    Trip,
)
from machine_learning.importance import get_item_importance
from machine_learning.optimizer import packing_decision_algorithm


class TestPackingAlgorithm(unittest.TestCase):

    def create_dummy_item(
        self,
        name: str,
        weight: float = 0.5,
        volume: float = 100.0,
        origin_price: float = 10.0,
        dest_price: float = 10.0,
    ) -> Item:
        """Helper to create a complex Pydantic Item with valid CVResults and Pricing."""

        # Create valid BoundingBox
        bbox = BoundingBox(x_min=0.0, y_min=0.0, x_max=10.0, y_max=10.0)

        # Create valid Dimensions
        dims = Dimensions(length=10.0, width=10.0, height=1.0)

        # Create CVResult
        cv = CVResult(
            item_name=name,
            confidence_score=0.99,
            bounding_boxes=[bbox],
            dimensions=dims,
        )

        return Item(
            weight_kg=weight,
            estimated_volume_cm3=volume,
            cv_result=cv,
            price_at_origin=origin_price,
            price_at_destination=dest_price,
        )

    def test_laptop_context_logic(self):
        """Test that Laptop is 5 importance for leisure, 100 for work."""
        item = self.create_dummy_item("electronics")

        # Case 1: Leisure
        trip_leisure = Trip(
            destination="Beach",
            destination_details=Destination(city="Bali", country="Indonesia"),
            duration_days=3,
            start_date="2026-02-14",
            end_date="2026-02-21",
            bag_type=BagType.checked,
            airline=Airline.air_canada,
            doing_laundry=False,
            activities=[Activity.beach],
            lowest_temp=25.0,
            highest_temp=30.0,
            precipitation_percentage=0.1,
            items=[],  # <-- Added missing items list
        )
        self.assertEqual(get_item_importance(item, trip_leisure, []), 5)

        # Case 2: Work
        trip_work = Trip(
            destination="Conf",
            destination_details=Destination(city="Banff", country="Canada"),
            duration_days=3,
            start_date="2026-02-14",
            end_date="2026-02-21",
            bag_type=BagType.checked,
            airline=Airline.air_canada,
            doing_laundry=False,
            activities=[Activity.work],
            lowest_temp=-5.0,
            highest_temp=2.0,
            precipitation_percentage=0.5,
            items=[],  # <-- Added missing items list
        )
        self.assertEqual(get_item_importance(item, trip_work, []), 100)

    def test_pack_happy_path(self):
        """Test simple successful packing."""
        trip = Trip(
            destination="Paris",
            destination_details=Destination(city="Paris", country="France"),
            start_date="2026-02-14",
            end_date="2026-02-21",
            bag_type=BagType.checked,
            airline=Airline.air_canada,
            duration_days=5,
            doing_laundry=False,
            lowest_temp=10.0,
            highest_temp=18.0,
            precipitation_percentage=0.2,
            items=[],  # <-- Added missing items list
        )
        current_items = []
        new_item = self.create_dummy_item("socks", weight=0.1)

        result = packing_decision_algorithm(new_item, trip, current_items)

        self.assertEqual(result.status, RemovalRecommendationStatus.pack)

    def test_overweight_remove(self):
        """
        Trip is full (19.9kg).
        New Item is 'tops', Weight 0.5kg.
        Existing Item is 'jackets'.
        Expect: REMOVE (New item isn't important enough to displace existing).
        """
        # 2. Setup Existing High Value Item first so we can reference its ID
        existing_jacket = self.create_dummy_item("jackets", weight=0.1)
        current_items = [existing_jacket]

        # 1. Setup Trip nearing limit
        trip = Trip(
            destination="Space",
            destination_details=Destination(city="Banff", country="Canada"),
            start_date="2026-02-14",
            end_date="2026-02-21",
            bag_type=BagType.checked,
            airline=Airline.air_canada,
            duration_days=7,
            lowest_temp=-10.0,
            highest_temp=0.0,
            precipitation_percentage=0.1,
            doing_laundry=False,
            total_items_weight=19.9,
            items=[existing_jacket.item_id],  # <-- Linked existing item
        )

        # 3. Setup New Low Value Item
        new_item = self.create_dummy_item("tops", weight=0.5)

        # 4. Run
        result = packing_decision_algorithm(new_item, trip, current_items)

        self.assertEqual(result.status, RemovalRecommendationStatus.remove)
        self.assertEqual(result.reason, RemovalRecommendationReason.overweight)
        self.assertIsNone(result.swap_candidates)

    def test_overweight_swap(self):
        """
        Trip is full (19.5kg).
        Existing Item is 'Snack' (Importance 20), Weight 2.0kg.
        New Item is 'Laptop' (Importance 80 - Work), Weight 1.0kg.
        Expect: SWAP (Remove Snack to fit Laptop).
        """
        # Existing heavy, unimportant item
        tops = self.create_dummy_item("tops", weight=2.0)
        current_items = [tops]

        trip = Trip(
            destination="Office",
            destination_details=Destination(city="Banff", country="Canada"),
            start_date="2026-02-14",
            end_date="2026-02-21",
            bag_type=BagType.checked,
            airline=Airline.air_canada,
            duration_days=1,
            doing_laundry=False,
            activities=[Activity.work],
            lowest_temp=5.0,
            highest_temp=15.0,
            precipitation_percentage=0.0,
            total_items_weight=19.5,
            items=[tops.item_id],  # <-- Linked existing item
        )

        # New important item
        laptop = self.create_dummy_item("electronics", weight=1.0)
        get_item_importance(laptop, trip, current_items)

        result = packing_decision_algorithm(laptop, trip, current_items)

        self.assertEqual(result.status, RemovalRecommendationStatus.swap)
        self.assertEqual(result.reason, RemovalRecommendationReason.overweight)

        # Verify the tops is the candidate for removal
        self.assertIsNotNone(result.swap_candidates)
        self.assertEqual(len(result.swap_candidates), 1)
        self.assertEqual(result.swap_candidates[0].item_id, tops.item_id)

    def test_empty_list_edge_case(self):
        """Ensure algorithm handles the very first item (empty current_items)."""
        trip = Trip(
            destination="Void",
            duration_days=1,
            destination_details=Destination(city="Banff", country="Canada"),
            start_date="2026-02-14",
            end_date="2026-02-21",
            bag_type=BagType.checked,
            airline=Airline.air_canada,
            doing_laundry=False,
            lowest_temp=10.0,
            highest_temp=20.0,
            precipitation_percentage=0.0,
            items=[],  # <-- Added missing items list
        )
        current_items = []
        item = self.create_dummy_item("coat")

        try:
            result = packing_decision_algorithm(item, trip, current_items)
            self.assertEqual(result.status, RemovalRecommendationStatus.pack)
        except ValueError:
            self.fail("Algorithm crashed on empty list check!")


if __name__ == "__main__":
    unittest.main()
