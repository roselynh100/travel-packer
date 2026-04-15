import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException

from app.models import (
    Activity,
    Airline,
    Item,
    Location,
    RecommendedItem,
    RemovalRecommendation,
    RemovalRecommendationUpdate,
    Trip,
    TripUpdate,
)
from app.state.db import items_store, recommendations_store, trips_store, users_store
from helpers.trip_helpers import (
    _calculate_trip_emissions_per_kg,
    _get_forecast_stats,
    _get_historical_stats,
    _get_lat_lon_for_trip,
    _trip_within_forecast_window,
)
from machine_learning.generator import baseline_list_algorithm
from machine_learning.optimizer import packing_decision_algorithm
from machine_learning.packing_score import get_user_packing_score

router = APIRouter()


@router.post("/", response_model=Trip)
def create_trip(trip: Trip, user_id: Optional[str] = None):
    trips_store[trip.trip_id] = trip

    # associate user if provided
    if user_id:
        if user_id not in users_store:
            raise HTTPException(status_code=404, detail="User not found")

        user = users_store[user_id]
        if trip.trip_id not in user.trips:
            user.trips.append(trip.trip_id)

    return trip


@router.get("/", response_model=List[Trip])
def get_trips():
    """Get all trips."""
    return list(trips_store.values())


@router.get("/activities", response_model=List[str])
def get_activities():
    """Get all activities."""
    return [activity.value for activity in Activity]


@router.get("/airlines", response_model=List[str])
def get_airlines():
    """Get all airlines."""
    return [airline.value for airline in Airline]


@router.get("/{trip_id}", response_model=Trip)
def get_trip(trip_id: str):
    """Get a specific trip by ID."""
    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trips_store[trip_id]


@router.put("/{trip_id}", response_model=Trip)
def update_trip(trip_id: str, update: TripUpdate):
    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")

    existing = trips_store[trip_id]
    patch_data = update.model_dump(exclude_unset=True)
    duration_days = patch_data.pop("duration_days", None)

    if "destination_details" in patch_data:
        patch_data["destination_details"] = Location.model_validate(
            patch_data["destination_details"]
        )

    if duration_days is not None:
        patch_data["end_date"] = existing.start_date + datetime.timedelta(
            days=duration_days - 1
        )

    updated = existing.model_copy(update=patch_data)
    updated = Trip.model_validate(updated.model_dump())

    trips_store[trip_id] = updated
    return updated


@router.delete("/{trip_id}")
def delete_trip(trip_id: str):
    """Delete a trip."""
    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")

    # remove trip reference from items
    for item in items_store.values():
        if trip_id in item.trips:
            item.trips.remove(trip_id)

    # remove from users
    for user in users_store.values():
        if trip_id in user.trips:
            user.trips.remove(trip_id)

    del trips_store[trip_id]
    return {"message": "Trip deleted successfully"}


@router.post("/{trip_id}/item/{item_id}")
def add_item_to_trip(trip_id: str, item_id: str):
    """Add existing item to a trip. This endpoint does not create the item itself."""
    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")

    if item_id not in items_store:
        raise HTTPException(status_code=404, detail="Item not found")

    trip = trips_store[trip_id]
    item = items_store[item_id]
    if item.item_id not in trip.items:
        trip.items.append(item.item_id)

    if trip_id not in item.trips:
        item.trips.append(trip_id)

    if item.estimated_volume_cm3 is not None or item.weight_kg is not None:
        recalculate_trip_totals(trip_id)


@router.delete("/{trip_id}/item/{item_id}")
def remove_item_from_trip(trip_id: str, item_id: str):
    """Remove existing item from a trip. This endpoint does not delete the item itself."""
    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")

    if item_id not in items_store:
        raise HTTPException(status_code=404, detail="Item not found")

    trip = trips_store[trip_id]
    item = items_store[item_id]
    if item.item_id in trip.items:
        trip.items.remove(item.item_id)

    if trip_id in item.trips:
        item.trips.remove(trip_id)

    if item.estimated_volume_cm3 is not None or item.weight_kg is not None:
        recalculate_trip_totals(trip_id)


@router.get("/{trip_id}/items", response_model=List[Item])
def get_trip_items(trip_id: str):
    """Get all items for a specific trip."""
    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")

    trip = trips_store[trip_id]
    if trip.items is None:
        return []
    trip_items = [items_store[id] for id in trip.items if id in items_store]

    return trip_items


@router.post("/{trip_id}/recalculate-totals")
def recalculate_trip_totals(trip_id: str):
    """Recalculate total weight, item volume, and liquid volume for a trip."""
    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")

    trip = trips_store[trip_id]

    trip.total_items_weight = sum(
        ((items_store[item_id].weight_kg or 0.0) * items_store[item_id].quantity)
        for item_id in trip.items
    )
    trip.total_items_volume = sum(
        (
            (items_store[item_id].estimated_volume_cm3 or 0.0)
            * items_store[item_id].quantity
        )
        for item_id in trip.items
    )
    trip.total_liquids_volume = sum(
        (
            (items_store[item_id].estimated_volume_cm3 or 0.0)
            * items_store[item_id].quantity
        )
        for item_id in trip.items
        if items_store[item_id].is_liquid
    )

    # TO-DO: can remove the return if not useful
    return {
        "trip_id": trip_id,
        "total_weight": trip.total_items_weight,
        "total_volume": trip.total_items_volume,
        "total_liquids_volume": trip.total_liquids_volume,
    }


@router.get("/{trip_id}/recommendations", response_model=List[RecommendedItem])
def get_trip_recommendations(trip_id: str):
    """Generate packing recommendations from the trip metadata and activities"""

    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")

    trip = trips_store[trip_id]

    recs = baseline_list_algorithm(trip)

    if recs is None:
        raise HTTPException(status_code=500, detail="No recommendations generated")

    return recs


@router.get(
    "/{trip_id}/item/{item_id}/packing-decision", response_model=RemovalRecommendation
)
def get_packing_decision(trip_id: str, item_id: str):
    """Returns decision on whether to pack an item."""
    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")

    if item_id not in items_store:
        raise HTTPException(status_code=404, detail="Item not found")

    trip = trips_store[trip_id]
    item = items_store[item_id]

    items = get_trip_items(trip_id)

    recommendation = packing_decision_algorithm(item, trip, items)
    recommendations_store[recommendation.recommendation_id] = recommendation
    trip.recommendations.append(recommendation.recommendation_id)
    item.recommendation = recommendation.recommendation_id

    return recommendation


@router.patch(
    "/{trip_id}/recommendations/{recommendation_id}",
    response_model=RemovalRecommendation,
)
def update_removal_recommendation(
    trip_id: str, recommendation_id: str, update: RemovalRecommendationUpdate
):
    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")

    if recommendation_id not in recommendations_store:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    trip = trips_store[trip_id]
    if recommendation_id not in trip.recommendations:
        raise HTTPException(status_code=404, detail="Recommendation not found in trip")

    existing = recommendations_store[recommendation_id]
    patch_data = update.model_dump(exclude_unset=True)
    updated = existing.model_copy(update=patch_data)
    recommendations_store[recommendation_id] = updated
    return updated


@router.delete(
    "/{trip_id}/item/{item_id}/removal-recommendations/{recommendation_id}",
    response_model=RemovalRecommendation,
)
def delete_removal_recommendation(trip_id: str, item_id: str, recommendation_id: str):
    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")

    if item_id not in items_store:
        raise HTTPException(status_code=404, detail="Item not found")

    if recommendation_id not in recommendations_store:
        raise HTTPException(status_code=404, detail="Recommendation not found")

    trip = trips_store[trip_id]
    recommendation = recommendations_store[recommendation_id]
    item = items_store[item_id]

    if item_id not in trip.items:
        raise HTTPException(status_code=404, detail="Item not found in trip")

    if recommendation_id not in trip.recommendations:
        raise HTTPException(status_code=404, detail="Recommendation not found in trip")

    if item.recommendation != recommendation_id:
        raise HTTPException(
            status_code=404, detail="Recommendation not attached to item"
        )

    item.recommendation = None
    trip.recommendations.remove(recommendation_id)
    del recommendations_store[recommendation_id]

    return recommendation


@router.post("/{trip_id}/emissions", response_model=Trip)
def calculate_trip_emissions(trip_id: str):
    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")

    trip = trips_store[trip_id]
    trip.emissions_per_kg = _calculate_trip_emissions_per_kg(trip)
    trips_store[trip_id] = trip
    return trip


@router.get("/{trip_id}/weather", response_model=Trip)
def get_weather(trip_id: str):
    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")

    trip = trips_store[trip_id]

    start_date = trip.start_date.date()
    end_date = trip.end_date.date()
    if end_date < start_date:
        raise HTTPException(
            status_code=400, detail="Trip end_date is before start_date"
        )
    trip_days = (end_date - start_date).days + 1

    lat, lon = _get_lat_lon_for_trip(trip)

    if _trip_within_forecast_window(start_date, end_date):
        lowest, highest, precip_pct = _get_forecast_stats(
            lat, lon, start_date, end_date, trip_days
        )
    else:
        lowest, highest, precip_pct = _get_historical_stats(
            lat, lon, start_date, end_date, trip_days
        )

    if lowest is None or highest is None or precip_pct is None:
        raise HTTPException(
            status_code=502,
            detail="Weather data unavailable for the requested trip dates",
        )

    trip.lowest_temp = lowest
    trip.highest_temp = highest
    trip.precipitation_percentage = precip_pct

    trips_store[trip_id] = trip
    return trip


@router.get("/{trip_id}/packing-score", response_model=float)
def get_packing_score(trip_id: str):
    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")

    trip = trips_store[trip_id]

    return get_user_packing_score(trip)
