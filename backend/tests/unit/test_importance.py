import os
import sys
from pathlib import Path

import joblib
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from app.models import (
    Activity,
    Airline,
    BagType,
    BoundingBox,
    CVResult,
    Dimensions,
    Item,
    Location,
    Trip,
)
from machine_learning.importance import get_item_importance

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
MODEL_PATH = os.path.join(
    BASE_DIR, "machine_learning/importance_model", "importance_model.joblib"
)


def create_mock_item(
    name: str, item_origin_price: float, item_dest_price: float
) -> Item:
    """Helper to create a valid Pydantic Item object."""
    return Item(
        cv_result=CVResult(
            item_name=name,
            confidence_score=0.99,
            bounding_boxes=[BoundingBox(x_min=0, y_min=0, x_max=1, y_max=1)],
            dimensions=Dimensions(length=10, width=10, height=10),
        ),
        price_at_origin=item_origin_price,
        price_at_destination=item_dest_price,
    )


def create_mock_destination(city: str, country: str) -> Location:
    airport_codes = {
        "Bali": "DPS",
        "New York City": "JFK",
        "Banff": "YYC",
    }
    return Location(
        city=city, country=country, airport_code=airport_codes.get(city, "AAA")
    )


def run_tests():
    if not os.path.exists(MODEL_PATH):
        print(f"FATAL: Model not found at {MODEL_PATH}. Check your file structure!")
        return

    print(
        f"\n{'ITEM SCANNED':<15} | {'TEST CONTEXT':<28} | {'EXPECTED SCORE':<25} | {'ACTUAL SCORE'}"
    )
    print("-" * 90)

    # 1. Mock Items
    new_top_cheaper_dest = create_mock_item("tops", 20, 10)  # price_less_at_dest = 1
    new_top_expensive_dest = create_mock_item("tops", 10, 50)  # price_less_at_dest = 0
    existing_tops_in_suitcase = [create_mock_item("tops", 10, 15) for _ in range(4)]

    mock_laptop = create_mock_item("electronics", 500, 400)
    mock_jacket = create_mock_item("jackets", 600, 100)
    unknown_item = create_mock_item("plumbus", 100, 100)

    # 2. Mock Destinations
    mock_bali = create_mock_destination("Bali", "Indonesia")
    mock_nyc = create_mock_destination("New York City", "USA")
    mock_banff = create_mock_destination("Banff", "Canada")

    # 3. Mock Trips
    beach_trip = Trip(
        destination="Bali",
        origin_details=mock_nyc,
        destination_details=mock_bali,
        duration_days=10,
        start_date="2026-02-14",
        end_date="2026-02-21",
        bag_type=BagType.checked,
        airline=Airline.air_canada,
        doing_laundry=True,
        activities=[Activity.beach, Activity.swimming],
        lowest_temp=28.0,
        highest_temp=35.0,
        precipitation_percentage=0.2,
        items=[item.item_id for item in existing_tops_in_suitcase],
    )

    biz_trip = Trip(
        destination="NYC",
        origin_details=mock_bali,
        destination_details=mock_nyc,
        duration_days=3,
        start_date="2026-02-14",
        end_date="2026-02-21",
        bag_type=BagType.checked,
        airline=Airline.air_canada,
        doing_laundry=False,
        activities=[Activity.work],
        lowest_temp=15.0,
        highest_temp=22.0,
        precipitation_percentage=0.5,
        items=[mock_laptop.item_id],
    )

    ski_trip = Trip(
        destination="Banff",
        origin_details=mock_nyc,
        destination_details=mock_banff,
        duration_days=3,
        start_date="2026-02-14",
        end_date="2026-02-21",
        bag_type=BagType.checked,
        airline=Airline.air_canada,
        doing_laundry=True,
        activities=[Activity.skiing, Activity.skating, Activity.formal],
        lowest_temp=-15.0,
        highest_temp=-10.0,
        precipitation_percentage=0.8,
        items=[],
    )

    # 4. Comprehensive Test Cases Mapping
    test_cases = [
        # Explicit Rule Tests
        (mock_laptop, biz_trip, [], "Work Laptop (1st)", 100),
        (
            mock_laptop,
            biz_trip,
            [mock_laptop],
            "Work Laptop (2nd)",
            "ML - Lower than 1st",
        ),
        (mock_laptop, beach_trip, [], "Beach Laptop", 5),
        (mock_jacket, ski_trip, [], "Ski Jacket (1st)", 100),
        (
            mock_jacket,
            ski_trip,
            [mock_jacket],
            "Ski Jacket (2nd)",
            "ML - Lower than 1st",
        ),
        (mock_jacket, beach_trip, [], "Beach Jacket", "ML - Very Low"),
        # General ML Feature Tests
        (
            new_top_cheaper_dest,
            beach_trip,
            existing_tops_in_suitcase,
            "High Cat Count",
            "ML - Low",
        ),
        (unknown_item, beach_trip, [], "Unknown Item (Cat 0)", 0),
        (new_top_expensive_dest, ski_trip, [], "Expensive at Dest", "ML - Any"),
        (
            new_top_cheaper_dest,
            ski_trip,
            [],
            "Cheaper at Dest",
            "ML - Lower than above",
        ),
    ]

    for item, trip, item_list, context, expected in test_cases:
        try:
            score = get_item_importance(item, trip, item_list)
            # work = "Yes" if Activity.work in trip.activities else "No"
            print(
                f"{item.cv_result.item_name:<15} | {context:<28} | {expected:<25} | {score}"
            )
        except Exception as e:
            print(f"Error testing {item.cv_result.item_name}: {str(e)}")


if __name__ == "__main__":
    run_tests()
