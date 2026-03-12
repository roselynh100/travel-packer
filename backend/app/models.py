import datetime
from enum import Enum
from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, computed_field, field_validator, model_validator


class Activity(str, Enum):
    beach = "Beach"
    camping = "Camping"
    concert = "Concert"
    dancing = "Dancing"
    festival = "Festival"
    formal = "Formal"
    hiking = "Hiking"
    sightseeing = "Sightseeing"
    shopping = "Shopping"
    skating = "Skating"
    skiing = "Skiing"
    snowboarding = "Snowboarding"
    surfing = "Surfing"
    swimming = "Swimming"
    work = "Work"


class Airline(str, Enum):
    air_canada = "Air Canada"
    porter = "Porter"
    westjet = "Westjet"


class BagType(str, Enum):
    carry_on = "Carry-on"
    checked = "Checked"


class BoundingBox(BaseModel):
    x_min: Optional[float] = None
    y_min: Optional[float] = None
    x_max: Optional[float] = None
    y_max: Optional[float] = None

    @model_validator(mode="after")
    def validate_coordinates(self):
        """Validate that all coordinates are present and valid."""
        if (
            self.x_min is None
            or self.y_min is None
            or self.x_max is None
            or self.y_max is None
        ):
            raise ValueError(
                "All bounding box coordinates (x_min, y_min, x_max, y_max) must be provided"
            )
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
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    bounding_boxes: List[BoundingBox]
    dimensions: Dimensions


class Item(BaseModel):
    item_id: str = Field(default_factory=lambda: str(uuid4()))
    item_importance: Optional[int] = 0
    weight_kg: Optional[float] = None
    estimated_volume_cm3: Optional[float] = None
    cv_result: Optional[CVResult] = None
    price_at_origin: Optional[float] = None
    price_at_destination: Optional[float] = None
    quantity: int = 1
    trips: List[str] = Field(default_factory=list, description="Trip IDs")


class ItemUpdate(BaseModel):
    item_importance: Optional[int] = 0
    weight_kg: Optional[float] = None
    estimated_volume_cm3: Optional[float] = None
    cv_result: Optional[CVResult] = None
    quantity: Optional[int] = None
    price_at_origin: Optional[float] = None
    price_at_destination: Optional[float] = None


class DetectResponse(BaseModel):
    item: Item
    cv_candidates: List[CVResult]
    annotated_image: Optional[str] = None


class ItemPriceResult(BaseModel):
    item_name: str
    source: str
    price: float
    currency: Optional[str] = None


class RecommendedItem(BaseModel):
    item_name: str
    reason: Optional[str] = None
    priority: Optional[int] = None


class RemovalRecommendationStatus(str, Enum):
    pack = "pack"
    remove = "remove"
    swap = "swap"


class RemovalRecommendationReason(str, Enum):
    overweight = "Luggage is too heavy!"
    over_volume = "Luggage is over volume!"


class RemovalRecommendation(BaseModel):
    status: RemovalRecommendationStatus
    reason: Optional[RemovalRecommendationReason] = None
    swap_candidates: Optional[List[Item]] = None

    class Config:
        use_enum_values = True


class Location(BaseModel):
    city: str
    state: Optional[str] = None
    country: str
    airport_code: str = Field(..., min_length=3, max_length=3)

    @field_validator("airport_code")
    @classmethod
    def validate_airport_code(cls, value: str) -> str:
        airport_code = value.strip().upper()
        if not airport_code.isalpha() or len(airport_code) != 3:
            raise ValueError("airport_code must be exactly 3 letters")
        return airport_code


class Trip(BaseModel):
    trip_id: str = Field(default_factory=lambda: str(uuid4()))
    origin_details: Location
    destination_details: Location
    start_date: datetime.datetime
    end_date: datetime.datetime
    highest_temp: Optional[float] = None
    lowest_temp: Optional[float] = None
    precipitation_percentage: Optional[float] = None
    doing_laundry: bool
    bag_type: BagType
    airline: Airline
    # probably going to create a map for this internal field?
    # airline_type: Optional[AirlineType] = AirlineType.budget
    activities: List[Activity] = Field(default_factory=list)
    items: List[str] = Field(default_factory=list, description="Item IDs")
    total_items_weight: float = 0.0
    total_items_volume: float = 0.0

    @computed_field
    @property
    def duration_days(self) -> int:
        return (self.end_date - self.start_date).days + 1

    class Config:
        use_enum_values = True


class TripUpdate(BaseModel):
    origin_details: Optional[Location] = None
    destination_details: Optional[Location] = None
    duration_days: Optional[int] = None
    start_date: Optional[datetime.datetime] = None
    end_date: Optional[datetime.datetime] = None
    doing_laundry: Optional[bool] = None
    activities: Optional[List[Activity]] = None
    bag_type: Optional[BagType] = None
    airline: Optional[Airline] = None
    items: Optional[List[str]] = None


class Gender(str, Enum):
    male = "male"
    female = "female"
    non_binary = "non-binary"
    other = "other"
    prefer_not_to_disclose = "prefer not to disclose"


class User(BaseModel):
    user_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    email: str
    password: str
    age: Optional[int] = None
    gender: Optional[Gender] = None
    trips: List[str] = Field(default_factory=list, description="Trip IDs")
