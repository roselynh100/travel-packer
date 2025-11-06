from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Optional

from app.models import Trip, Item

router = APIRouter()

trips_store: Dict[str, Trip] = {}  # trip_id -> Trip


@router.post("/", response_model=Trip)
def create_trip(trip: Trip, user_id: Optional[str] = Query(None)):
    """Create a new trip and optionally associate it with a user."""
    trips_store[trip.trip_id] = trip
    
    if user_id:
        from app.routes.user import users_store
        if user_id not in users_store:
            raise HTTPException(status_code=404, detail="User not found")
        if trip.trip_id not in users_store[user_id].trips:
            users_store[user_id].trips.append(trip.trip_id)
    
    return trip


@router.get("/", response_model=List[Trip])
def get_trips():
    """Get all trips."""
    return list[Trip](trips_store.values())


@router.get("/{trip_id}", response_model=Trip)
def get_trip(trip_id: str):
    """Get a specific trip by ID."""
    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trips_store[trip_id]


@router.put("/{trip_id}", response_model=Trip)
def update_trip(trip_id: str, trip: Trip):
    """Update a trip."""
    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")
    trip.trip_id = trip_id 
    if not trip.items:
        trip.items = trips_store[trip_id].items
    trips_store[trip_id] = trip
    return trip


@router.delete("/{trip_id}")
def delete_trip(trip_id: str):
    """Delete a trip."""
    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    from app.routes.user import users_store
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
    
    from app.routes.item import item_store
    
    trip = trips_store[trip_id]
    items = []
    for item_id in trip.items:
        if item_id in item_store:
            items.append(item_store[item_id])
    
    return items

