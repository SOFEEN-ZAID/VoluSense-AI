
import cv2
import numpy as np
from scipy.spatial import ConvexHull, QhullError

def estimate_volume(left_img, right_img, calibration):
    required = [
        "K1", "D1", "K2", "D2",
        "R1", "R2", "P1", "P2", "Q"
    ]

    for key in required:
        if key not in calibration:
            raise ValueError(f"Calibration is missing {key}")

    height, width = left_img.shape[:2]

    if right_img.shape[:2] != (height, width):
        raise ValueError("Left and right images must have equal dimensions.")

    saved_size = tuple(
        int(x) for x in calibration["image_size"]
    )

    if (width, height) != saved_size:
        raise ValueError(
            f"Images must be {saved_size[0]}x{saved_size[1]} pixels. "
            "Capture images using the calibration resolution."
        )

    map_l1, map_l2 = cv2.initUndistortRectifyMap(
        calibration["K1"], calibration["D1"],
        calibration["R1"], calibration["P1"],
        (width, height), cv2.CV_32FC1
    )

    map_r1, map_r2 = cv2.initUndistortRectifyMap(
        calibration["K2"], calibration["D2"],
        calibration["R2"], calibration["P2"],
        (width, height), cv2.CV_32FC1
    )

    left_rect = cv2.remap(
        left_img, map_l1, map_l2, cv2.INTER_LINEAR
    )
    right_rect = cv2.remap(
        right_img, map_r1, map_r2, cv2.INTER_LINEAR
    )

    gray_left = cv2.cvtColor(left_rect, cv2.COLOR_BGR2GRAY)
    gray_right = cv2.cvtColor(right_rect, cv2.COLOR_BGR2GRAY)

    matcher = cv2.StereoSGBM_create(
        minDisparity=0,
        numDisparities=128,
        blockSize=5,
        P1=8 * 5 * 5,
        P2=32 * 5 * 5,
        disp12MaxDiff=1,
        uniquenessRatio=10,
        speckleWindowSize=100,
        speckleRange=2
    )

    disparity = matcher.compute(
        gray_left, gray_right
    ).astype(np.float32) / 16.0

    points_3d = cv2.reprojectImageTo3D(
        disparity, calibration["Q"]
    )

    # GrabCut: assumes the object is near the image centre
    mask = np.zeros((height, width), np.uint8)
    background_model = np.zeros((1, 65), np.float64)
    foreground_model = np.zeros((1, 65), np.float64)

    margin_x = int(width * 0.12)
    margin_y = int(height * 0.12)

    rectangle = (
        margin_x,
        margin_y,
        width - 2 * margin_x,
        height - 2 * margin_y
    )

    cv2.grabCut(
        left_rect,
        mask,
        rectangle,
        background_model,
        foreground_model,
        5,
        cv2.GC_INIT_WITH_RECT
    )

    object_mask = np.where(
        (mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD),
        255, 0
    ).astype(np.uint8)

    valid = (
        (disparity > 1) &
        (object_mask > 0) &
        np.isfinite(points_3d).all(axis=2) &
        (points_3d[:, :, 2] > 0)
    )

    cloud = points_3d[valid]

    if len(cloud) < 100:
        raise ValueError(
            "Not enough valid 3D points. Check calibration, "
            "image quality and object visibility."
        )

    # Remove extreme depth outliers
    depth = cloud[:, 2]
    low, high = np.percentile(depth, [2, 98])
    cloud = cloud[(depth >= low) & (depth <= high)]

    if len(cloud) < 100:
        raise ValueError("Too few 3D points after filtering.")

    # Limit the number of points used for the hull
    if len(cloud) > 20000:
        indexes = np.random.choice(
            len(cloud), 20000, replace=False
        )
        cloud = cloud[indexes]

    try:
        hull = ConvexHull(cloud)
    except QhullError as error:
        raise ValueError(
            "Could not create a 3D hull. Try better images."
        ) from error

    # Calibration square size was entered in centimetres.
    volume_cm3 = float(hull.volume)

    return {
        "volume": volume_cm3,
        "cloud": cloud,
        "disparity": disparity,
        "object_mask": object_mask,
        "left_rect": left_rect,
        "right_rect": right_rect
    }
