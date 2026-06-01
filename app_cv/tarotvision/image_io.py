import os

import cv2
import numpy as np


def imread_unicode(path, flags=cv2.IMREAD_UNCHANGED):
    if not os.path.exists(path):
        return None
    data = np.fromfile(path, dtype=np.uint8)
    if data.size == 0:
        return None
    return cv2.imdecode(data, flags)


def imread_grayscale_unicode(path):
    return imread_unicode(path, cv2.IMREAD_GRAYSCALE)


def imwrite_unicode(path, image, params=None):
    extension = os.path.splitext(path)[1]
    if not extension:
        return False
    ok, encoded = cv2.imencode(extension, image, params or [])
    if not ok:
        return False
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    encoded.tofile(path)
    return True
