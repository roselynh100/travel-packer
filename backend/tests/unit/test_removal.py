import sys
import unittest
from pathlib import Path

# Ensure the app module is visible
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.models import (
    BoundingBox,
    CVResult,
    Dimensions,
    Item,
    RemovalRecommendation,
    RemovalRecommendationReason,
    RemovalRecommendationStatus,
    Trip,
)

# Make sure this import path matches your actual file structure
from machine_learning.poc_decision_model import (
    get_item_importance,
    packing_decision_algorithm,
)


class TestPackingAlgorithm(unittest.TestCase):

    def create_dummy_item(
        self, name: str, weight: float = 0.5, volume: float = 100.0
    ) -> Item:
        """Helper to create a complex Pydantic Item with valid CVResults."""

        # Create valid BoundingBox
        bbox = BoundingBox(x_min=0.0, y_min=0.0, x_max=10.0, y_max=10.0)

        # Create valid Dimensions
        dims = Dimensions(length=10.0, width=10.0, height=1.0)

        # Create CVResult
        cv = CVResult(
            item_name=name,
            class_name="generic",
            confidence_score=0.99,
            bounding_boxes=[bbox],
            dimensions=dims,
        )

        # UPDATED: Use 'cv_result' (singular) to match your code's access pattern
        return Item(weight_kg=weight, estimated_volume_cm3=volume, cv_result=cv)

    def test_importance_scoring(self):
        """Test that item names map to the correct importance integers."""
        trip = Trip(destination="Test", duration_days=3, doing_laundry=False)

        item = self.create_dummy_item("toothbrush")
        score = get_item_importance(item, trip)
        self.assertEqual(score, 90)
        # The function modifies the item in place, so this check is valid
        self.assertEqual(item.item_importance, 90)

        item_snack = self.create_dummy_item("snack")
        self.assertEqual(get_item_importance(item_snack, trip), 20)

    def test_laptop_context_logic(self):
        """Test that Laptop is 0 importance for leisure, 80 for work."""
        item = self.create_dummy_item("laptop")

        # Case 1: Leisure
        trip_leisure = Trip(
            destination="Beach",
            duration_days=3,
            doing_laundry=False,
            activities="Relaxing",
        )
        self.assertEqual(get_item_importance(item, trip_leisure), 0)

        # Case 2: Work
        trip_work = Trip(
            destination="Conf",
            duration_days=3,
            doing_laundry=False,
            activities="Business Work",
        )
        self.assertEqual(get_item_importance(item, trip_work), 80)

    def test_pack_happy_path(self):
        """Test simple successful packing."""
        trip = Trip(destination="Paris", duration_days=5, doing_laundry=False)
        current_items = []
        new_item = self.create_dummy_item("socks", weight=0.1)

        result = packing_decision_algorithm(new_item, trip, current_items)

        # UPDATED: Only check the decision. The algorithm does NOT update the trip object.
        self.assertEqual(result.status, RemovalRecommendationStatus.pack)

    def test_overweight_remove(self):
        """
        Trip is full (19.9kg).
        New Item is 'Snack' (Importance 20), Weight 0.5kg.
        Existing Item is 'Toothbrush' (Importance 90).
        Expect: REMOVE (New item isn't important enough to displace existing).
        """
        # 1. Setup Trip nearing limit
        trip = Trip(
            destination="Space",
            duration_days=1,
            doing_laundry=False,
            total_items_weight=19.9,
        )

        # 2. Setup Existing High Value Item
        existing_item = self.create_dummy_item("toothbrush", weight=0.1)
        current_items = [existing_item]

        # 3. Setup New Low Value Item
        new_item = self.create_dummy_item("snack", weight=0.5)

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
        trip = Trip(
            destination="Office",
            duration_days=1,
            doing_laundry=False,
            activities="Work",
            total_items_weight=19.5,
        )

        # Existing heavy, unimportant item
        snack = self.create_dummy_item("snack", weight=2.0)
        current_items = [snack]

        # New important item
        laptop = self.create_dummy_item("laptop", weight=1.0)

        result = packing_decision_algorithm(laptop, trip, current_items)

        self.assertEqual(result.status, RemovalRecommendationStatus.swap)
        self.assertEqual(result.reason, RemovalRecommendationReason.overweight)

        # Verify the snack is the candidate for removal
        self.assertIsNotNone(result.swap_candidates)
        self.assertEqual(len(result.swap_candidates), 1)
        self.assertEqual(result.swap_candidates[0].item_id, snack.item_id)

    def test_empty_list_edge_case(self):
        """Ensure algorithm handles the very first item (empty current_items)."""
        trip = Trip(destination="Void", duration_days=1, doing_laundry=False)
        current_items = []
        item = self.create_dummy_item("coat")

        try:
            result = packing_decision_algorithm(item, trip, current_items)
            self.assertEqual(result.status, RemovalRecommendationStatus.pack)
        except ValueError:
            self.fail("Algorithm crashed on empty list check!")


if __name__ == "__main__":
    unittest.main()
