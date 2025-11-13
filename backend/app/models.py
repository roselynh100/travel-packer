from datetime import datetime
from typing import Dict, Optional, List
from uuid import uuid4

from pydantic import BaseModel, Field

class BoundingBox(BaseModel):
    x_min: float
    y_min: float
    x_max: float
    y_max: float

class Dimensions(BaseModel):
    length: float
    width: float
    height: float

class Item(BaseModel):
    item_id: str = Field(default_factory=lambda: str(uuid4()))
    item_name: Optional[str] = None
    class_name: Optional[str] = None
    bounding_boxes: Optional[List[BoundingBox]] = None
    weight_kg: Optional[float] = None
    confidence: Optional[float] = None
    dimensions_cm: Optional[Dimensions] = None
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
