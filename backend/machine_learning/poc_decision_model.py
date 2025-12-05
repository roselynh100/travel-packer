from typing import List, Optional

from app.models import (
    Item,
    RecommendedItem,
    RemovalRecommendation,
    RemovalRecommendationReason,
    RemovalRecommendationStatus,
    Trip,
)

from .item_groups import ACCESSORIES, CLOTHING, ESSENTIALS, TOILETRIES

# Hard coded limits for now TODO: figure out where to put these
WEIGHT_LIMIT_KG = 20.0
VOLUME_LIMIT_CM3 = 50000.0


def get_item_importance(item: Item, trip: Trip) -> int:
    """Generates item importance score."""
    name = "Unknown Item"
    if item.cv_result:
        name = item.cv_result.item_name

    score = 0
    if name in ["laptop", "laptop charger", "cell phone"]:
        score = 80
    elif name in ["toothbrush", "toothpaste"]:
        score = 90
    elif name in [
        "shirt",
        "pants",
        "socks",
        "shoes",
        "backpack",
        "handbag",
        "suitcase",
    ]:
        score = 95
    elif name == "coat":
        score = 70
    elif name == "umbrella":
        score = 35
    elif name == "sunglasses":
        score = 30
    elif name in ["snack", "bottle", "book"]:
        score = 20
    else:
        score = 0

    # Rules

    if (
        name in ["laptop", "laptop charger"]
        and "work" not in (trip.activities or "").lower()
    ):
        score = 0

    # Not sure how weather is going to work yet
    # if name == "Coat" and "hot" in (trip.weather or "").lower():
    #     score = 0

    item.item_importance = score
    return score


def packing_decision_algorithm(
    new_item: Item, trip: Trip, current_items: List[Item]
) -> RemovalRecommendation:
    """Returns packing status i.e. whether items must be removed."""

    # Calculate importance of new item
    get_item_importance(new_item, trip)
    # Find the minimum importance score of already packed items
    if not current_items:
        min_item_importance = 0
    else:
        for i in current_items:
            get_item_importance(i, trip)
        min_item_importance = min(i.item_importance for i in current_items)

    # Check Weight
    if new_item.weight_kg is not None and (
        trip.total_items_weight + new_item.weight_kg > WEIGHT_LIMIT_KG
    ):
        if new_item.item_importance > min_item_importance:

            # Order by importance ASC and add items to list until overflow is fixed
            weight_overflow = (
                trip.total_items_weight + new_item.weight_kg
            ) - WEIGHT_LIMIT_KG
            candidates = []
            weight_cleared = 0.0
            for i in sorted(current_items, key=lambda x: x.item_importance):
                candidates.append(i)
                weight_cleared += i.weight_kg

                # Stop as soon as we have cleared enough space
                if weight_cleared >= weight_overflow:
                    break

            return RemovalRecommendation(
                status=RemovalRecommendationStatus.swap,
                reason=RemovalRecommendationReason.overweight,
                swap_candidates=candidates,
            )
        else:
            return RemovalRecommendation(
                status=RemovalRecommendationStatus.remove,
                reason=RemovalRecommendationReason.overweight,
                swap_candidates=None,
            )

    # Check Volume
    if new_item.estimated_volume_cm3 is not None and (
        trip.total_items_volume + new_item.estimated_volume_cm3 > VOLUME_LIMIT_CM3
    ):
        if new_item.item_importance > min_item_importance:

            # Order by importance ASC and add items to list until overflow is fixed
            volume_overflow = (
                trip.total_items_volume + new_item.estimated_volume_cm3
            ) - VOLUME_LIMIT_CM3
            candidates = []
            volume_cleared = 0.0
            for i in sorted(current_items, key=lambda x: x.item_importance):
                candidates.append(i)
                volume_cleared += i.estimated_volume_cm3

                # Stop as soon as we have cleared enough space
                if volume_cleared >= volume_overflow:
                    break

            return RemovalRecommendation(
                status=RemovalRecommendationStatus.swap,
                reason=RemovalRecommendationReason.over_volume,
                swap_candidates=candidates,
            )
        else:
            return RemovalRecommendation(
                status=RemovalRecommendationStatus.remove,
                reason=RemovalRecommendationReason.over_volume,
                swap_candidates=None,
            )

    return RemovalRecommendation(
        status=RemovalRecommendationStatus.pack, reason=None, swap_candidates=None
    )


def get_base_items() -> List[RecommendedItem]:
    """Returns the static list of items needed for every trip."""
    return CLOTHING + ACCESSORIES + TOILETRIES + ESSENTIALS


def get_work_items(activities: Optional[str]) -> List[RecommendedItem]:
    """Returns items specific to work trips."""
    items = []
    if "work" in (activities or "").lower():
        items.append(
            RecommendedItem(item_name="laptop", reason="Needed for work", priority=1)
        )
        items.append(
            RecommendedItem(
                item_name="laptop charger", reason="Needed for work", priority=2
            )
        )
    return items


def get_weather_items(lowest_temp: Optional[float]) -> List[RecommendedItem]:
    """Returns items based on temperature logic."""
    items = []
    if lowest_temp is not None and lowest_temp < 10:
        items.append(
            RecommendedItem(
                item_name="coat", reason="Needed for cold weather", priority=1
            )
        )
    return items


def baseline_list_algorithm(trip: Trip) -> List[RecommendedItem]:
    """Returns a list of things that the user should pack based on trip details."""
    recs = []

    # Compose the final list using the helpers
    recs.extend(get_base_items())
    recs.extend(get_work_items(trip.activities))
    recs.extend(get_weather_items(trip.lowest_temp))

    return recs
