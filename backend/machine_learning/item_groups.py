from app.models import RecommendedItem

CLOTHING = [
    RecommendedItem(item_name="Shirt", reason="Needed for everyday wear", priority=1),
    RecommendedItem(item_name="Pants", reason="Needed for everyday wear", priority=1),
    RecommendedItem(item_name="Socks", reason="Needed for everyday wear", priority=1),
    RecommendedItem(item_name="Shoes", reason="Needed for everyday wear", priority=1),
]

ACCESSORIES = [
    RecommendedItem(
        item_name="Sunglasses", reason="Needed for sunny weather", priority=1
    ),
    RecommendedItem(
        item_name="Umbrella", reason="Needed for rainy weather", priority=1
    ),
]

TOILETRIES = [
    RecommendedItem(
        item_name="Toothpaste", reason="Needed for oral hygiene", priority=1
    ),
    RecommendedItem(
        item_name="Toothbrush", reason="Needed for oral hygiene", priority=1
    ),
]
