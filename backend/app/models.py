from datetime import datetime
from typing import Dict, Optional, List
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

class BoundingBox(BaseModel):
    x_min: float
    y_min: float
    x_max: float
    y_max: float

class Dimensions(BaseModel):
    length: float
    width: float
    height: float

class YoloResult(BaseModel):
    item_name: str
    class_name: str = Field(..., alias="class")
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    bounding_boxes: List[BoundingBox]

    @field_validator("bounding_boxes", mode="before")
    def convert_bounding_boxes(cls, v):
        """
        YOLO returns bounding boxes as:
            [[x_min, y_min, x_max, y_max], ...]
        We convert them into actual BoundingBox objects.
        """
        if not isinstance(v, list):
            raise ValueError("bounding_boxes must be a list")

        converted = []
        for bb in v:
            if not isinstance(bb, list) or len(bb) != 4:
                raise ValueError(
                    f"Invalid bounding box format: {bb}. Expected [x_min, y_min, x_max, y_max]"
                )
            converted.append(
                BoundingBox(
                    x_min=bb[0],
                    y_min=bb[1],
                    x_max=bb[2],
                    y_max=bb[3]
                )
            )
        return converted

class Item(BaseModel):
    item_id: str = Field(default_factory=lambda: str(uuid4()))
    item_name: Optional[str] = None
    class_name: Optional[str] = None
    bounding_boxes: Optional[List[BoundingBox]] = None
    weight_kg: Optional[float] = None
    confidence: Optional[float] = None
    dimensions_cm: Optional[Dimensions] = None
    estimated_volume_cm3: Optional[float] = None

class ItemUpdate(BaseModel):
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
    items: Optional[List[str]] = Field(default=None, description="Item IDs")

class User(BaseModel):
    user_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    email: str
    password: str
    trips: List[str] = Field(default_factory=list)  # List of trip_ids
