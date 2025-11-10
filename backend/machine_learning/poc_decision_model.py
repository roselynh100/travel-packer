import json


# Load items from items.json
def load_items(filename="items.json"):
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: The file {filename} was not found.")
        return []
    except json.JSONDecodeError:
        print(f"Error: Could not decode the JSON from {filename}.")
        return []


# User inputs trip details
def get_trip_details():
    print("--- Enter trip details ---")

    details = {}
    details["purpose"] = input("Purpose (work/leisure): ").lower().strip()
    details["weather"] = (
        input("Weather forecast (sunny/rainy/hot/cold/mixed): ").lower().strip()
    )
    # Note: in our actual solution, weather will be grabbed from backend and users will instead input destination and trip dates

    details["weight_limit_kg"] = 3.0
    details["volume_limit_L"] = 8.0
    # Note: limits will be determined by user inputting bag types they are bringing + airline

    return details


# Packing algorithm
def packing_algorithm():
    item_database = load_items()
    trip = get_trip_details()

    pack_list = []
    leave_list = []

    total_weight_kg = 0.0
    total_volume_L = 0.0

    for item_data in item_database:
        item = item_data.copy()

        item["importance"] = item["baseImportance"]

        # Rules
        if (item["name"] == "Laptop" or item["name"] == "Laptop Charger") and trip[
            "purpose"
        ] != "work":
            item["importance"] = 0

        if item["name"] == "Coat" and trip["weather"] == "hot":
            item["importance"] = 0

        if item["name"] == "Sunglasses" and (
            trip["weather"] != "sunny" and trip["weather"] != "mixed"
        ):
            item["importance"] = 0

        if (
            item["name"] == "Umbrella"
            and trip["weather"] != "rainy"
            and trip["weather"] != "mixed"
        ):
            item["importance"] = 0

        # Add to pack list if importance is > 0
        if item["importance"] > 0:
            pack_list.append(item)
            total_weight_kg += item["weight_kg"]
            total_volume_L += item["volume_L"]
            print(f"Adding {item['name']} to pack list")
        else:
            leave_list.append(item)
            print(f"Adding {item['name']} to leave list")

    # Print pack list weight
    print(f"Total weight: {total_weight_kg}, total volume: {total_volume_L}")

    over_weight = total_weight_kg > trip["weight_limit_kg"]
    over_volume = total_volume_L > trip["volume_limit_L"]

    if over_weight or over_volume:
        if over_weight:
            print(f"List is {total_weight_kg - trip['weight_limit_kg']} kg overweight")
        if over_volume:
            print(f"List is {total_volume_L - trip['volume_limit_L']} L over volume")

    # Sort pack list by importance
    pack_list.sort(key=lambda x: x["importance"])

    # Remove lowest importance items until within limits
    while (
        total_weight_kg > trip["weight_limit_kg"]
        or total_volume_L > trip["volume_limit_L"]
    ):

        # Move to leave_list
        item_to_remove = pack_list.pop(0)
        leave_list.append(item_to_remove)

        # Subtract weight and volume of removed item
        total_weight_kg -= item_to_remove["weight_kg"]
        total_volume_L -= item_to_remove["volume_L"]

        print(f"Remove {item_to_remove['name']}")

    # Display final pack list
    print("--- Final Pack List ---")
    for item in pack_list:
        print(f"{item['name']}")

    # Display final leave list
    print("--- Items to leave behind ---")
    if not leave_list:
        print("No items on leave list")
    else:
        for item in leave_list:
            print(f"{item['name']}")

    # Display final weight and volume
    print(f"Final weight: {total_weight_kg} / {trip['weight_limit_kg']} kg")
    print(f"Final volume: {total_volume_L} / {trip['volume_limit_L']} L")


if __name__ == "__main__":
    packing_algorithm()
