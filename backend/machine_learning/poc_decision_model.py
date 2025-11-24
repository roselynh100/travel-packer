from typing import List

from app.models import (
    Item,
    RecommendedItem,
    RemovalRecommendation,
    RemovalRecommendationReason,
    RemovalRecommendationStatus,
    Trip,
)


def get_item_importance(item: Item, trip: Trip) -> int:
    """Generates item importance score."""
    name = "Unknown Item"
    if item.cv_results and len(item.cv_results) > 0:
        name = item.cv_results[0].item_name

    if name in ["Laptop", "Laptop Charger"]:
        item.importance = 80
    elif name in ["Toothbrush", "Toothpaste"]:
        item.importance = 90
    elif name in ["Shirt", "Pants", "Socks", "Shoes"]:
        item.importance = 95
    elif name == "Coat":
        item.importance = 70
    elif name == "Umbrella":
        item.importance = 35
    elif name == "Sunglasses":
        item.importance = 30
    elif name == "Snack":
        item.importance = 20
    else:
        item.importance = 0

    # Rules

    if (
        name in ["Laptop", "Laptop Charger"]
        and "work" not in (trip.activities or "").lower()
    ):
        item.importance = 0

    # Not sure how weather is going to work yet
    # if name == "Coat" and "hot" in (trip.weather or "").lower():
    #     item.importance = 0

    return item.importance


def removal_recommendation_algorithm(item: Item, trip: Trip) -> RemovalRecommendation:
    """Returns packing status i.e. whether items must be removed."""

    get_item_importance(item)
    min_item_importance = min(get_item_importance(i) for i in trip.items)

    # Hard coded limits for now TODO: figure out where to put these
    WEIGHT_LIMIT_KG = 20.0
    VOLUME_LIMIT_CM3 = 50000.0

    # Check Weight
    if trip.total_items_weight + item.weight_kg > WEIGHT_LIMIT_KG:
        if item.importance > min_item_importance:

            # Order by importance DESC and add items to list until overflow is fixed
            weight_overflow = (
                trip.total_items_weight + item.weight_kg
            ) - WEIGHT_LIMIT_KG
            candidates = []
            weight_cleared = 0.0
            for i in sorted(trip.items, key=lambda x: x.importance):
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
    if trip.total_items_volume + item.estimated_volume_cm3 > VOLUME_LIMIT_CM3:
        if item.importance > min_item_importance:

            # Order by importance DESC and add items to list until overflow is fixed
            volume_overflow = (
                trip.total_items_volume + item.estimated_volume_cm3
            ) - VOLUME_LIMIT_CM3
            candidates = []
            volume_cleared = 0.0
            for i in sorted(trip.items, key=lambda x: x.importance):
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

    # Item is successfully packed:
    trip.total_items_weight += item.weight_kg
    trip.total_items_volume += item.estimated_volume_cm3

    return RemovalRecommendation(
        status=RemovalRecommendationStatus.pack, reason=None, swap_candidates=None
    )


def generate_recommendation_list(trip: Trip) -> List[RecommendedItem]:
    """Returns a list of things that the user should pack based on trip details"""
    # access trip info like this:
    activities = trip.activities

    # TO-DO: replace with our actual generate_recommendation_list algorithm once thats ready
    recs = [
        RecommendedItem(
            item_name="Passport", reason="Required for international travel", priority=1
        ),
        RecommendedItem(
            item_name="Phone Charger", reason="Daily essential", priority=2
        ),
    ]
    return recs
