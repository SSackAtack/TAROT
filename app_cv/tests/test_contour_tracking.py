import unittest

from tarotvision.contour_tracking import assign_boxes_to_cards


class ContourTrackingTest(unittest.TestCase):
    def test_assigns_candidate_to_best_overlapping_card(self):
        tracked = {
            "00_fool": (10, 10, 50, 80),
            "01_magician": (200, 10, 50, 80),
        }
        candidates = [(12, 12, 50, 80)]

        assignments = assign_boxes_to_cards(tracked, candidates, min_iou=0.5)

        self.assertEqual(assignments, {"00_fool": (12, 12, 50, 80)})

    def test_ignores_candidate_with_low_overlap(self):
        tracked = {"00_fool": (10, 10, 50, 80)}
        candidates = [(200, 200, 50, 80)]

        assignments = assign_boxes_to_cards(tracked, candidates, min_iou=0.5)

        self.assertEqual(assignments, {})


if __name__ == "__main__":
    unittest.main()
