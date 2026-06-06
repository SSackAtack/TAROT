import unittest

try:
    import cv2
except ModuleNotFoundError:
    cv2 = None

try:
    import numpy as np
except ModuleNotFoundError:
    np = None

if np is not None and cv2 is not None:
    from tarotvision.motion import MotionDetector, MotionMaskCache, MotionMask
else:
    MotionDetector = None
    MotionMaskCache = None
    MotionMask = None


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

    def test_motion_inside_and_outside_mask(self):
        detector = MotionDetector(min_changed_ratio=0.02, settle_frames=2)
        cache = MotionMaskCache()

        # Maska: kwadrat 10x10 w lewym górnym rogu na klatce 100x100
        corners = np.array([[0, 0], [10, 0], [10, 10], [0, 10]], dtype=np.float32)
        mask = cache.update((100, 100), corners)

        self.assertIsNotNone(mask)
        self.assertEqual(mask.area, 121)  # 11x11 pikseli z uwzględnieniem granic w cv2.fillPoly

        first = np.zeros((100, 100), dtype=np.uint8)
        detector.update(first, mask=mask)

        # 1. Ruch poza maską (w prawym dolnym rogu)
        outside_motion = first.copy()
        outside_motion[50:80, 50:80] = 255
        result_outside = detector.update(outside_motion, mask=mask)
        self.assertFalse(result_outside.motion_detected)
        self.assertEqual(result_outside.changed_ratio, 0.0)

        # 2. Ruch wewnątrz masky
        inside_motion = outside_motion.copy()
        inside_motion[2:8, 2:8] = 255  # 36 pikseli zmienionych
        result_inside = detector.update(inside_motion, mask=mask)
        self.assertTrue(result_inside.motion_detected)
        self.assertAlmostEqual(result_inside.changed_ratio, 36.0 / 121.0)

    def test_mask_cache_key_and_rounding(self):
        cache = MotionMaskCache()
        corners_1 = np.array([[0.1, 0.2], [9.9, 0.1], [10.2, 10.3], [0.3, 9.8]], dtype=np.float32)
        corners_2 = np.array([[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0]], dtype=np.float32)

        mask_1 = cache.update((100, 100), corners_1)
        mask_2 = cache.update((100, 100), corners_2)

        # Powinny wskazywać na ten sam obiekt z cache, bo zaokrąglają się do tych samych współrzędnych
        self.assertIs(mask_1, mask_2)

    def test_invalid_mask_fallback(self):
        detector = MotionDetector(min_changed_ratio=0.02, settle_frames=2)
        first = np.zeros((20, 20), dtype=np.uint8)
        detector.update(first)

        # Maska ma zły wymiar (10x10 zamiast 20x20)
        invalid_mask = MotionMask(mask=np.ones((10, 10), dtype=bool), area=100, key=())

        second = first.copy()
        second[0:5, 0:5] = 255  # ruch 25 pikseli, czyli > 2% całego kadru (400 pikseli)

        # Nie powinno rzucić błędu, tylko bezpiecznie zignorować maskę i wykryć ruch
        result = detector.update(second, mask=invalid_mask)
        self.assertTrue(result.motion_detected)

    def test_shape_change_guard(self):
        detector = MotionDetector(min_changed_ratio=0.02, settle_frames=2)
        first = np.zeros((20, 20), dtype=np.uint8)
        detector.update(first)

        # Zmiana rozdzielczości
        second = np.zeros((30, 30), dtype=np.uint8)
        result = detector.update(second)

        # Powinno bezpiecznie zresetować klatkę referencyjną i nie wykryć ruchu
        self.assertFalse(result.motion_detected)
        self.assertEqual(detector.previous_gray.shape, (30, 30))


if __name__ == "__main__":
    unittest.main()
