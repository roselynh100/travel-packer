"hi im kate"

import cv2
import numpy as np
from ultralytics import YOLO
from app.models import CVResult, BoundingBox, Dimensions
from typing import Tuple

def bytes_to_numpy(image_bytes: bytes):
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

def detect_objects_yolo(image_bytes: bytes) -> CVResult:
    """Mock YOLO detection function for testing."""
    # TO-DO: replace with actual yolo related code later
    model = YOLO('yolov8n.pt') 

    img = bytes_to_numpy(image_bytes)
    results = model(img)

    # parse results into an CV result Object (i already imported the pydantic model i created for you)
    # i decided to return the object instead of a json object so that it makes validation easier

    # call detect_object_dimensions with image bytes and bounding_box coordinates
    # the return will be (height, width). add these to the item you just created

    # finally, return the item object

    example = CVResult(
        item_name="Water Bottle",
        class_name="bottle",
        confidence_score=0.92,
        bounding_boxes=[BoundingBox(
            x_min=120.5,
            y_min=80.2,
            x_max=300.1,
            y_max=600.9
        )],
        dimensions=Dimensions(
            length=1.0,
            height=1.0
        ),
    )

    return example

def detect_object_dimensions(image_bytes: bytes, bounding_box: BoundingBox) -> Tuple[float, float]:
    # convert image if needed and determine pixel:cm ratio
    # use pixel:cm ratio to determine the height and width of the object
    # return as a tuple (height, width)
    return (1.0, 1.0)