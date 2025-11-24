from fastapi import APIRouter, HTTPException
from typing import List, Optional

from app.models import Trip, TripUpdate, Item, RecommendedItem, RemovalRecommendation
from machine_learning.poc_decision_model import generate_recommendation_list, removal_recommendation_algorithm
from app.state.db import trips_store, items_store, users_store

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

@router.post("/{trip_id}/recommendations", response_model=List[RecommendedItem])
def get_trip_recommendations(trip_id: str):
    """Generate packing recommendations from the trip metadata and activities"""

    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")

    trip = trips_store[trip_id]

    recs = generate_recommendation_list(trip)
    
    if recs is None:
        raise HTTPException(status_code=500, detail="No recommendations generated")

    return recs

@router.post("/{trip_id}/item/{item_id}/removal-recommendation",
             response_model=RemovalRecommendation)
def get_removal_recommendation(trip_id: str, item_id: str):
    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")

    if item_id not in items_store:
        raise HTTPException(status_code=404, detail="Item not found")

    trip = trips_store[trip_id]
    item = items_store[item_id]

    if item_id not in trip.items:
        raise HTTPException(status_code=400, detail="Item does not belong to this trip")

    return removal_recommendation_algorithm(item, trip)
