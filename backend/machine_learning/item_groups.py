from app.models import RecommendedItem

CLOTHING = [
    RecommendedItem(item_name="shirt", reason="Needed for everyday wear", priority=1),
    RecommendedItem(item_name="pants", reason="Needed for everyday wear", priority=1),
    RecommendedItem(item_name="socks", reason="Needed for everyday wear", priority=1),
    RecommendedItem(item_name="shoes", reason="Needed for everyday wear", priority=1),
]

ACCESSORIES = [
    RecommendedItem(
        item_name="sunglasses", reason="Needed for sunny weather", priority=1
    ),
    RecommendedItem(
        item_name="umbrella", reason="Needed for rainy weather", priority=1
    ),
]

TOILETRIES = [
    RecommendedItem(
        item_name="toothpaste", reason="Needed for oral hygiene", priority=1
    ),
    RecommendedItem(
        item_name="toothbrush", reason="Needed for oral hygiene", priority=1
    ),
]

ESSENTIALS = [
    RecommendedItem(item_name="cell phone", reason="Essential item", priority=1),
]
