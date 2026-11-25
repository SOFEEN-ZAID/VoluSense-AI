
from ultralytics import YOLO
from functools import lru_cache


@lru_cache(maxsize=1)
def load_model():
    return YOLO("yolo11n.pt")


def detect_objects(image):

    model = load_model()

    results = model.predict(
        image,
        conf=0.35,
        verbose=False
    )

    detections = []

    for result in results:
        for box in result.boxes:

            class_id = int(box.cls.item())
            confidence = float(box.conf.item())

            detections.append({
                "object": model.names[class_id],
                "confidence": round(confidence * 100, 2),
                "box": box.xyxy[0].tolist()
            })

    annotated_image = results[0].plot()

    return annotated_image, detections
