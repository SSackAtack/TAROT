import json
import os
from datetime import datetime

import cv2
import numpy as np

from tarotvision.image_io import imwrite_unicode


def _timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def draw_quads(frame, quads):
    canvas = frame.copy()
    for index, quad in enumerate(quads):
        points = np.asarray(quad, dtype=np.int32)
        cv2.polylines(canvas, [points], True, (0, 255, 0), 2)
        x, y, _, _ = cv2.boundingRect(points)
        cv2.putText(canvas, str(index), (x, y - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    return canvas


def save_snapshot_debug_artifacts(directory, frame, quads, metadata):
    os.makedirs(directory, exist_ok=True)
    stem = _timestamp()
    raw_path = os.path.join(directory, f"{stem}_raw.jpg")
    overlay_path = os.path.join(directory, f"{stem}_quads.jpg")
    json_path = os.path.join(directory, f"{stem}_metadata.json")

    imwrite_unicode(raw_path, frame)
    imwrite_unicode(overlay_path, draw_quads(frame, quads))
    with open(json_path, "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, ensure_ascii=False, indent=2, sort_keys=True)
    return {
        "raw": raw_path,
        "quads": overlay_path,
        "metadata": json_path,
    }
