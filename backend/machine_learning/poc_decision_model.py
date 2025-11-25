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

    score = 0
    if name in ["Laptop", "Laptop Charger"]:
        score = 80
    elif name in ["Toothbrush", "Toothpaste"]:
        score = 90
    elif name in ["Shirt", "Pants", "Socks", "Shoes"]:
        score = 95
    elif name == "Coat":
        score = 70
    elif name == "Umbrella":
        score = 35
    elif name == "Sunglasses":
        score = 30
    elif name == "Snack":
        score = 20
    else:
        score = 0

    # Rules

    if (
        name in ["Laptop", "Laptop Charger"]
        and "work" not in (trip.activities or "").lower()
    ):
        score = 0

    # Not sure how weather is going to work yet
    # if name == "Coat" and "hot" in (trip.weather or "").lower():
    #     score = 0

    item.item_importance = score
    return score


def removal_recommendation_algorithm(
    new_item: Item, trip: Trip, current_items: List[Item]
) -> RemovalRecommendation:
    """Returns packing status i.e. whether items must be removed."""
    # current_items would be something like:
    # current_items_objects = []
    #    for item_id in trip.items:
    #        if item_id in items_store:
    #            current_items_objects.append(items_store[item_id])
    # removal_recommendation_algorithm(new_item=new_item, trip=trip, current_items=current_items_objects)

    # Calculate importance of new item
    get_item_importance(new_item, trip)
    # Find the minimum importance score of already packed items
    if not current_items:
        min_item_importance = 0
    else:
        for i in current_items:
            get_item_importance(i, trip)
        min_item_importance = min(i.item_importance for i in current_items)

    # Hard coded limits for now TODO: figure out where to put these
    WEIGHT_LIMIT_KG = 20.0
    VOLUME_LIMIT_CM3 = 50000.0

    # Check Weight
    if trip.total_items_weight + new_item.weight_kg > WEIGHT_LIMIT_KG:
        if new_item.item_importance > min_item_importance:

            # Order by importance DESC and add items to list until overflow is fixed
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
    if trip.total_items_volume + new_item.estimated_volume_cm3 > VOLUME_LIMIT_CM3:
        if new_item.item_importance > min_item_importance:

            # Order by importance DESC and add items to list until overflow is fixed
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

    # Item is successfully packed:
    trip.total_items_weight += new_item.weight_kg
    trip.total_items_volume += new_item.estimated_volume_cm3

    trip.items.append(new_item.item_id)

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
