from typing import List, Tuple

import cv2
import numpy as np
from cv2 import aruco
from ultralytics import YOLO

from app.models import BoundingBox, CVResult, Dimensions


def bytes_to_numpy(image_bytes: bytes):
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img


def detect_objects_yolo(image_bytes: bytes) -> List[CVResult]:
    model = YOLO("yolov8s.pt")
    img = bytes_to_numpy(image_bytes)
    results = model(
        img,
        conf=0.3,  # Confidence threshold (at least 30% certainty required for a detection)
        imgsz=640,  # Input image size (standard 640x640 for YOLOv8n)
    )

    # Define the list of target class names
    TARGET_CLASSES = {
        "backpack",
        "handbag",
        "suitcase",
        "bottle",
        "laptop",
        "cell phone",
        "book",
        "toothbrush",
    }

    detections_list = []

    # YOLO returns a list, but we only pass one image, so we'll only get one result
    result = results[0]

    # Loop through detections in the image
    for box in result.boxes:
        # Extract the necessary data
        confidence = box.conf.item()
        class_id = box.cls.item()
        class_name = model.names[int(class_id)]

        # filter by class name
        if class_name in TARGET_CLASSES:
            coords = box.xyxy.tolist()[0]
            x_min = round(coords[0], 2)
            y_min = round(coords[1], 2)
            x_max = round(coords[2], 2)
            y_max = round(coords[3], 2)

            bounding_box = BoundingBox(
                x_min=x_min,
                y_min=y_min,
                x_max=x_max,
                y_max=y_max,
            )

            dimensions = detect_object_dimensions(image_bytes, bounding_box)

            # Create CVResult object
            cv_result = CVResult(
                item_name=class_name,
                class_name=class_name,
                confidence_score=round(confidence, 2),
                bounding_boxes=[bounding_box],
                dimensions=dimensions,
            )

            detections_list.append(cv_result)
        # If the class name is not in TARGET_CLASSES, we just skip it

    return detections_list


# RACHEL THIS IS WHAT YOU IMPLEMENT
def detect_object_dimensions(
    image_bytes: bytes, bounding_box: BoundingBox
) -> Dimensions:
    # convert image if needed and determine pixel:cm ratio
    # use pixel:cm ratio to determine the length and width of the object

    # These are placeholder values - need to calculate these numbers
    length = 1.0
    width = 1.0
    height = None

    return Dimensions(length=length, width=width, height=height)
