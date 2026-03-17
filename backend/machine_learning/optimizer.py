# Main function: packing_decision_algorithm()
# Returns: RemovalRecommendation object

from typing import List

from app.models import (
    BagType,
    Item,
    RemovalRecommendation,
    RemovalRecommendationReason,
    RemovalRecommendationStatus,
    Trip,
)
from machine_learning.helpers import over_limit
from machine_learning.importance import get_item_importance

VOLUME_LIMIT_CM3 = 75000.0


def packing_decision_algorithm(
    new_item: Item, trip: Trip, current_items: List[Item]
) -> RemovalRecommendation:
    """Returns packing status i.e. whether items must be removed."""

    # Calculate importance of new item
    new_item.item_importance = get_item_importance(new_item, trip, current_items)
    # Find the minimum importance score of already packed items
    if not current_items:
        min_item_importance = 0
    else:
        for i in current_items:
            i.item_importance = get_item_importance(
                i, trip, [item for item in current_items if item is not i]
            )
        min_item_importance = min(i.item_importance for i in current_items)

    weight_limit_kg = trip.limit_kg

    # Check Weight
    if over_limit(
        current=trip.total_items_weight,
        additional=new_item.weight_kg,
        limit=weight_limit_kg,
    ):
        if not current_items:
            return RemovalRecommendation(
                status=RemovalRecommendationStatus.remove,
                reason=RemovalRecommendationReason.overweight,
                swap_candidates=None,
            )
        elif new_item.item_importance > min_item_importance:

            # Order by importance ASC and add items to list until overflow is fixed
            weight_overflow = (
                trip.total_items_weight + new_item.weight_kg
            ) - weight_limit_kg
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
    if over_limit(
        current=trip.total_items_volume,
        additional=new_item.estimated_volume_cm3,
        limit=VOLUME_LIMIT_CM3,
    ):
        if not current_items:
            return RemovalRecommendation(
                status=RemovalRecommendationStatus.remove,
                reason=RemovalRecommendationReason.over_volume,
                swap_candidates=None,
            )
        elif new_item.item_importance > min_item_importance:

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
