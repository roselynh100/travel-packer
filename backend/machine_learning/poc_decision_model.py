from app.models import Item
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