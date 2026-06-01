import cv2
import numpy as np


class BackgroundModel:
    def __init__(self):
        self._gray_background = None

    @property
    def active(self):
        return self._gray_background is not None

    def capture(self, frame):
        arr = np.asarray(frame)
        if arr.ndim == 2:
            gray = arr
        else:
            gray = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)
        self._gray_background = gray.copy()

    def clear(self):
        self._gray_background = None

    def foreground_mask(self, frame, threshold=18):
        if self._gray_background is None:
            return None
        arr = np.asarray(frame)
        if arr.ndim == 2:
            gray = arr
        else:
            gray = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)
        if gray.shape != self._gray_background.shape:
            return None
        diff = cv2.absdiff(self._gray_background, gray)
        _, mask = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)
        kernel = np.ones((5, 5), dtype=np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        return mask
