# Main function: get_item_importance()
# Returns: int 'score' with value 0 to 100

from app.models import (
    Activity,
    Item,
    Trip,
)


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

    if name in ["laptop", "laptop charger"] and Activity.work not in trip.activities:
        score = 0

    # Not sure how weather is going to work yet
    # if name == "Coat" and "hot" in (trip.weather or "").lower():
    #     score = 0

    item.item_importance = score
    return score
