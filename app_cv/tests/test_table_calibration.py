import unittest

import numpy as np

from tarotvision.table_calibration import (
    has_required_markers,
    filter_table_markers,
    extract_workspace_corners,
    compute_table_homography,
    TableCalibration,
    INNER_CORNER_INDEX,
)


class HasRequiredMarkersTest(unittest.TestCase):
    def test_all_markers_present(self):
        ids = np.array([[10], [11], [12], [13]], dtype=np.int32)
        self.assertTrue(has_required_markers(ids))

    def test_missing_marker(self):
        ids = np.array([[10], [11], [13]], dtype=np.int32)
        self.assertFalse(has_required_markers(ids))

    def test_none_ids(self):
        self.assertFalse(has_required_markers(None))

    def test_empty_ids(self):
        ids = np.array([], dtype=np.int32).reshape(0, 1)
        self.assertFalse(has_required_markers(ids))

    def test_extra_markers_still_valid(self):
        ids = np.array([[10], [11], [12], [13], [20]], dtype=np.int32)
        self.assertTrue(has_required_markers(ids))

    def test_filter_table_markers_ignores_card_markers(self):
        ids = np.array([[10], [37], [11], [12], [13]], dtype=np.int32)
        corners = (
            _make_marker_corners(0, 0),
            _make_marker_corners(200, 200),
            _make_marker_corners(100, 0),
            _make_marker_corners(100, 100),
            _make_marker_corners(0, 100),
        )

        filtered_corners, filtered_ids = filter_table_markers(corners, ids)

        self.assertEqual(filtered_ids.reshape(-1).tolist(), [10, 11, 12, 13])
        self.assertEqual(len(filtered_corners), 4)


def _make_marker_corners(tl_x, tl_y, size=50):
    """Helper: build a single marker's corner array in OpenCV format (1, 4, 2).

    OpenCV ArUco corner order: TL, TR, BR, BL of the marker itself.
    """
    return np.array([
        [
            [tl_x, tl_y],
            [tl_x + size, tl_y],
            [tl_x + size, tl_y + size],
            [tl_x, tl_y + size],
        ]
    ], dtype=np.float32)


class ExtractWorkspaceCornersTest(unittest.TestCase):
    def test_extracts_inner_corners(self):
        # Synthetic ArUco corners for 4 markers placed at table corners
        ids = np.array([[10], [11], [12], [13]], dtype=np.int32)
        corners = (
            _make_marker_corners(50, 50, size=50),     # Marker 10 at top-left
            _make_marker_corners(900, 50, size=50),     # Marker 11 at top-right
            _make_marker_corners(900, 600, size=50),    # Marker 12 at bottom-right
            _make_marker_corners(50, 600, size=50),     # Marker 13 at bottom-left
        )

        workspace = extract_workspace_corners(corners, ids)

        # Marker 10 (top-left of table): inner corner = BR of marker (index 2)
        np.testing.assert_array_almost_equal(workspace[10], [100, 100])
        # Marker 11 (top-right of table): inner corner = BL of marker (index 3)
        np.testing.assert_array_almost_equal(workspace[11], [900, 100])
        # Marker 12 (bottom-right of table): inner corner = TL of marker (index 0)
        np.testing.assert_array_almost_equal(workspace[12], [900, 600])
        # Marker 13 (bottom-left of table): inner corner = TR of marker (index 1)
        np.testing.assert_array_almost_equal(workspace[13], [100, 600])

    def test_handles_markers_in_different_order(self):
        # ArUco detector may return markers in any order
        ids = np.array([[13], [10], [12], [11]], dtype=np.int32)
        corners = (
            _make_marker_corners(50, 600, size=50),     # Marker 13 (first in this order)
            _make_marker_corners(50, 50, size=50),      # Marker 10
            _make_marker_corners(900, 600, size=50),    # Marker 12
            _make_marker_corners(900, 50, size=50),     # Marker 11
        )

        workspace = extract_workspace_corners(corners, ids)

        np.testing.assert_array_almost_equal(workspace[10], [100, 100])
        np.testing.assert_array_almost_equal(workspace[11], [900, 100])


class ComputeTableHomographyTest(unittest.TestCase):
    def test_returns_3x3_matrix(self):
        workspace_corners = {
            10: np.array([100, 100], dtype=np.float32),
            11: np.array([900, 100], dtype=np.float32),
            12: np.array([900, 600], dtype=np.float32),
            13: np.array([100, 600], dtype=np.float32),
        }

        M = compute_table_homography(workspace_corners, 1280, 720)

        self.assertEqual(M.shape, (3, 3))

    def test_identity_when_corners_match_destination(self):
        # If source corners match destination exactly, homography ~ identity
        workspace_corners = {
            10: np.array([0, 0], dtype=np.float32),
            11: np.array([1280, 0], dtype=np.float32),
            12: np.array([1280, 720], dtype=np.float32),
            13: np.array([0, 720], dtype=np.float32),
        }

        M = compute_table_homography(workspace_corners, 1280, 720)

        identity = np.eye(3, dtype=np.float64)
        np.testing.assert_array_almost_equal(M, identity, decimal=3)

    def test_workspace_inflation_offsets_corners_from_centroid(self):
        try:
            import cv2
        except ImportError:
            self.skipTest("cv2 not available")

        workspace_corners = {
            10: np.array([100, 100], dtype=np.float32),
            11: np.array([900, 100], dtype=np.float32),
            12: np.array([900, 600], dtype=np.float32),
            13: np.array([100, 600], dtype=np.float32),
        }

        # Obliczamy homografię z poszerzeniem o 10%
        M = compute_table_homography(workspace_corners, 1280, 720, workspace_inflate_percent=10.0)

        # Nadmuchane rogi: [60, 75] -> [0, 0], [940, 75] -> [1280, 0], etc.
        test_pts = np.array([
            [60, 75],
            [940, 75],
            [940, 625],
            [60, 625]
        ], dtype=np.float32).reshape(-1, 1, 2)

        warped_pts = cv2.perspectiveTransform(test_pts, M)
        expected_pts = np.array([
            [0, 0],
            [1280, 0],
            [1280, 720],
            [0, 720]
        ], dtype=np.float32).reshape(-1, 1, 2)

        np.testing.assert_array_almost_equal(warped_pts, expected_pts, decimal=1)


class TableCalibrationClassTest(unittest.TestCase):
    def test_not_calibrated_initially(self):
        cal = TableCalibration()
        self.assertFalse(cal.calibrated)
        self.assertIsNone(cal.homography)

    def test_warp_returns_none_when_not_calibrated(self):
        cal = TableCalibration()
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        self.assertIsNone(cal.warp_frame(frame))

    def test_status_dict_format(self):
        cal = TableCalibration()
        status = cal.status()
        self.assertIn("calibrated", status)
        self.assertIn("marker_ids", status)
        self.assertFalse(status["calibrated"])


if __name__ == "__main__":
    unittest.main()
