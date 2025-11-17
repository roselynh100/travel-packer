def detect_objects_yolo(image_bytes: bytes):
    """Mock YOLO detection function for testing."""
    # TO-DO: replace with actual yolo related code later
    return {
        "item_name": "Water Bottle",
        "class": "bottle",
        "confidence_score": 0.92,
        "bounding_boxes": [
            [120.5, 80.2, 300.1, 600.9],   # x_min, y_min, x_max, y_max
        ]
    }