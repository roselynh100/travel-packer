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
            dimensions=Dimensions(width=1.0, length=1.0, height=None),
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

    return detections_list


def detect_object_dimensions(image_bytes: bytes, bounding_box: BoundingBox) -> Dimensions:
    # Constants based on the marker I chose
    physical_marker_cm = 5.0
    marker_id = 2

    img = bytes_to_numpy(image_bytes)

    # Converting image to black and white for contrast
    greyscale = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Detect marker 
    aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
    detector = aruco.ArucoDetector(aruco_dict)
    corners, ids, _ = detector.detectMarkers(greyscale)

    # Default fallback for debugging (large dimension will indicate marker wasn't detected)
    px_per_cm = 1.0

    # Check marker against dictionary
    if ids is not None:
        marker_corners = next(
            (corners[i][0] for i, id_ in enumerate(ids) if id_[0] == marker_id), None
        )
        if marker_corners is not None:
            marker_width_px = np.linalg.norm(marker_corners[0] - marker_corners[1])
            px_per_cm = marker_width_px / physical_marker_cm

    # Taking in bounding box coordinates
    width_px = bounding_box.x_max - bounding_box.x_min
    length_px = bounding_box.y_max - bounding_box.y_min

    # Calculate dimensions
    return Dimensions(
        width = round(width_px / px_per_cm, 2),
        length = round(length_px / px_per_cm, 2),
        height = None
    )