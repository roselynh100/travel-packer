import base64
import json
import re
from typing import List, Optional, Tuple

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.models import (
    CVResult,
    DetectResponse,
    Item,
    ItemPriceComparisonResult,
    ItemPriceResult,
    ItemUpdate,
)
from app.routes.trip import recalculate_trip_totals
from app.state.db import items_store, trips_store
from computer_vision.cv import detect_objects_yolo
from constants import SERPAPI_API_KEY
from hardware.readscale import get_weight
from helpers.trip_helpers import (
    _fetch_price_results,
    _get_country_details,
    _get_exchange_rate,
    _get_item_name,
)

router = APIRouter()

CONFIDENCE_THRESHOLD = 0.5


@router.post("/", response_model=Item)
def create_item(item: Item, trip_id: Optional[str] = Query(None)):
    """Create a new item and optionally associate it with a trip."""
    items_store[item.item_id] = item

    if trip_id:
        if trip_id not in trips_store:
            raise HTTPException(status_code=404, detail="Trip not found")

        trip = trips_store[trip_id]

        if item.item_id not in trip.items:
            trip.items.append(item.item_id)

        if trip_id not in item.trips:
            item.trips.append(trip_id)

        if item.estimated_volume_cm3 is not None or item.weight_kg is not None:
            recalculate_trip_totals(trip_id)

    return item


@router.get("/", response_model=List[Item])
def get_items():
    """Get all items."""
    return list(items_store.values())


@router.get("/{item_id}", response_model=Item)
def get_item(item_id: str):
    """Get a specific item by ID."""
    if item_id not in items_store:
        raise HTTPException(status_code=404, detail="Item not found")
    return items_store[item_id]


@router.put("/{item_id}", response_model=Item)
def update_item(item_id: str, updated_item: Item):
    """Fully replace an item."""
    if item_id not in items_store:
        raise HTTPException(status_code=404, detail="Item not found")

    updated = updated_item.model_copy(update={"item_id": item_id})
    items_store[item_id] = updated
    return updated


@router.patch("/{item_id}", response_model=Item)
def patch_item(item_id: str, patch: ItemUpdate):
    """Partially update an item."""
    if item_id not in items_store:
        raise HTTPException(status_code=404, detail="Item not found")

    existing = items_store[item_id]
    patch_data = patch.model_dump(exclude_unset=True)

    # Turn json into CVResult object
    if "cv_result" in patch_data and patch_data["cv_result"] is not None:
        patch_data["cv_result"] = CVResult.model_validate(patch_data["cv_result"])

    updated = existing.model_copy(update=patch_data)
    items_store[item_id] = updated

    if {"weight_kg", "estimated_volume_cm3", "quantity"} & set(patch_data.keys()):
        for trip_id in updated.trips:
            if trip_id in trips_store:
                recalculate_trip_totals(trip_id)

    return updated


@router.delete("/{item_id}")
def delete_item(item_id: str):
    """Delete an item and remove it from any trips that reference it."""
    if item_id not in items_store:
        raise HTTPException(status_code=404, detail="Item not found")

    item = items_store[item_id]

    for trip_id in list(item.trips):
        if trip_id in trips_store:
            trip = trips_store[trip_id]

            if item_id in trip.items:
                trip.items.remove(item_id)

            if item.weight_kg is not None or item.estimated_volume_cm3 is not None:
                recalculate_trip_totals(trip_id)

    del items_store[item_id]
    return {"message": "Item deleted successfully"}


@router.post("/weight", response_model=Item)
def read_weight(item_id: Optional[str] = Query(None)):
    """Read weight from the scale and optionally associate with item."""

    result = get_weight()
    result_dict = json.loads(result)

    if "error" in result_dict:
        raise HTTPException(status_code=500, detail=result_dict["error"])

    weight_kg = result_dict.get("total_weight_kg")
    if weight_kg is None:
        raise HTTPException(status_code=500, detail="Failed to get weight reading")

    # create/update an item
    if item_id and item_id in items_store:
        item = items_store[item_id]
        item.weight_kg = weight_kg
        for trip_id in item.trips:
            recalculate_trip_totals(trip_id)
    else:
        # new item
        item = Item(weight_kg=weight_kg)
        items_store[item.item_id] = item

    return item


@router.post("/detect", response_model=DetectResponse)
async def detect_item_from_image(
    image: UploadFile = File(...), item_id: Optional[str] = Query(None)
):
    """Run YOLO detection. Then create or update an item with the highest-confidence result."""

    image_bytes = await image.read()
    cv_results, annotated_image_bytes = detect_objects_yolo(image_bytes)
    if not cv_results:
        raise HTTPException(status_code=500, detail="Invalid YOLO output")

    annotated_image = (
        base64.standard_b64encode(annotated_image_bytes).decode("ascii")
        if annotated_image_bytes
        else None
    )

    # Sort by confidence (highest first)
    cv_results_sorted = sorted(
        cv_results, key=lambda r: r.confidence_score, reverse=True
    )
    primary_result = cv_results_sorted[0]

    volume = 0
    if primary_result.dimensions:
        volume = (
            primary_result.dimensions.length
            * primary_result.dimensions.width
            * primary_result.dimensions.height
        )

    if item_id and item_id in items_store:
        item = items_store[item_id]
        item.cv_result = primary_result
        item.estimated_volume_cm3 = volume
        for trip_id in item.trips:
            recalculate_trip_totals(trip_id)
    else:
        item = Item(cv_result=primary_result, estimated_volume_cm3=volume)
        items_store[item.item_id] = item

    return DetectResponse(
        item=item,
        annotated_image=annotated_image,
    )


@router.get("/{item_id}/price", response_model=List[ItemPriceResult])
def get_item_price(
    item_id: str,
    country: str,
    limit: int = Query(5, ge=1, le=20),
):
    if SERPAPI_API_KEY == "KEY":
        raise HTTPException(status_code=500, detail="SerpAPI key not configured")

    item_name = _get_item_name(item_id)
    country_details = _get_country_details(country)
    return _fetch_price_results(
        item_name,
        country_details["country_code"],
        country_details["currency_code"],
        limit,
        SERPAPI_API_KEY,
    )


@router.get("/{item_id}/price-comparison", response_model=ItemPriceComparisonResult)
def get_item_price_comparison(
    item_id: str,
    origin_country: str,
    destination_country: str,
    limit: int = Query(5, ge=1, le=20),
):
    if SERPAPI_API_KEY == "KEY":
        raise HTTPException(status_code=500, detail="SerpAPI key not configured")

    item_name = _get_item_name(item_id)
    origin = _get_country_details(origin_country)
    destination = _get_country_details(destination_country)

    origin_prices = _fetch_price_results(
        item_name,
        origin["country_code"],
        origin["currency_code"],
        limit,
        SERPAPI_API_KEY,
    )
    destination_prices = _fetch_price_results(
        item_name,
        destination["country_code"],
        destination["currency_code"],
        limit,
        SERPAPI_API_KEY,
    )
    exchange_rate = _get_exchange_rate(
        destination["currency_code"],
        origin["currency_code"],
    )

    destination_prices_in_origin_currency = [
        ItemPriceResult(
            item_name=result.item_name,
            source=result.source,
            price=round(result.price * exchange_rate, 2),
            currency=origin["currency_code"],
        )
        for result in destination_prices
    ]

    return ItemPriceComparisonResult(
        origin_currency=origin["currency_code"],
        destination_currency=destination["currency_code"],
        exchange_rate=exchange_rate,
        origin_prices=origin_prices,
        destination_prices_in_origin_currency=destination_prices_in_origin_currency,
    )
