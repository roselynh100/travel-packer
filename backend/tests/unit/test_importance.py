import os
import sys
from pathlib import Path

import joblib
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from app.models import (
    Activity,
    BoundingBox,
    CVResult,
    Destination,
    Dimensions,
    Item,
    Trip,
)
from machine_learning.importance import get_item_importance

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
MODEL_PATH = os.path.join(
    BASE_DIR, "machine_learning/importance_model", "importance_model.joblib"
)


def create_mock_item(name: str) -> Item:
    """Helper to create a valid Pydantic Item object."""
    return Item(
        cv_result=CVResult(
            item_name=name,
            class_name="object",
            confidence_score=0.99,
            bounding_boxes=[BoundingBox(x_min=0, y_min=0, x_max=1, y_max=1)],
            dimensions=Dimensions(length=10, width=10, height=10),
        )
    )


def create_mock_destination(city: str, country: str) -> Destination:
    return Destination(city=city, country=country)


def run_tests():
    if not os.path.exists(MODEL_PATH):
        print(f"FATAL: Model not found at {MODEL_PATH}. Check your file structure!")
        return

    print(f"\n{'ITEM SCANNED':<15} | {'TRIP':<20} | {'WORK':<8} | {'SCORE'}")
    print("-" * 75)

    # mock items
    new_top = create_mock_item("tops")
    existing_tops_in_suitcase = [create_mock_item("tops") for _ in range(4)]
    mock_laptop = create_mock_item("electronics")
    mock_jacket = create_mock_item("jacket")

    # mock destinations
    mock_bali = create_mock_destination("Bali", "Indonesia")
    mock_nyc = create_mock_destination("New York City", "USA")
    mock_banff = create_mock_destination("Banff", "Canada")

    beach_trip = Trip(
        destination="Bali",
        destination_details=mock_bali,
        duration_days=10,
        start_date="2026-02-14",
        end_date="2026-02-21",
        doing_laundry=True,
        activities=[Activity.beach, Activity.swimming],
        lowest_temp=28.0,
        highest_temp=35.0,
        items=[item.item_id for item in existing_tops_in_suitcase],  # <--- IDs ONLY
    )

    laptop = create_mock_item("electronics")
    biz_trip = Trip(
        destination="NYC",
        destination_details=mock_nyc,
        duration_days=3,
        start_date="2026-02-14",
        end_date="2026-02-21",
        doing_laundry=False,
        activities=[Activity.work],
        lowest_temp=15.0,
        highest_temp=22.0,
        items=[mock_laptop.item_id],
    )

    jacket = create_mock_item("jacket")
    ski_trip = Trip(
        destination="Banff",
        destination_details=mock_banff,
        duration_days=3,
        start_date="2026-02-14",
        end_date="2026-02-21",
        doing_laundry=True,
        activities=[Activity.skiing, Activity.skating, Activity.formal],
        lowest_temp=-15.0,
        highest_temp=-10.0,
        items=[],
    )

    test_cases = [
        (new_top, beach_trip, existing_tops_in_suitcase, "Beach Vacation"),
        (laptop, biz_trip, [], "Business Trip"),
        (jacket, ski_trip, [mock_jacket], "Ski Trip"),
        (laptop, ski_trip, [], "Ski Trip"),
        (new_top, ski_trip, [], "Ski Trip"),
    ]

    for item, trip, item_list, context in test_cases:
        try:
            # We pass the real objects (item_list) directly to the function
            score = get_item_importance(item, trip, item_list)

            work = "Yes" if Activity.work in trip.activities else "No"

            print(
                f"{item.cv_result.item_name:<15} | {context:<20} | {work:<8} | {score}"
            )
        except Exception as e:
            print(f"Error testing {item.cv_result.item_name}: {str(e)}")


if __name__ == "__main__":
    run_tests()
