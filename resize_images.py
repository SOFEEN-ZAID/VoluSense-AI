
import cv2
from pathlib import Path

folders = [
    "dataset/left/left",
    "dataset/right/right"
]

for folder in folders:
    output = Path(folder + "_resized")
    output.mkdir(exist_ok=True)

    for path in Path(folder).glob("*.jpg"):
        img = cv2.imread(str(path))

        if img is not None:
            resized = cv2.resize(
                img, (960, 1280),
                interpolation=cv2.INTER_AREA
            )

            cv2.imwrite(str(output / path.name), resized)
            print("Resized:", path.name)

print("All images resized successfully!")
