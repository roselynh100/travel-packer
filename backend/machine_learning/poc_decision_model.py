from app.models import Item, RecommendedItem
from typing import List

def packing_algorithm(items: List[Item]):
    """Returns items to remove."""
    # TO-DO: replace with our actual packing_algorithm once thats ready (run with integration tests to ensure compatibility with endpoint)
    to_remove = [
        item.model_dump()
        for item in items
        if item.weight_kg is not None and item.weight_kg > 3.0
    ]
    return to_remove

def generate_recommendation_list(destination: str, duration_days: int, doing_laundry: bool, activities: str | None) -> List[RecommendedItem]:
    """Returns a list of things that the user should pack based on trip details"""
    # TO-DO: replace with our actual generate_recommendation_list algorithm once thats ready
    recs = [
        RecommendedItem(item_name="Passport", reason="Required for international travel", priority=1),
        RecommendedItem(item_name="Phone Charger", reason="Daily essential", priority=2),
    ]
    return recs