import json
from typing import List, Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.models import CVResult, Item, ItemUpdate
from app.state.db import items_store, trips_store
from computer_vision.cv import detect_objects_yolo
from app.models import Item, ItemUpdate
from app.state.db import items_store, trips_store

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

            if item.weight_kg is not None:
                trip.total_items_weight = max(
                    0.0,
                    (trip.total_items_weight or 0.0) - item.weight_kg
                )

            if item.estimated_volume_cm3 is not None:
                trip.total_items_volume = max(
                    0.0,
                    (trip.total_items_volume or 0.0) - item.estimated_volume_cm3
                )

    del items_store[item_id]
    return {"message": "Item deleted successfully"}


@router.post("/weight", response_model=Item)
def read_weight(
    trip_id: str = Query(...),
    item_id: Optional[str] = Query(None)
):
    """Read weight from the scale and associate with item/trip."""
    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")

    result = get_weight(wait_time=6.0)
    result_dict = json.loads(result)

    if "error" in result_dict:
        raise HTTPException(status_code=500, detail=result_dict["error"])

    weight_kg = result_dict.get("total_weight_kg")
    if weight_kg is None:
        raise HTTPException(status_code=500, detail="Failed to get weight reading")

    trip = trips_store[trip_id]

    # create/update an item
    if item_id and item_id in items_store:
        item = items_store[item_id]

        # subtract old weight if it existed
        if item.weight_kg is not None:
            trip.total_items_weight -= item.weight_kg

        # set new weight
        item.weight_kg = weight_kg

    else:
        # new item
        item = Item(
            item_id=item_id,
            weight_kg=weight_kg,
        )
        items_store[item.item_id] = item

    if item.item_id not in trip.items:
        trip.items.append(item.item_id)

    if trip_id not in item.trips:
        item.trips.append(trip_id)

    trip.total_items_weight += weight_kg

    trip.total_items_weight = max(trip.total_items_weight, 0.0)

    return item



@router.post("/detect", response_model=Item)
async def detect_item_from_image(
    image: UploadFile = File(...),
    trip_id: str = Query(...),
    item_id: Optional[str] = Query(None),
):
    """Run YOLO detection, create/update an item, and optionally associate with a trip."""
    if trip_id not in trips_store:
        raise HTTPException(status_code=404, detail="Trip not found")

    image_bytes = await image.read()
    cv_results = detect_objects_yolo(image_bytes)

    if not cv_results:
        raise HTTPException(status_code=500, detail="Invalid YOLO output")

    if item_id and item_id in items_store:
        item = items_store[item_id]
        item.cv_results = cv_results
    else:
        item = Item(item_id=item_id, cv_results=cv_results)
        items_store[item.item_id] = item

    # associate bidirectionally
    trip = trips_store[trip_id]

    if item.item_id not in trip.items:
        trip.items.append(item.item_id)

    if trip_id not in item.trips:
        item.trips.append(trip_id)

    # recalc volume for item
    if cv_results:
        total_volume = 0
        for r in cv_results:
            if r.dimensions:
                h = r.dimensions.height or 1
                total_volume += r.dimensions.length * r.dimensions.width * h
        item.estimated_volume_cm3 = total_volume

    # recalc trip totals
    trip.total_items_volume = sum(
        items_store[i].estimated_volume_cm3 or 0.0 for i in trip.items
    )

    return item
