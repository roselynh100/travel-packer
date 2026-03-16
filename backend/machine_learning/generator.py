import math
from typing import List

from app.models import Activity, RecommendedItem, Trip
from machine_learning.helpers import gt, lt

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
    12: "flip flops",
    13: "umbrella",
}


def get_dynamic_clothes(trip: Trip) -> List[RecommendedItem]:
    """Calculates individual everyday wear items based on duration, laundry, and weather."""
    items = []

    # 1. Calculate effective days (The "Laundry Cap")
    # If doing laundry, pack for a maximum of 7 days.
    eff_days = min(trip.duration_days, 7) if trip.doing_laundry else trip.duration_days

    # 2. Add Tops (1 per day)
    tops_qty = max(1, eff_days)
    items.extend(
        [RecommendedItem(item_name=CATEGORIES[1], priority=1) for _ in range(tops_qty)]
    )

    # 3. Add Bottoms (1 for every 2 days)
    total_bottoms = max(1, math.ceil(eff_days / 2))

    # Check for specific activities and weather
    requires_pants = Activity.work in (trip.activities or []) or Activity.formal in (
        trip.activities or []
    )
    is_warm = trip.lowest_temp is not None and gt(trip.lowest_temp, 18)

    if is_warm:
        if requires_pants:
            # Pack 1 pair of pants for the activity, the rest are shorts
            items.append(
                RecommendedItem(
                    item_name=CATEGORIES[3],
                    reason="Needed for work or formal events",
                    priority=1,
                )
            )
            remaining_bottoms = total_bottoms - 1
            if remaining_bottoms > 0:
                items.extend(
                    [
                        RecommendedItem(
                            item_name=CATEGORIES[2],
                            reason="Warm daytime temperatures",
                            priority=1,
                        )
                        for _ in range(remaining_bottoms)
                    ]
                )
        else:
            # No formal/work requirements, pack all shorts
            items.extend(
                [
                    RecommendedItem(
                        item_name=CATEGORIES[2], reason="Warm temperatures", priority=1
                    )
                    for _ in range(total_bottoms)
                ]
            )
    else:
        # It's cool, or we don't know the temp. Pack all pants (covers work/formal naturally)
        items.extend(
            [
                RecommendedItem(
                    item_name=CATEGORIES[3],
                    reason="Cooler temperatures or formal/work requirements",
                    priority=1,
                )
                for _ in range(total_bottoms)
            ]
        )

    # 4. Add Shoes (1 pair base, 2 pairs if trip > 4 days)
    shoes_qty = 2 if eff_days > 4 else 1
    items.extend(
        [RecommendedItem(item_name=CATEGORIES[4], priority=1) for _ in range(shoes_qty)]
    )

    # 5. Toiletries (Always 1)
    items.append(RecommendedItem(item_name=CATEGORIES[5], priority=1))

    return items


def get_conditional_items(trip: Trip) -> List[RecommendedItem]:
    """Calculates special items based on activities and weather conditions."""
    items = []

    if Activity.work in (trip.activities or []):
        items.append(
            RecommendedItem(
                item_name=CATEGORIES[6], reason="Work requirements", priority=2
            )
        )

    if trip.lowest_temp is not None and lt(trip.lowest_temp, 0):
        items.append(
            RecommendedItem(
                item_name=CATEGORIES[7],
                reason="Below freezing temperatures",
                priority=1,
            )
        )

    if any(
        act in (trip.activities or [])
        for act in [Activity.beach, Activity.swimming, Activity.surfing]
    ):
        items.extend(
            [
                RecommendedItem(
                    item_name=CATEGORIES[8], reason="Swimming attire", priority=1
                ),
                RecommendedItem(
                    item_name=CATEGORIES[12], reason="Beach footwear", priority=1
                ),
            ]
        )

    if Activity.skiing in (trip.activities or []) or Activity.snowboarding in (
        trip.activities or []
    ):
        items.append(
            RecommendedItem(
                item_name=CATEGORIES[9], reason="Snow sports attire", priority=1
            )
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

    if trip.precipitation_percentage is not None and trip.lowest_temp is not None:
        if gt(trip.precipitation_percentage, 0.5) and gt(trip.lowest_temp, 0):
            items.append(
                RecommendedItem(
                    item_name=CATEGORIES[13], reason="Needed for rain", priority=1
                )
            )

    return items


def baseline_list_algorithm(trip: Trip) -> List[RecommendedItem]:
    """Primary entry point to generate the packing list."""
    recs = []

    # 1. Add the dynamic everyday items
    recs.extend(get_dynamic_clothes(trip))

    # 2. Add items based on specific rules
    recs.extend(get_conditional_items(trip))

    return recs
