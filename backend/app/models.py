from datetime import datetime
from typing import Dict, Optional, List
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator, model_validator

class BoundingBox(BaseModel):
    x_min: Optional[float] = None
    y_min: Optional[float] = None
    x_max: Optional[float] = None
    y_max: Optional[float] = None

    @model_validator(mode="after")
    def validate_coordinates(self):
        """Validate that all coordinates are present and valid."""
        if self.x_min is None or self.y_min is None or self.x_max is None or self.y_max is None:
            raise ValueError("All bounding box coordinates (x_min, y_min, x_max, y_max) must be provided")
        if self.x_min >= self.x_max:
            raise ValueError("x_min must be less than x_max")
        if self.y_min >= self.y_max:
            raise ValueError("y_min must be less than y_max")
        return self

class Dimensions(BaseModel):
    length: float
    width: float
    height: Optional[float] = None

class CVResult(BaseModel):
    item_name: str
    class_name: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    bounding_boxes: List[BoundingBox]
    dimensions: Dimensions

class Item(BaseModel):
    item_id: str = Field(default_factory=lambda: str(uuid4()))
    weight_kg: Optional[float] = None
    estimated_volume_cm3: Optional[float] = None
    cv_results: Optional[List[CVResult]] = None

class ItemUpdate(BaseModel):
    weight_kg: Optional[float] = None
    estimated_volume_cm3: Optional[float] = None
    cv_result: Optional[CVResult] = None

class Trip(BaseModel):
    trip_id: str = Field(default_factory=lambda: str(uuid4()))
    destination: str
    duration_days: int
    doing_laundry: bool
    items: Optional[List[str]] = Field(default=None, description="Item IDs")

class User(BaseModel):
    user_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    email: str
    password: str
    trips: List[str] = Field(default_factory=list)  # List of trip_ids
