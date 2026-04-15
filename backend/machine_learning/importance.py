# Main function: get_item_importance()
# Returns: int 'score' with value 0 to 100

import os
from typing import List

import joblib
import numpy as np
import pandas as pd

from app.models import (
    Activity,
    Item,
    Trip,
)
from machine_learning.helpers import all_present, default

# Loading model in
base_path = os.path.dirname(__file__)
MODEL_PATH = os.path.join(base_path, "importance_model", "importance_model.joblib")

if os.path.exists(MODEL_PATH):
    model = joblib.load(MODEL_PATH)
else:
    model = None


def map_to_cat_id(item_name: str) -> int:
    """
    Maps raw item name to a numeric category ID.
    """
    name = item_name.lower()
    categories = {
        0: ["unknown"],
        1: ["tops"],
        2: ["shorts"],
        3: ["pants"],
        4: ["shoes"],
        5: ["toiletries"],
        6: ["electronics"],
        7: ["jackets"],
    }

    for cat_id, keywords in categories.items():
        if any(word in name for word in keywords):
            return cat_id
    return 0


def extract_features(item: Item, trip: Trip, trip_items: List[Item]) -> List[float]:
    """
    Transforms Pydantic models into a numeric feature vector for the ML model.
    """
    # Item Category
    item_category = map_to_cat_id(item.cv_result.item_name if item.cv_result else "")

    # Bring vs. Buy (use 0 when no price available)
    price_less_at_dest = (
        1
        if default(item.price_at_destination, 0) <= default(item.price_at_origin, 0)
        else 0
    )

    # Activity Binary Encoding
    is_work = 1 if Activity.work in trip.activities else 0
    is_beach = 1 if Activity.beach in trip.activities else 0
    is_swimming = 1 if Activity.swimming in trip.activities else 0
    is_surfing = 1 if Activity.surfing in trip.activities else 0
    is_camping = 1 if Activity.camping in trip.activities else 0
    is_hiking = 1 if Activity.hiking in trip.activities else 0
    is_skiing = 1 if Activity.skiing in trip.activities else 0
    is_snowboarding = 1 if Activity.snowboarding in trip.activities else 0
    is_skating = 1 if Activity.skating in trip.activities else 0
    is_formal = 1 if Activity.formal in trip.activities else 0
    is_laundry = 1 if trip.doing_laundry else 0

    # Weather
    temperature = (
        (trip.lowest_temp + trip.highest_temp) / 2
        if all_present(trip.lowest_temp, trip.highest_temp)
        else 20.0
    )
    precipitation = default(trip.precipitation_percentage, 0)

    duration = trip.duration_days

    # Duplicate/Quantity Logic
    # Counts how many items of the SAME category are already in the trip
    category_count = sum(
        1
        for existing_item in trip_items
        if map_to_cat_id(
            existing_item.cv_result.item_name if existing_item.cv_result else ""
        )
        == item_category
    )

    # Return features as binary encode
    return [
        float(item_category),
        float(is_work),
        float(is_beach),
        float(is_swimming),
        float(is_surfing),
        float(is_camping),
        float(is_hiking),
        float(is_skiing),
        float(is_snowboarding),
        float(is_skating),
        float(is_formal),
        float(is_laundry),
        float(temperature),
        float(precipitation),
        float(duration),
        float(category_count),
        float(price_less_at_dest),
    ]


def get_item_importance(item: Item, trip: Trip, trip_items: List[Item]) -> int:
    if model is None:
        return 0  # Fallback logic

    # Extraction for explicit rules
    item_category = map_to_cat_id(item.cv_result.item_name if item.cv_result else "")
    is_work = 1 if Activity.work in trip.activities else 0
    low_temp = default(trip.lowest_temp, 20.0)
    cat_count = (
        sum(
            1
            for i in trip_items
            if map_to_cat_id(i.cv_result.item_name if i.cv_result else "")
            == item_category
        )
        + 1
    )

    # Explicit rules with set item importance

    ## If item is unknown, set importance to 0
    if item_category == 0:
        return 0

    ## If item = electronics and work = 1 then importance = 100
    if item_category == 6 and is_work == 1:
        if cat_count == 1:
            return 100
        # If there's more than one, we continue to the ML model to decide the penalty
    if item_category == 6 and is_work == 0:
        return 5

    ## If item = jacket and temp < 0 then importance = 100
    if item_category == 7 and low_temp <= 0:
        if cat_count == 1:
            return 100
        # If there's more than one, we continue to the ML model to decide the penalty

    # Use ML model to determine importance score
    features = extract_features(item, trip, trip_items)
    feature_names = [
        "item_category",
        "is_work",
        "is_beach",
        "is_swimming",
        "is_surfing",
        "is_camping",
        "is_hiking",
        "is_skiing",
        "is_snowboarding",
        "is_skating",
        "is_formal",
        "is_laundry",
        "temperature",
        "precipitation",
        "duration",
        "category_count",
        "price_less_at_dest",
    ]

    features_df = pd.DataFrame([features], columns=feature_names)

    score = model.predict(features_df)[0]
    return int(np.clip(score, 0, 100))
