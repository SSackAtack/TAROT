"""ArUco-based table calibration for TarotVision.

Uses four ArUco markers (DICT_4X4_50) placed at the corners of the
play-mat to compute a perspective transform.  The warped frame gives
a top-down view of the table workspace, which downstream modules
(card_detection, card_recognition) can use for cleaner contour
detection and crop normalization.

Marker layout (physical mat):
    ID 10 = top-left
    ID 11 = top-right
    ID 12 = bottom-right
    ID 13 = bottom-left

The markers define the *workspace boundary*, not card identities.
"""

import cv2
import numpy as np


# --- Constants ---

# Slownik ArUco — DICT_4X4_50: 50 markerow 4x4, szybki i wystarczajacy dla 4 markerow stolu
ARUCO_DICT = cv2.aruco.DICT_4X4_50

REQUIRED_MARKER_IDS = {10, 11, 12, 13}

MARKER_ID_TOP_LEFT = 10
MARKER_ID_TOP_RIGHT = 11
MARKER_ID_BOTTOM_RIGHT = 12
MARKER_ID_BOTTOM_LEFT = 13

# Defaults for the warped output size.
# Matches the camera capture resolution for easy compositing.
TABLE_WIDTH = 1280
TABLE_HEIGHT = 720

# Which corner of each marker is the "inner" corner pointing toward
# the center of the workspace.
# OpenCV ArUco corner order: 0=TL, 1=TR, 2=BR, 3=BL of the marker.
INNER_CORNER_INDEX = {
    MARKER_ID_TOP_LEFT: 2,      # marker's bottom-right
    MARKER_ID_TOP_RIGHT: 3,     # marker's bottom-left
    MARKER_ID_BOTTOM_RIGHT: 0,  # marker's top-left
    MARKER_ID_BOTTOM_LEFT: 1,   # marker's top-right
}


# --- Pure functions ---

def has_required_markers(ids):
    """Check whether all four required ArUco IDs were detected.

    Args:
        ids: numpy array of shape (N, 1) from cv2.aruco.detectMarkers,
             or None if no markers were found.

    Returns:
        True if IDs 10, 11, 12, 13 are all present.
    """
    if ids is None:
        return False
    present = {int(value) for value in np.asarray(ids).reshape(-1)}
    return REQUIRED_MARKER_IDS.issubset(present)


def extract_workspace_corners(corners, ids):
    """Extract the four inner corners that define the play area.

    For each required marker, picks the corner closest to the table
    center (see INNER_CORNER_INDEX).

    Args:
        corners: tuple of numpy arrays from cv2.aruco.detectMarkers,
                 each with shape (1, 4, 2).
        ids:     numpy array of shape (N, 1) with detected marker IDs.

    Returns:
        dict mapping marker_id -> np.array([x, y], dtype=float32)
    """
    id_to_index = {}
    flat_ids = np.asarray(ids).reshape(-1)
    for idx, marker_id in enumerate(flat_ids):
        mid = int(marker_id)
        if mid in REQUIRED_MARKER_IDS:
            id_to_index[mid] = idx

    workspace = {}
    for marker_id, corner_idx in INNER_CORNER_INDEX.items():
        array_idx = id_to_index[marker_id]
        # corners[array_idx] has shape (1, 4, 2)
        workspace[marker_id] = corners[array_idx][0][corner_idx].copy()

    return workspace


def compute_table_homography(workspace_corners, table_width=TABLE_WIDTH,
                             table_height=TABLE_HEIGHT):
    """Compute a 3x3 perspective transform from workspace corners to a
    top-down rectangle of size (table_width x table_height).

    Args:
        workspace_corners: dict from extract_workspace_corners().
        table_width:  output width in pixels.
        table_height: output height in pixels.

    Returns:
        3x3 numpy matrix suitable for cv2.warpPerspective.
    """
    # Source points: the four inner corners detected in the camera frame
    src = np.array([
        workspace_corners[MARKER_ID_TOP_LEFT],
        workspace_corners[MARKER_ID_TOP_RIGHT],
        workspace_corners[MARKER_ID_BOTTOM_RIGHT],
        workspace_corners[MARKER_ID_BOTTOM_LEFT],
    ], dtype=np.float32)

    # Destination points: a flat rectangle
    dst = np.array([
        [0, 0],
        [table_width, 0],
        [table_width, table_height],
        [0, table_height],
    ], dtype=np.float32)

    return cv2.getPerspectiveTransform(src, dst)


def detect_aruco_markers(gray_frame, detector=None):
    """Detect ArUco markers in a grayscale frame.

    Uses DICT_4X4_50 dictionary (small, fast, sufficient for 4 markers).

    Args:
        gray_frame: single-channel uint8 numpy array.
        detector:   optional pre-created cv2.aruco.ArucoDetector.
                    If None, creates a new one (slower, for backward compat).

    Returns:
        (corners, ids, rejected) — same as cv2.aruco.detectMarkers.
    """
    if detector is None:
        dictionary = cv2.aruco.getPredefinedDictionary(ARUCO_DICT)
        parameters = cv2.aruco.DetectorParameters()
        detector = cv2.aruco.ArucoDetector(dictionary, parameters)
    corners, ids, rejected = detector.detectMarkers(gray_frame)
    return corners, ids, rejected


# --- Stateful wrapper ---

class TableCalibration:
    """Manages per-frame ArUco detection and table perspective warp.

    Once calibrated, skips ArUco detection for `recalibrate_interval`
    frames to save CPU.  The homography is stable as long as the mat
    doesn't move, so re-checking every ~30 frames is plenty.

    Usage in the CV loop::

        calibration = TableCalibration()

        # Each frame:
        calibration.update(gray_frame)
        if calibration.calibrated:
            warped = calibration.warp_frame(bgr_frame)
    """

    def __init__(self, table_width=TABLE_WIDTH, table_height=TABLE_HEIGHT,
                 recalibrate_interval=30):
        self.table_width = table_width
        self.table_height = table_height
        self.recalibrate_interval = recalibrate_interval
        self.homography = None
        self.calibrated = False
        self.detected_marker_ids = []
        self._last_corners = None
        self._last_ids = None
        self._frames_since_detect = 0
        # Cache detector — tworzenie obiektu co klatke jest kosztowne
        self._dictionary = cv2.aruco.getPredefinedDictionary(ARUCO_DICT)
        self._parameters = cv2.aruco.DetectorParameters()
        self._detector = cv2.aruco.ArucoDetector(
            self._dictionary, self._parameters
        )

    def update(self, gray_frame):
        """Detect markers and recompute homography if all 4 are found.

        When already calibrated, skips ArUco detection for
        recalibrate_interval frames to save ~30ms/frame.

        Returns True if calibration is active.
        """
        self._frames_since_detect += 1

        # Jesli juz skalibrowany — pomijamy detekcje przez N klatek
        if (self.calibrated
                and self._frames_since_detect < self.recalibrate_interval):
            return True

        self._frames_since_detect = 0
        corners, ids, _ = detect_aruco_markers(gray_frame, self._detector)

        if ids is not None:
            self.detected_marker_ids = sorted(int(v) for v in ids.reshape(-1))
        else:
            self.detected_marker_ids = []

        if not has_required_markers(ids):
            # Keep the last valid homography if we had one — markers may be
            # temporarily occluded by a hand.  Clear only after prolonged loss.
            return self.calibrated

        self._last_corners = corners
        self._last_ids = ids
        workspace = extract_workspace_corners(corners, ids)
        self.homography = compute_table_homography(
            workspace, self.table_width, self.table_height
        )
        self.calibrated = True
        return True

    def warp_frame(self, frame):
        """Warp a BGR or grayscale frame to the top-down table view.

        Returns None if not calibrated.
        """
        if not self.calibrated or self.homography is None:
            return None
        return cv2.warpPerspective(
            frame, self.homography, (self.table_width, self.table_height)
        )

    def status(self):
        """Return a JSON-serialisable status dict for the WebSocket payload."""
        return {
            "calibrated": self.calibrated,
            "marker_ids": self.detected_marker_ids,
        }
