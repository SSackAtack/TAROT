import unittest

from tarotvision.roi_map import filter_boxes_outside_occupied, inflate_box


class RoiMapTest(unittest.TestCase):
    def test_inflate_box_expands_each_side(self):
        self.assertEqual(inflate_box((10, 20, 30, 40), 5), (5, 15, 40, 50))

    def test_filters_candidate_overlapping_occupied_box(self):
        candidates = [(0, 0, 10, 10), (100, 100, 20, 20)]
        occupied = [(0, 0, 12, 12)]

        result = filter_boxes_outside_occupied(candidates, occupied, max_iou=0.1)

        self.assertEqual(result, [(100, 100, 20, 20)])


if __name__ == "__main__":
    unittest.main()
