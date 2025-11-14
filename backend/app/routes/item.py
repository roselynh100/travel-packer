from fastapi import APIRouter, HTTPException, Query, File, UploadFile
from typing import Dict, List, Optional
import json
from uuid import uuid4

from hardware.readscale import get_weight
from computer_vision.cv import detect_objects_yolo
from app.models import Item, BoundingBox

router = APIRouter()

item_store: Dict[str, Item] = {}  # item_id -> Item


@router.post("/", response_model=Item)
def create_item(item: Item, trip_id: Optional[str] = Query(None)):
    """Create a new item and optionally associate it with a trip."""
    item_store[item.item_id] = item
    
    # Associate item with trip if trip_id provided
    if trip_id:
        from app.routes.trip import trips_store
        if trip_id not in trips_store:
            raise HTTPException(status_code=404, detail="Trip not found")
        if item.item_id not in trips_store[trip_id].items:
            trips_store[trip_id].items.append(item.item_id)
    
    return item


@router.get("/", response_model=List[Item])
def get_items():
    """Get all items."""
    return list[Item](item_store.values())

@router.get("/{item_id}", response_model=Item)
def get_item(item_id: str):
    """Get a specific item by ID."""
    if item_id not in item_store:
        raise HTTPException(status_code=404, detail="Item not found")
    return item_store[item_id]


@router.put("/{item_id}", response_model=Item)
def update_item(item_id: str, item: Item):
    """Update an item."""
    if item_id not in item_store:
        raise HTTPException(status_code=404, detail="Item not found")
    item.item_id = item_id  # Ensure ID matches
    item_store[item_id] = item
    return item


@router.delete("/{item_id}")
def delete_item(item_id: str):
    """Delete an item."""
    if item_id not in item_store:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Remove item from trip's items list
    from app.routes.trip import trips_store
    for trip in trips_store.values():
        if item_id in trip.items:
            trip.items.remove(item_id)
    
    del item_store[item_id]
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
    
    if item_id and item_id in item_store:
        item = item_store[item_id]
        item.weight_kg = weight_kg
    else:
        if item_id is None:
            item = Item(weight_kg=weight_kg)  # item_id will be auto-generated
        else:
            item = Item(item_id=item_id, weight_kg=weight_kg)
        item_store[item.item_id] = item
    
    if trip_id:
        from app.routes.trip import trips_store
        if trip_id not in trips_store:
            raise HTTPException(status_code=404, detail="Trip not found")
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

    try:
        yolo_result = detect_objects_yolo(image_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CV model error: {str(e)}")

    required_fields = ["confidence_score", "bounding_boxes", "class", "item_name"]
    if not all(field in yolo_result for field in required_fields):
        raise HTTPException(
            status_code=500, 
            detail=f"YOLO output missing fields: {yolo_result}"
        )

    confidence = yolo_result["confidence_score"]
    class_name = yolo_result["class"]
    item_name = yolo_result["item_name"]
    bounding_boxes = yolo_result["bounding_boxes"]
    
    # Validate bounding boxes format
    for bb in bounding_boxes:
        if not isinstance(bb, list) or len(bb) != 4:
            raise HTTPException(
                status_code=500,
                detail=f"Invalid bounding box format: {bb}. Expected list of 4 numbers [x_min, y_min, x_max, y_max]"
            )
    
    bounding_boxes: List[BoundingBox] = [
        BoundingBox(
            x_min=bb[0],
            y_min=bb[1],
            x_max=bb[2],
            y_max=bb[3]
        )
        for bb in bounding_boxes
    ]

    if item_id and item_id in item_store:
        item = item_store[item_id]
        item.item_name = item_name
        item.class_name = class_name
        item.confidence = confidence
        item.bounding_boxes = bounding_boxes

    else:
        item = Item(
            item_name=item_name,
            class_name=class_name,
            confidence=confidence,
            bounding_boxes=bounding_boxes,
        )
        item_store[item.item_id] = item

    if trip_id:
        from app.routes.trip import trips_store
        if trip_id not in trips_store:
            raise HTTPException(status_code=404, detail="Trip not found")
        if item.item_id not in trips_store[trip_id].items:
            trips_store[trip_id].items.append(item.item_id)

    return item