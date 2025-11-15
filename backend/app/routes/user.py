from fastapi import APIRouter, HTTPException
from typing import List, Dict

from app.models import User, Trip
from app.state.db import users_store, trips_store

router = APIRouter()


@router.post("/", response_model=User)
def create_user(user: User):
    """Create a new user."""
    users_store[user.user_id] = user
    return user


@router.get("/", response_model=List[User])
def get_users():
    """Get all users."""
    return list[User](users_store.values())


@router.get("/{user_id}", response_model=User)
def get_user(user_id: str):
    """Get a specific user by ID."""
    if user_id not in users_store:
        raise HTTPException(status_code=404, detail="User not found")
    return users_store[user_id]


@router.put("/{user_id}", response_model=User)
def update_user(user_id: str, user: User):
    """Update a user."""
    if user_id not in users_store:
        raise HTTPException(status_code=404, detail="User not found")
    user.user_id = user_id  # Ensure ID matches
    users_store[user_id] = user
    return user


@router.delete("/{user_id}")
def delete_user(user_id: str):
    """Delete a user."""
    if user_id not in users_store:
        raise HTTPException(status_code=404, detail="User not found")
    del users_store[user_id]
    return {"message": "User deleted successfully"}


@router.get("/{user_id}/trips", response_model=List[Trip])
def get_user_trips(user_id: str):
    """Get all trips for a specific user."""
    if user_id not in users_store:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = users_store[user_id]
    trips = []
    for trip_id in user.trips:
        if trip_id in trips_store:
            trips.append(trips_store[trip_id])
    
    return trips

