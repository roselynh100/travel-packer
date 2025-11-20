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
    model = YOLO("yolov5nu.pt")
    img = bytes_to_numpy(image_bytes)
    results = model(img)

    detections_list = []

    # YOLO returns a list, but we only pass one image, so we'll only get one result
    result = results[0]

    # Exit early if no boxes (items detected)
    # Either something failed (we need to account for this) or we're just testing bad images
    if result.boxes is None or len(result.boxes) == 0:
        example = CVResult(
            item_name="Water Bottle",
            class_name="bottle",
            confidence_score=0.92,
            bounding_boxes=[
                BoundingBox(x_min=120.5, y_min=80.2, x_max=300.1, y_max=600.9)
            ],
            dimensions=Dimensions(length=1.0, width=1.0, height=None),
        )

        detections_list.append(example)

    else:
        # Loop through detections in the image
        for box in result.boxes:
            # Extract the necessary data
            coords = box.xyxy.tolist()[0]
            x_min = round(coords[0], 2)
            y_min = round(coords[1], 2)
            x_max = round(coords[2], 2)
            y_max = round(coords[3], 2)

            confidence = box.conf.item()
            class_id = box.cls.item()
            class_name = model.names[int(class_id)]

            bounding_box = BoundingBox(
                x_min=x_min,
                y_min=y_min,
                x_max=x_max,
                y_max=y_max,
            )

            length, width = detect_object_dimensions(image_bytes, bounding_box)
            dimensions = Dimensions(
                length=length,
                width=width,
                height=None,
            )

            # Create CVResult object
            cv_result = CVResult(
                item_name=class_name,
                class_name=class_name,
                confidence_score=round(confidence, 2),
                bounding_boxes=[bounding_box],
                dimensions=dimensions,
            )

            detections_list.append(cv_result)

    return detections_list


# RACHEL THIS IS WHAT YOU IMPLEMENT
def detect_object_dimensions(
    image_bytes: bytes, bounding_box: BoundingBox
) -> Tuple[float, float]:
    # convert image if needed and determine pixel:cm ratio
    # use pixel:cm ratio to determine the length and width of the object
    # return as a tuple (length, width)
    return (1.0, 1.0)
