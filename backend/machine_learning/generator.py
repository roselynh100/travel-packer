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
    8: "swimsuit",
    9: "snow pants",
    10: "skis",
    11: "snowboard",
    12: "tent",
    13: "flip flops",
    14: "umbrella",
}


def get_base_items() -> List[RecommendedItem]:
    """Returns items that are always required."""
    base_ids = [1, 3, 4, 5]
    return [RecommendedItem(item_name=CATEGORIES[i], priority=1) for i in base_ids]


def get_conditional_items(trip: Trip) -> List[RecommendedItem]:
    items = []

    # If work is in activities, pack electronics
    if Activity.work in (trip.activities or []):
        items.append(
            RecommendedItem(
                item_name=CATEGORIES[6], reason="Work requirements", priority=2
            )
        )

    # If lowest temp is less than 0, pack jacket
    if trip.lowest_temp is not None and trip.lowest_temp < 0:
        items.append(
            RecommendedItem(
                item_name=CATEGORIES[7],
                reason="Below freezing temperatures",
                priority=1,
            )
        )

    # If lowest temp is greater than 10, pack shorts
    if trip.lowest_temp is not None and trip.lowest_temp > 10:
        items.append(
            RecommendedItem(
                item_name=CATEGORIES[2], reason="Warm temperatures", priority=1
            )
        )

    # If swimming, add swimming attire
    if (
        Activity.beach in (trip.activities or [])
        or Activity.swimming in (trip.activities or [])
        or Activity.surfing in (trip.activities or [])
    ):
        items.extend(
            [
                RecommendedItem(
                    item_name=CATEGORIES[8], reason="Swimming attire", priority=1
                ),
                RecommendedItem(
                    item_name=CATEGORIES[13], reason="Swimming attire", priority=1
                ),
            ]
        )

    # Ski and snowboarding rules
    if Activity.skiing in (trip.activities or []) or Activity.snowboarding in (
        trip.activities or []
    ):
        items.append(
            RecommendedItem(item_name=CATEGORIES[9], reason="Skiing attire", priority=1)
        )

    if Activity.skiing in (trip.activities or []):
        items.append(
            RecommendedItem(
                item_name=CATEGORIES[10], reason="Ski equipment", priority=1
            )
        )

    if Activity.snowboarding in (trip.activities or []):
        items.append(
            RecommendedItem(
                item_name=CATEGORIES[11], reason="Snowboarding equipment", priority=1
            )
        )

    # Tent for camping
    if Activity.camping in (trip.activities or []):
        items.append(
            RecommendedItem(
                item_name=CATEGORIES[12], reason="Camping equipment", priority=1
            )
        )

    # Pack umbrella if high precipitation & it's not snow
    if trip.precipitation_percentage > 0.5 and trip.lowest_temp > 0:
        items.append(
            RecommendedItem(
                item_name=CATEGORIES[14], reason="Needed for rain", priority=1
            )
        )

    return items


def baseline_list_algorithm(trip: Trip) -> List[RecommendedItem]:
    """Primary entry point to generate the packing list."""
    recs = []

    # 1. Add the "always-pack" items
    recs.extend(get_base_items())

    # 2. Add items based on specific rules
    recs.extend(get_conditional_items(trip))

    return recs
