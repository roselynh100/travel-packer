from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional

from app.models import Trip, TripUpdate, Item, RecommendedItem
from machine_learning.poc_decision_model import packing_algorithm, generate_recommendation_list
from app.state.db import trips_store, items_store, users_store

router = APIRouter()

@router.post("/", response_model=Trip)
def create_trip(trip: Trip, user_id: Optional[str] = Query(None)):
    """Create a new trip and optionally associate it with a user."""
    trips_store[trip.trip_id] = trip
    
    if user_id:
        if user_id not in users_store:
            raise HTTPException(status_code=404, detail="User not found")
        if trip.trip_id not in users_store[user_id].trips:
            users_store[user_id].trips.append(trip.trip_id)
    
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
def update_trip(trip_id: str, trip: TripUpdate):
    """Update a trip."""
    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")
    existing = trips_store[trip_id]
    patch_data = trip.model_dump(exclude_unset=True)

    updated = existing.model_copy(update=patch_data)

    trips_store[trip_id] = updated
    return updated


@router.delete("/{trip_id}")
def delete_trip(trip_id: str):
    """Delete a trip."""
    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    for user in users_store.values():
        if trip_id in user.trips:
            user.trips.remove(trip_id)
    
    del trips_store[trip_id]
    return {"message": "Trip deleted successfully"}


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

@router.post("/{trip_id}/removal-recommendations", response_model=List[Item])
def get_removal_recommendations(trip_id: str):
    """Suggest items to remove from a trip based on  recommendation algorithm"""

    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")

    trip = trips_store[trip_id]

    if trip.items is None:
        trip_items = []
    else:
        trip_items = [items_store[id] for id in trip.items if id in items_store]

    result = packing_algorithm(trip_items)

    items = [Item(**d) for d in result]

    return items

@router.post("/{trip_id}/recommendations", response_model=List[RecommendedItem])
def get_trip_recommendations(trip_id: str):
    """Generate packing recommendations from the trip metadata and activities"""

    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")

    trip = trips_store[trip_id]

    recs = generate_recommendation_list(
        destination=trip.destination,
        duration_days=trip.duration_days,
        doing_laundry=trip.doing_laundry,
        activities=trip.activities,
    )

    if recs is None or not isinstance(recs, list):
        raise HTTPException(status_code=500, detail="Input should be a valid list")

    return recs