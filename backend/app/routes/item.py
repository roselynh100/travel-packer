import json
import re
from typing import List, Optional, Tuple

import requests
from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.google_countries import country_info
from app.models import CVResult, Item, ItemPriceResult, ItemUpdate
from app.routes.trip import recalculate_trip_totals
from app.state.db import items_store, trips_store
from computer_vision.cv import detect_objects_yolo
from constants import SERPAPI_API_KEY, SERPAPI_SEARCH_URL
from hardware.readscale import get_weight

router = APIRouter()


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

    updated = existing.model_copy(update=patch_data)
    items_store[item_id] = updated

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


@router.post("/detect", response_model=Item)
async def detect_item_from_image(
    image: UploadFile = File(...), item_id: Optional[str] = Query(None)
):
    """Run YOLO detection, and create an item."""

    image_bytes = await image.read()
    cv_results = detect_objects_yolo(image_bytes)
    if not cv_results:
        raise HTTPException(status_code=500, detail="Invalid YOLO output")

    # assuming cv_results only ever returns result of one item
    cv_result = cv_results[0]

    volume = 0

    # calculate volume for item
    if cv_result.dimensions:
        h = cv_result.dimensions.height or 1
        volume = cv_result.dimensions.length * cv_result.dimensions.width * h

    if item_id and item_id in items_store:
        item = items_store[item_id]
        item.cv_result = cv_result
        item.estimated_volume_cm3 = volume
        for trip_id in item.trips:
            recalculate_trip_totals(trip_id)
    else:
        item = Item(cv_result=cv_result, estimated_volume_cm3=volume)
        # need to store so we can update this item when we read weight
        items_store[item.item_id] = item

    return item


@router.get("/{item_id}/price", response_model=List[ItemPriceResult])
def get_item_price(
    item_id: str,
    country: str,
    limit: int = Query(5, ge=1, le=20),
):
    if SERPAPI_API_KEY == "KEY":
        raise HTTPException(status_code=500, detail="SerpAPI key not configured")

    item = get_item(item_id)
    if not item.cv_result:
        raise HTTPException(
            status_code=404,
            detail="Item has no CV result and name cannot be retrieved",
        )
    class_name = item.cv_result.class_name

    try:
        country_entry = country_info[country.title()]
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Country not found") from exc

    country_code = country_entry.get("country_code")
    currency_code = country_entry.get("currency_code")
    if not country_code or not currency_code:
        raise HTTPException(
            status_code=404,
            detail="Could not retrieve country code or currency code",
        )

    params = {
        "engine": "google_shopping",
        "q": class_name,
        "gl": country_code,
        "hl": "en",
        "api_key": SERPAPI_API_KEY,
    }

    try:
        response = requests.get(SERPAPI_SEARCH_URL, params=params, timeout=15)
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail="SerpAPI request failed") from exc

    if not response.ok:
        raise HTTPException(status_code=502, detail="SerpAPI returned an error")

    try:
        search_results = response.json()
    except ValueError as exc:
        raise HTTPException(
            status_code=502, detail="SerpAPI returned invalid JSON"
        ) from exc

    shopping_results = search_results.get("shopping_results") or []
    results = []

    for entry in shopping_results:
        title = entry.get("title")
        if not title:
            continue

        source = entry.get("source")
        if not source:
            continue

        price = entry.get("extracted_price")

        if price is None:
            continue

        results.append(
            ItemPriceResult(
                item_name=title, source=source, price=price, currency=currency_code
            )
        )

        if len(results) >= limit:
            break

    if not results:
        raise HTTPException(status_code=404, detail="No price results found")

    return results
