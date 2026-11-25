
import numpy as np
from pathlib import Path

path = Path("calibration/stereo_calibration.npz")

with np.load(path) as data:
    calibration = dict(data)

# Preserve the original calibration
np.savez("calibration/backup_calibration.npz", **calibration)

# Add compatible camera matrix names
mapping = {
    "K1": "mtx_left",
    "K2": "mtx_right",
    "D1": "dist_left",
    "D2": "dist_right"
}

for new_key, old_key in mapping.items():
    if old_key in calibration:
        calibration[new_key] = calibration[old_key]

required = ["K1", "K2", "D1", "D2", "R1", "R2", "P1", "P2", "Q"]

missing = [key for key in required if key not in calibration]

if missing:
    print("Missing calibration values:", missing)
else:
    np.savez(path, **calibration)
    print("Calibration fixed successfully!")
    print("Saved:", path)
