
import cv2
from pathlib import Path

folders = [
    "dataset/object_left",
    "dataset/object_right"
]

for folder in folders:

    output = Path(folder + "_resized")
    output.mkdir(exist_ok=True)

    for path in Path(folder).iterdir():

        if path.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
            continue

        img = cv2.imread(str(path))

        if img is None:
            continue

        h, w = img.shape[:2]

        if abs(w / h - 960 / 1280) > 0.01:
            print("Aspect ratio mismatch:", path.name)
            continue

        resized = cv2.resize(
            img,
            (960, 1280),
            interpolation=cv2.INTER_AREA
        )

        cv2.imwrite(str(output / path.name), resized)

        print("Resized:", path.name)

print("Processing completed!")
