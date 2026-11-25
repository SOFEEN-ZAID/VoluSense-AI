
import cv2

path = "dataset/right/right_resized/pair03.jpg"

img = cv2.imread(path)

if img is None:
    print("Image not found!")
    exit()

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

images = {
    "Normal": gray,
    "Enhanced": cv2.equalizeHist(gray),
    "Red channel": img[:, :, 2]
}

patterns = [
    (9, 6),
    (8, 6),
    (9, 5),
    (8, 5),
    (10, 7),
    (7, 5),
    (6, 9)
]

for name, image in images.items():
    for pattern in patterns:

        found, corners = cv2.findChessboardCornersSB(
            image,
            pattern,
            cv2.CALIB_CB_NORMALIZE_IMAGE
        )

        print(name, pattern, ":", found)

        if found:
            print("CHECKERBOARD DETECTED!")
            print("Columns:", pattern[0])
            print("Rows:", pattern[1])

            cv2.drawChessboardCorners(
                img, pattern, corners, found
            )

            cv2.imshow("Detected Checkerboard", img)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            exit()

print("No checkerboard detected.")
