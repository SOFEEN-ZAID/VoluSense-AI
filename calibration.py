
import cv2
import numpy as np
import argparse
from pathlib import Path


def detect_checkerboard(img, board_size):

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    clahe = cv2.createCLAHE(
        clipLimit=2.0, tileGridSize=(8, 8)
    )

    images = [
        gray,
        cv2.equalizeHist(gray),
        img[:, :, 2],
        clahe.apply(gray)
    ]

    flags_list = [
        cv2.CALIB_CB_NORMALIZE_IMAGE,

        cv2.CALIB_CB_NORMALIZE_IMAGE |
        cv2.CALIB_CB_EXHAUSTIVE |
        cv2.CALIB_CB_ACCURACY
    ]

    for image in images:

        for flags in flags_list:

            found, corners = cv2.findChessboardCornersSB(
                image, board_size, flags
            )

            if found:
                return True, corners

    return False, None


def calibrate(left_folder, right_folder,
              square_size, columns, rows):

    board_size = (columns, rows)

    objp = np.zeros(
        (rows * columns, 3), np.float32
    )

    objp[:, :2] = np.mgrid[
        0:columns, 0:rows
    ].T.reshape(-1, 2)

    objp *= square_size

    objpoints = []
    imgpoints_left = []
    imgpoints_right = []

    left_images = sorted(
        Path(left_folder).glob("*.jpg")
    )

    image_size = None

    print("Starting calibration...\n")

    for left_path in left_images:

        right_path = Path(right_folder) / left_path.name

        print("Processing:", left_path.name)

        left_img = cv2.imread(str(left_path))
        right_img = cv2.imread(str(right_path))

        if left_img is None or right_img is None:
            print("Missing image:", left_path.name)
            continue

        if left_img.shape[:2] != right_img.shape[:2]:
            print("Image dimensions do not match")
            continue

        current_size = (
            left_img.shape[1],
            left_img.shape[0]
        )

        if image_size is not None and current_size != image_size:
            print("Different image resolution")
            continue

        found_left, corners_left = detect_checkerboard(
            left_img, board_size
        )

        found_right, corners_right = detect_checkerboard(
            right_img, board_size
        )

        if found_left and found_right:

            image_size = current_size

            objpoints.append(objp.copy())
            imgpoints_left.append(corners_left)
            imgpoints_right.append(corners_right)

            print("Accepted:", left_path.name)

        else:

            print(
                "Checkerboard not detected:",
                left_path.name,
                "| Left:", found_left,
                "| Right:", found_right
            )

    print("\nValid matching pairs:", len(objpoints))

    if len(objpoints) < 8:
        print("ERROR: At least 8 valid pairs are required.")
        return

    print("\nCalibrating left camera...")

    ret_left, mtx_left, dist_left, _, _ = (
        cv2.calibrateCamera(
            objpoints,
            imgpoints_left,
            image_size,
            None,
            None
        )
    )

    print("Calibrating right camera...")

    ret_right, mtx_right, dist_right, _, _ = (
        cv2.calibrateCamera(
            objpoints,
            imgpoints_right,
            image_size,
            None,
            None
        )
    )

    criteria = (
        cv2.TERM_CRITERIA_EPS +
        cv2.TERM_CRITERIA_MAX_ITER,
        100,
        1e-6
    )

    print("Performing stereo calibration...")

    ret, mtx_left, dist_left, mtx_right, dist_right, R, T, E, F = (
        cv2.stereoCalibrate(
            objpoints,
            imgpoints_left,
            imgpoints_right,
            mtx_left,
            dist_left,
            mtx_right,
            dist_right,
            image_size,
            criteria=criteria,
            flags=cv2.CALIB_FIX_INTRINSIC
        )
    )

    R1, R2, P1, P2, Q, roi1, roi2 = (
        cv2.stereoRectify(
            mtx_left,
            dist_left,
            mtx_right,
            dist_right,
            image_size,
            R,
            T
        )
    )

    Path("calibration").mkdir(exist_ok=True)

    np.savez(
        "calibration/stereo_calibration.npz",
        mtx_left=mtx_left,
        dist_left=dist_left,
        mtx_right=mtx_right,
        dist_right=dist_right,
        R=R,
        T=T,
        E=E,
        F=F,
        R1=R1,
        R2=R2,
        P1=P1,
        P2=P2,
        Q=Q,
        image_size=image_size
    )

    print("\nCalibration completed!")
    print("Left camera error:", ret_left)
    print("Right camera error:", ret_right)
    print("Stereo calibration error:", ret)
    print("Saved: calibration/stereo_calibration.npz")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument("--left", required=True)
    parser.add_argument("--right", required=True)
    parser.add_argument("--square-size", type=float, default=2.5)
    parser.add_argument("--columns", type=int, default=9)
    parser.add_argument("--rows", type=int, default=6)

    args = parser.parse_args()

    calibrate(
        args.left,
        args.right,
        args.square_size,
        args.columns,
        args.rows
    )
