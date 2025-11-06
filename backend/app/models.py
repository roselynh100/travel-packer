from datetime import datetime
from typing import Dict, Optional, List
from uuid import uuid4

from pydantic import BaseModel, Field


class Item(BaseModel):
    item_id: str = Field(default_factory=lambda: str(uuid4()))
    name: Optional[str] = None
    weight_kg: Optional[float] = None
    confidence: Optional[float] = None
    dimensions_cm: Optional[Dict[str, float]] = None  # {length, width, height}
    estimated_volume_cm3: Optional[float] = None


class Trip(BaseModel):
    trip_id: str = Field(default_factory=lambda: str(uuid4()))
    destination: str
    duration_days: int
    doing_laundry: bool
    items: List[str] = Field(default_factory=list)  # List of item_ids


class User(BaseModel):
    user_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    email: str
    password: str
    trips: List[str] = Field(default_factory=list)  # List of trip_ids
