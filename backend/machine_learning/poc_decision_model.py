from app.models import Item, RecommendedItem, Trip, RemovalRecommendation
from typing import List

def removal_recommendation_algorithm(item: Item, trip: Trip) -> RemovalRecommendation:
    """Returns items to remove."""
    # TO-DO: replace with our actual packing_algorithm once thats ready (run with integration tests to ensure compatibility with endpoint)
    rec = RemovalRecommendation(should_remove=True, reason="Exceeded baggage limit")
    return rec

def generate_recommendation_list(trip: Trip) -> List[RecommendedItem]:
    """Returns a list of things that the user should pack based on trip details"""
    # access trip info like this:
    activities = trip.activities

    # TO-DO: replace with our actual generate_recommendation_list algorithm once thats ready
    recs = [
        RecommendedItem(item_name="Passport", reason="Required for international travel", priority=1),
        RecommendedItem(item_name="Phone Charger", reason="Daily essential", priority=2),
    ]
    return recs