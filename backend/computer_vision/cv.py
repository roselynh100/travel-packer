import cv2
import numpy as np
from ultralytics import YOLO
# from backend.app.models import CVResult, BoundingBox, Dimensions
from typing import Tuple
from cv2 import aruco

def bytes_to_numpy(image_bytes: bytes):
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

def detect_objects_yolo(image_bytes: bytes):
    model = YOLO('yolov5nu.pt')
    img = bytes_to_numpy(image_bytes)
    results = model(img)

    detections_list = []
    for result in results:  # Loop through images (usually one image unless in stream mode)
        for box in result.boxes:  # Loop through detections in the image
            # Extract the necessary data
            coords = box.xyxy.tolist()[0]
            x_min = coords[0]
            y_min = coords[1]
            x_max = coords[2]
            y_max = coords[3]

            confidence = box.conf.item()
            class_id = box.cls.item()
            class_name = model.names[int(class_id)]

            # Create a dictionary for the detection
            detection = {
                "class_name": class_name,
                "class_id": int(class_id),
                "confidence": round(confidence, 2),
                "x_min": round(x_min, 2),
                "y_min": round(y_min, 2),
                "x_max": round(x_max, 2),
                "y_max": round(y_max, 2)
            }
            detections_list.append(detection)

    print(detections_list)

    return detections_list

with open(r"C:\Users\kateh\Desktop\capstone\yolov8-custom-model\code\data\images\train2\000396ae942e8778.jpg", "rb") as image:
  f = image.read()
  b = bytearray(f)

  detect_objects_yolo(b)