import os
from datetime import datetime
from typing import List, Tuple

import cv2
import numpy as np
from cv2 import aruco
from ultralytics import YOLO

from app.models import BoundingBox, CVResult, Dimensions

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
YOLO_MODEL_PATH = os.path.join(BASE_DIR, "model_train", "best.pt")

DEBUG_SAVE_CV_IMAGES = True
DEBUG_IMAGES_DIR = "debug_images"


def bytes_to_numpy(image_bytes: bytes):
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img


def _debug_save_cv_images(image_bytes: bytes, annotated_bytes: bytes) -> None:
    """Save capture + annotated image to debug_images/ when DEBUG_SAVE_CV_IMAGES is True."""
    try:
        os.makedirs(DEBUG_IMAGES_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Capture: detect format for extension (same logic as old debug_test_image)
        is_jpeg = image_bytes[:3] == b"\xff\xd8\xff"
        is_png = image_bytes[:4] == b"\x89PNG"
        capture_ext = "jpg" if is_jpeg else ("png" if is_png else "bin")
        capture_path = os.path.join(
            DEBUG_IMAGES_DIR, f"{timestamp}_capture.{capture_ext}"
        )
        with open(capture_path, "wb") as f:
            f.write(image_bytes)
        print(f"[DEBUG CV] Saved capture: {os.path.abspath(capture_path)}")

        if annotated_bytes:
            annotated_path = os.path.join(
                DEBUG_IMAGES_DIR, f"{timestamp}_annotated.jpg"
            )
            with open(annotated_path, "wb") as f:
                f.write(annotated_bytes)
            print(f"[DEBUG CV] Saved annotated: {os.path.abspath(annotated_path)}")
    except Exception as e:
        print(f"[DEBUG CV] WARNING: Could not save debug images: {e}")


def annotate_image_with_yolo_plot(yolo_result) -> bytes:
    """
    Annotate an image using YOLO's built-in plot() (bounding boxes, labels, confidence).
    Standalone so it can be reused from /detect and from any future re-annotation (e.g. CV correction).
    """
    annotated_img = yolo_result.plot()
    _, jpeg_buffer = cv2.imencode(".jpg", annotated_img)
    return jpeg_buffer.tobytes()


def detect_objects_yolo(image_bytes: bytes) -> Tuple[List[CVResult], bytes]:
    model = YOLO(YOLO_MODEL_PATH)
    img = bytes_to_numpy(image_bytes)
    results = model(
        img,
        conf=0.3,  # Confidence threshold (at least 30% certainty required for a detection)
        imgsz=640,  # Input image size (standard 640x640 for YOLOv8n)
    )

    # Define the list of target class names
    TARGET_CLASSES = {
        "container",
        "electronics",
        "jackets",
        "pants",
        "shoes",
        "shorts",
        "tops",
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
                confidence_score=round(confidence, 2),
                bounding_boxes=[bounding_box],
                dimensions=dimensions,
            )

            detections_list.append(cv_result)
        # If the class name is not in TARGET_CLASSES, we just skip it

    annotated_bytes = annotate_image_with_yolo_plot(result)

    if DEBUG_SAVE_CV_IMAGES:
        _debug_save_cv_images(image_bytes, annotated_bytes)

    return detections_list, annotated_bytes


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
