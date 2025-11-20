from fastapi import APIRouter, HTTPException, Query, File, UploadFile
from typing import List, Optional
import json

from hardware.readscale import get_weight
from computer_vision.cv import detect_objects_yolo
from app.models import Item, ItemUpdate, CVResult
from app.state.db import items_store, trips_store

router = APIRouter()

@router.post("/", response_model=Item)
def create_item(item: Item, trip_id: Optional[str] = Query(None)):
    """Create a new item and optionally associate it with a trip."""
    items_store[item.item_id] = item
    
    # Associate item with trip if trip_id provided
    if trip_id:
        if trip_id not in trips_store:
            raise HTTPException(status_code=404, detail="Trip not found")
        if trips_store[trip_id].items is None:
            trips_store[trip_id].items = []
        if item.item_id not in trips_store[trip_id].items:
            trips_store[trip_id].items.append(item.item_id)

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
def update_item(item_id: str, item: Item):
    """Update an item."""
    if item_id not in items_store:
        raise HTTPException(status_code=404, detail="Item not found")

    items_store[item_id] = item.model_copy(update={"item_id": item_id})
    return items_store[item_id]

@router.patch("/{item_id}", response_model=Item)
def patch_item(item_id: str, patch: ItemUpdate):
    if item_id not in items_store:
        raise HTTPException(status_code=404, detail="Item not found")

    item = items_store[item_id]
    patch_data = patch.model_dump(exclude_unset=True)
    updated = item.model_copy(update=patch_data)

    items_store[item_id] = updated
    return updated

@router.delete("/{item_id}")
def delete_item(item_id: str):
    """Delete an item."""
    if item_id not in items_store:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Remove item from trip's items list
    for trip in trips_store.values():
        if trip.items and item_id in trip.items:
            trip.items.remove(item_id)

    del items_store[item_id]
    return {"message": "Item deleted successfully"}


@router.post("/weight")
def read_weight(trip_id: str = Query(...), item_id: Optional[str] = Query(None)):
    """Get weight reading from the scale and optionally associate it with a trip and/or item."""
    result = get_weight(wait_time=6.0)
    result_dict = json.loads(result)

    if "error" in result_dict:
        raise HTTPException(status_code=500, detail=result_dict["error"])

    weight_kg = result_dict["total_weight_kg"]

    if weight_kg is None:
        raise HTTPException(status_code=500, detail="Failed to get weight reading from the scale")
    
    if item_id and item_id in items_store:
        item = items_store[item_id]
        item.weight_kg = weight_kg
    else:
        item = Item(item_id=item_id, weight_kg=weight_kg) if item_id else Item(weight_kg=weight_kg)
        items_store[item.item_id] = item
    
    if trip_id:
        if trip_id not in trips_store:
            raise HTTPException(status_code=404, detail="Trip not found")
        if trips_store[trip_id].items is None:
            trips_store[trip_id].items = []
        if item.item_id not in trips_store[trip_id].items:
            trips_store[trip_id].items.append(item.item_id)

    return {
        "status": "success",
        "item": item.model_dump(),
        "total_weight_kg": weight_kg,
    }

@router.post("/detect", response_model=Item)
async def detect_item_from_image(
    image: UploadFile = File(...),
    trip_id: Optional[str] = Query(None),
    item_id: Optional[str] = Query(None),
):
    """Upload an image, run object detection (YOLO), and create/update an Item and optionally associate it with a trip."""
    image_bytes = await image.read()

    cv_results = detect_objects_yolo(image_bytes)
    if cv_results is None or len(cv_results) == 0:
        raise HTTPException(status_code=500, detail="Invalid YOLO output")

    if item_id and item_id in items_store:
        item = items_store[item_id]
        item.cv_results = cv_results
    else:
        if item_id:
            item = Item(item_id=item_id, cv_results=cv_results)
        else:
            item = Item(cv_results=cv_results)  # item_id will be auto-generated
        items_store[item.item_id] = item

    if trip_id:
        if trip_id not in trips_store:
            raise HTTPException(status_code=404, detail="Trip not found")
        if trips_store[trip_id].items is None:
            trips_store[trip_id].items = []
        if item.item_id not in trips_store[trip_id].items:
            trips_store[trip_id].items.append(item.item_id)

    return item
