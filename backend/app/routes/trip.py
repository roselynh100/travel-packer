import json
from typing import List, Optional

import requests
from fastapi import APIRouter, HTTPException

from app.models import Item, RecommendedItem, RemovalRecommendation, Trip, TripUpdate
from app.state.db import items_store, trips_store, users_store
from constants import TOMORROW_WEATHER_URL
from machine_learning.poc_decision_model import (
    baseline_list_algorithm,
    packing_decision_algorithm,
)

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
    updated = existing.model_copy(update=patch_data)

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
    """Add existing item to a trip."""
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
    """Recalculate total weight and volume for a trip."""
    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")

    trip = trips_store[trip_id]

    trip.total_items_weight = sum(
        (items_store[item_id].weight_kg or 0.0) for item_id in trip.items
    )
    trip.total_items_volume = sum(
        (items_store[item_id].estimated_volume_cm3 or 0.0) for item_id in trip.items
    )

    # TO-DO: can remove the return if not useful
    return {
        "trip_id": trip_id,
        "total_weight": trip.total_items_weight,
        "total_volume": trip.total_items_volume,
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

    return packing_decision_algorithm(item, trip, items)

@router.post("/{trip_id}/weather")
def get_weather(trip_id: str):
    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")

    trip = trips_store[trip_id]
    destination = trip.destination

    print(destination)
    if destination != "New York":
        raise HTTPException(status_code=404, detail="Location not supported")

    api_url = TOMORROW_WEATHER_URL.format(location=destination)

    headers = {"accept": "application/json", "accept-encoding": "deflate, gzip, br"}
    response = requests.get(api_url, headers=headers)
    weather_json_str = response.text
    weather_data = json.loads(weather_json_str)

    lowest_temp = 1000
    highest_temp = -1000
    for timestamp in weather_data["timelines"]["minutely"]:
        temperature = timestamp["values"]["temperature"]
        lowest_temp = min(lowest_temp, temperature)
        highest_temp = max(highest_temp, temperature)

    print(lowest_temp)
    print(highest_temp)

    trip.highest_temp = highest_temp
    trip.lowest_temp = lowest_temp
