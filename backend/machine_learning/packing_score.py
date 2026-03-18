from typing import Dict

from app.models import Trip
from app.state.db import items_store, recommendations_store
from machine_learning.generator import baseline_list_algorithm


def calc_list_match_score(
    packed_counts: Dict[str, int], recommended_counts: Dict[str, int]
) -> float:
    """Calculates S_{list_match} with a penalty for extra/unrecommended items, scaled to 0-100."""
    total_recommended = sum(recommended_counts.values())
    total_rec_safe = max(1, total_recommended)

    match_sum = 0
    extras_sum = 0

    # Create a set of all unique categories from BOTH dictionaries to catch unrecommended items
    all_categories = set(packed_counts.keys()).union(set(recommended_counts.keys()))

    for category in all_categories:
        p_count = packed_counts.get(category, 0)
        r_count = recommended_counts.get(category, 0)

        match_sum += min(p_count, r_count)
        extras_sum += max(0, p_count - r_count)

    # Calculate base score and penalty
    base_match_score = 100.0 * (match_sum / total_rec_safe)
    penalty = 10.0 * (extras_sum / total_rec_safe)

    # Apply penalty and clip at 0 so it doesn't go negative
    return max(0.0, base_match_score - penalty)


def calc_optimization_score(current: float, maximum: float) -> float:
    """Calculates S_{weight} or S_{volume}."""
    usage_ratio = current / maximum

    if usage_ratio <= 0.8:
        return 100.0  # 0-80% usage is "Safe/Perfect"
    elif usage_ratio <= 1.0:
        # Scale from 100 down to 80 as they hit the limit
        return 100.0 - (usage_ratio - 0.8) * 100
    else:
        # Penalty for being over
        return max(0.0, 80.0 - 200.0 * (usage_ratio - 1.0))
    # if maximum <= 0:
    #     return 0.0 if current > 0 else 100.0 # Guard against division by zero

    # if current <= maximum:
    #     return 100.0 * (1 - (current / maximum))
    # else:
    #     # Penalty for exceeding the limit
    #     penalty_score = 100.0 - 200.0 * ((current - maximum) / maximum)
    #     return max(0.0, penalty_score)


def calc_acceptance_factor(accepted_recs: int, given_recs: int) -> float:
    """Calculates the Recommendation Acceptance Factor (Delta)."""
    if given_recs == 0:
        return 0.0

    # r = acceptance rate
    r = accepted_recs / max(1, given_recs)

    delta = 10.0 * (r - 0.5)

    # Clip between -10 and 10
    return max(-10.0, min(10.0, delta))


def calculate_final_score(
    packed_counts: Dict[str, int],
    recommended_counts: Dict[str, int],
    total_weight: float,
    max_weight: float,
    total_volume: float,
    max_volume: float,
    accepted_recs: int,
    given_recs: int,
) -> float:
    """Calculates the Final Packing Score (S_{final})."""

    # 1. Calculate individual component scores
    s_list = calc_list_match_score(packed_counts, recommended_counts)
    s_weight = calc_optimization_score(total_weight, max_weight)
    s_volume = calc_optimization_score(total_volume, max_volume)

    # 2. Calculate delta modifier
    delta = calc_acceptance_factor(accepted_recs, given_recs)

    # 3. Calculate base score (50% list, 25% weight, 25% volume)
    s_base = (0.50 * s_list) + (0.25 * s_weight) + (0.25 * s_volume)

    # 4. Apply delta and clip final score between 0 and 100
    s_final = s_base + delta
    return max(0.0, min(100.0, s_final))


def get_user_packing_score(trip: Trip) -> float:
    # 1. Map current items in the trip to counts
    # We fetch the actual Item objects from the items_store
    packed_counts: Dict[str, int] = {}
    packed_items = [items_store[iid] for iid in trip.items if iid in items_store]

    for item in packed_items:
        # Match using the CV name so it aligns with the recommendation engine
        name = item.cv_result.item_name if item.cv_result else "Unknown"
        packed_counts[name] = packed_counts.get(name, 0) + item.quantity

    # 2. Get Recommended Counts
    recommended_items = baseline_list_algorithm(trip)
    recommended_counts: Dict[str, int] = {}
    if recommended_items:
        for rec in recommended_items:
            recommended_counts[rec.item_name] = (
                recommended_counts.get(rec.item_name, 0) + 1
            )

    # 3. Calculate Acceptance Stats (for Delta)
    # Filter for RemovalRecommendations where status is not 'pack'
    total_recs_given = 0
    accepted_recs_count = 0

    for rec_id in trip.recommendations:
        rec = recommendations_store.get(rec_id)
        # Assuming 'type' or similar attribute identifies it as a RemovalRecommendation
        if (
            rec
            and getattr(rec, "type", None) == "RemovalRecommendation"
            and rec.status != "pack"
        ):
            total_recs_given += 1
            if rec.is_accepted:
                accepted_recs_count += 1

    # 4. Final Calculation
    return calculate_final_score(
        packed_counts=packed_counts,
        recommended_counts=recommended_counts,
        total_weight=trip.total_items_weight,
        max_weight=trip.limit_kg,
        total_volume=trip.total_items_volume,
        max_volume=75000.0,
        accepted_recs=accepted_recs_count,
        given_recs=total_recs_given,
    )
