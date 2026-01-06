# Main function: baseline_list_algorithm()
# Returns: List[RecommendedItem]

from typing import List, Optional

from app.models import (
    RecommendedItem,
    Trip,
)

from .item_groups import ACCESSORIES, CLOTHING, ESSENTIALS, TOILETRIES


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
