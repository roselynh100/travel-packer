import json


# What is this function for?
def run_ml() -> str:
    return "ML function"


def load_items(filename="items.json"):
    """Loads item list from JSON file."""
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: The file {filename} was not found.")
        return []
    except json.JSONDecodeError:
        print(f"Error: Could not decode the JSON from {filename}.")
        return []


def get_totals(pack_list):
    """Calculates the total weight and volume of a list of items."""
    total_weight_kg = sum(item["weight_kg"] for item in pack_list)
    total_volume_L = sum(item["volume_L"] for item in pack_list)
    return total_weight_kg, total_volume_L


def is_overlimit(pack_list, limits):
    """Checks if the pack list is over the weight or volume limits."""
    total_weight, total_volume = get_totals(pack_list)
    return (
        total_weight > limits["weight_limit_kg"]
        or total_volume > limits["volume_limit_L"]
    )


def display_item_list(item_list):
    """Prints a formatted list of items."""
    if not item_list:
        print("  (empty)")
        return
    for item in item_list:
        print(f"  - {item['name']} (Importance: {item['importance']})")
