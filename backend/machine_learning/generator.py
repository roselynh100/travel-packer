from typing import List, Optional

from app.models import Activity, RecommendedItem, Trip

CATEGORIES = {
    0: "unknown",
    1: "tops",
    2: "shorts",
    3: "pants",
    4: "shoes",
    5: "toiletries",
    6: "electronics",
    7: "jackets",
}


def get_base_items() -> List[RecommendedItem]:
    """Returns items that are always required."""
    base_ids = [1, 3, 4, 5]
    return [RecommendedItem(item_name=CATEGORIES[i], priority=1) for i in base_ids]


def get_conditional_items(
    activities: List[Activity], low_temp: Optional[float]
) -> List[RecommendedItem]:
    items = []

    # If work is in activities, pack electronics
    if Activity.work in (activities or []):
        items.append(
            RecommendedItem(
                item_name=CATEGORIES[6], reason="Work requirements", priority=2
            )
        )

    # If lowest temp is less than 0, pack jacket
    if low_temp is not None and low_temp < 0:
        items.append(
            RecommendedItem(
                item_name=CATEGORIES[7],
                reason="Below freezing temperatures",
                priority=1,
            )
        )

    # If lowest temp is greater than 10, pack shorts
    if low_temp is not None and low_temp > 10:
        items.append(
            RecommendedItem(
                item_name=CATEGORIES[2], reason="Warm temperatures", priority=1
            )
        )

    return items


def baseline_list_algorithm(trip: Trip) -> List[RecommendedItem]:
    """Primary entry point to generate the packing list."""
    recs = []

    # 1. Add the "always-pack" items
    recs.extend(get_base_items())

    # 2. Add items based on specific rules
    recs.extend(get_conditional_items(trip.activities, trip.lowest_temp))

    return recs
