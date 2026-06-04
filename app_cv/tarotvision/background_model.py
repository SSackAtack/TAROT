import cv2
import numpy as np


class BackgroundModel:
    def __init__(self):
        self._gray_background = None

    @property
    def active(self):
        return self._gray_background is not None

    def capture(self, frame):
        self._gray_background = _to_gray(frame).copy()

    def capture_many(self, frames):
        gray_frames = [_to_gray(frame) for frame in frames if frame is not None]
        if not gray_frames:
            self.clear()
            return
        shape = gray_frames[0].shape
        aligned = [frame for frame in gray_frames if frame.shape == shape]
        if not aligned:
            self.clear()
            return
        stacked = np.stack(aligned, axis=0)
        self._gray_background = np.median(stacked, axis=0).astype(np.uint8)

    def clear(self):
        self._gray_background = None

    def foreground_mask(self, frame, threshold=18):
        if self._gray_background is None:
            return None
        gray = _to_gray(frame)
        if gray.shape != self._gray_background.shape:
            return None
        diff = cv2.absdiff(self._gray_background, gray)
        _, mask = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)
        kernel = np.ones((5, 5), dtype=np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        return mask

    def changed_ratio(self, frame, threshold=18):
        mask = self.foreground_mask(frame, threshold=threshold)
        if mask is None or mask.size == 0:
            return 0.0
        return float(np.count_nonzero(mask)) / float(mask.size)


def _to_gray(frame):
    arr = np.asarray(frame)
    if arr.ndim == 2:
        return arr
    return cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)
