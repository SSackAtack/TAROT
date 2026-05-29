import unittest

try:
    import cv2  # noqa: F401
except ModuleNotFoundError:
    cv2 = None

try:
    import numpy as np
except ModuleNotFoundError:
    np = None

if np is not None and cv2 is not None:
    from tarotvision.motion import MotionDetector
else:
    MotionDetector = None


@unittest.skipIf(np is None or cv2 is None, "numpy/cv2 is not installed in this environment")
class MotionDetectorTest(unittest.TestCase):
    def test_no_motion_for_identical_frames(self):
        detector = MotionDetector(min_changed_ratio=0.02, settle_frames=2)
        frame = np.zeros((20, 20), dtype=np.uint8)

        detector.update(frame)
        result = detector.update(frame.copy())

        self.assertFalse(result.motion_detected)

    def test_motion_when_enough_pixels_change(self):
        detector = MotionDetector(min_changed_ratio=0.02, settle_frames=2)
        first = np.zeros((20, 20), dtype=np.uint8)
        second = first.copy()
        second[0:10, 0:10] = 255

        detector.update(first)
        result = detector.update(second)

        self.assertTrue(result.motion_detected)

    def test_settled_after_motion_stops(self):
        detector = MotionDetector(min_changed_ratio=0.02, settle_frames=2)
        first = np.zeros((20, 20), dtype=np.uint8)
        moving = first.copy()
        moving[0:10, 0:10] = 255

        detector.update(first)
        detector.update(moving)
        detector.update(moving.copy())
        result = detector.update(moving.copy())

        self.assertTrue(result.scene_settled)


if __name__ == "__main__":
    unittest.main()
