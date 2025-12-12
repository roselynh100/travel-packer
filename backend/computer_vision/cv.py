import os
from datetime import datetime
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


# Debug function that saves image locally
# Can remove later
def debug_test_image(image_bytes: bytes):
    # Verify image format and log info
    print(f"\nReceived image size={len(image_bytes)} bytes, type={type(image_bytes)}")
    print(
        f"First 20 bytes (hex): {image_bytes[:20].hex() if len(image_bytes) >= 20 else image_bytes.hex()}"
    )

    # Check for JPEG signature (FF D8 FF)
    is_jpeg = image_bytes[:3] == b"\xff\xd8\xff"
    # Check for PNG signature (89 50 4E 47)
    is_png = image_bytes[:4] == b"\x89PNG"

    if is_jpeg:
        print(f"Image format: JPEG (detected by magic bytes)")
    elif is_png:
        print(f"Image format: PNG (detected by magic bytes)")
    else:
        print(f"WARNING: Unknown image format")
        print(f"First 20 bytes (hex): {image_bytes[:20].hex()}")

    # Save the raw image bytes to verify it's valid (for debugging)
    try:
        debug_dir = "debug_images"
        os.makedirs(debug_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        extension = "jpg" if is_jpeg else ("png" if is_png else "bin")
        debug_path = os.path.join(debug_dir, f"received_image_{timestamp}.{extension}")

        with open(debug_path, "wb") as f:
            f.write(image_bytes)
        print(f"Saved debug image to: {debug_path}")
    except Exception as e:
        print(f"WARNING: Could not save debug image: {e}")

    print("=== End Image Verification ===\n")
    return


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


def detect_object_dimensions(
    image_bytes: bytes, bounding_box: BoundingBox
) -> Dimensions:
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
        width=round(width_px / px_per_cm, 2),
        length=round(length_px / px_per_cm, 2),
        height=None,
    )
