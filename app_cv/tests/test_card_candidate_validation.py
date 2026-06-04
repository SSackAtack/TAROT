import unittest

import cv2
import numpy as np

from tarotvision.card_candidate_validation import validate_card_candidate_crop


class CardCandidateValidationTest(unittest.TestCase):
    def test_rejects_smooth_glare_like_crop(self):
        crop = np.full((516, 300), 216, dtype=np.uint8)
        cv2.ellipse(crop, (90, 150), (44, 120), -18, 0, 360, 246, -1)
        crop = cv2.GaussianBlur(crop, (31, 31), 0)

        result = validate_card_candidate_crop(crop)

        self.assertFalse(result.accepted)
        self.assertIn(
            result.reject_reason,
            {"smooth_low_texture", "no_card_border_evidence"},
        )

    def test_accepts_card_like_crop_with_border_and_texture(self):
        crop = np.full((516, 300), 172, dtype=np.uint8)
        cv2.rectangle(crop, (12, 12), (287, 503), 42, 6)
        cv2.rectangle(crop, (32, 42), (268, 478), 108, 3)
        for y in range(78, 462, 42):
            cv2.line(crop, (44, y), (256, y + 22), 72, 2)
        for x in range(72, 250, 34):
            cv2.circle(crop, (x, 250), 16, 60, 2)

        result = validate_card_candidate_crop(crop)

        self.assertTrue(result.accepted, result)


if __name__ == "__main__":
    unittest.main()
