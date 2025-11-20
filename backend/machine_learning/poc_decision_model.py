from collections import Counter
from typing import Any, Dict, List

import utils

Item = Dict[str, Any]


def get_trip_details():
    print("--- Enter trip details ---")
    details = {}
    details["purpose"] = input("Purpose (work/leisure): ").lower().strip()
    details["weather"] = (
        input("Weather forecast (sunny/rainy/hot/cold/mixed): ").lower().strip()
    )

    # Hard coded limits for now
    details["weight_limit_kg"] = 5.0
    details["volume_limit_L"] = 10.0

    return details


def run_manual_removal(pack_list, leave_list, limits):
    """
    A mandatory loop that forces the user to manually remove items until the bag is compliant.
    This will run if the bag is over the limits.
    """
    print("\n" + "=" * 30)
    print("--- MANUAL TRIAGE MODE ---")
    print("Your bag is over limit. You must remove items.")

    while utils.is_overlimit(pack_list, limits):
        current_weight, current_volume = utils.get_totals(pack_list)
        over_weight = current_weight - limits["weight_limit_kg"]
        over_volume = current_volume - limits["volume_limit_L"]

        print("\n" + "-" * 30)
        if over_weight > 0:
            print(f"CURRENTLY {over_weight:.2f} kg OVERWEIGHT")
        if over_volume > 0:
            print(f"CURRENTLY {over_volume:.2f} L OVER VOLUME")

        print("\nYour Pack List:")

        """
        SORTING LOGIC:
        Show duplicate items first, then sort by importance
        """
        # Get counts of all item names in the current pack_list
        name_counts = Counter(item["name"] for item in pack_list)

        def sort_key(item):
            # This will be True for unique items, False for duplicates
            is_unique = name_counts[item["name"]] == 1

            # Duplicates come first, then order by importance
            return (is_unique, item["importance"])

        # Sort the actual pack_list using this new key
        pack_list.sort(key=sort_key)

        # Display the list with labels
        for i, item in enumerate(pack_list):
            label = ""
            # Check if it's a duplicate
            if name_counts[item["name"]] > 1:
                label = "DUPLICATE: "

            print(
                f"  [{i}] {label}{item['name']} "
                f"({item['weight_kg']}kg, {item['volume_L']}L) "
                f"(Importance: {item['importance']})"
            )

        print("-" * 30)

        try:
            choice = input("Enter the number of the item to remove: ")
            item_index = int(choice)

            if 0 <= item_index < len(pack_list):
                item_to_remove = pack_list.pop(item_index)
                leave_list.append(item_to_remove)
                print(f"Removed {item_to_remove['name']}.")
            else:
                print("Invalid number. Try again.")

        except ValueError:
            print("Invalid input. Please enter a number.")

    print("--- MANUAL TRIAGE COMPLETE ---")


# --- MAIN PACKING ALGORITHM ---


def packing_algorithm(items: List[Item]):
    """
    Runs the complete packing process.
    Args:
        items: a list of item objects
    """
    trip = get_trip_details()

    pack_list = []
    leave_list = []

    # 1. Initial Scoring and Sorting
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

        if item["importance"] > 0:
            pack_list.append(item)
        else:
            leave_list.append(item)

    print("\n--- Initial Pack Complete ---")

    # 2. Manual Reduction (if needed)

    # Check if overweight. If so, allow user to select items to remove.
    if utils.is_overlimit(pack_list, trip):
        current_weight, current_volume = utils.get_totals(pack_list)
        over_weight = current_weight - trip["weight_limit_kg"]
        over_volume = current_volume - trip["volume_limit_L"]

        print("\n" + "=" * 30)
        print("🛑 BAG IS OVER LIMITS")
        if over_weight > 0:
            print(f"  Overweight by: {over_weight:.2f} kg")
        if over_volume > 0:
            print(f"  Over volume by: {over_volume:.2f} L")
        print(
            f"  Current: {current_weight:.2f}kg / {trip['weight_limit_kg']}kg, "
            f"{current_volume:.2f}L / {trip['volume_limit_L']}L"
        )

        run_manual_removal(pack_list, leave_list, trip)

    # 3. Final Lists
    print("\n" + "=" * 30)
    print("🎉 SUCCESS! Your bag is now within all limits.")
    print("=" * 30)

    # Display final pack list
    print("\n--- ✅ Final Pack List ---")
    pack_list.sort(key=lambda x: x["importance"], reverse=True)
    utils.display_item_list(pack_list)

    # Display final leave list
    print("\n--- ❌ Items to leave behind ---")
    utils.display_item_list(leave_list)

    # Display final weight and volume
    final_weight, final_volume = utils.get_totals(pack_list)
    print(f"\nFinal weight: {final_weight:.2f} / {trip['weight_limit_kg']} kg")
    print(f"Final volume: {final_volume:.2f} / {trip['volume_limit_L']} L")


if __name__ == "__main__":
    item_database = utils.load_items()

    packing_algorithm(item_database)
