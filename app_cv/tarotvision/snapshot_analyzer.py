from dataclasses import dataclass
import math

import numpy as np

from tarotvision.card_detection_profiles import find_card_quads_multi_profile
from tarotvision.card_recognition import deskew_card_crop


@dataclass(frozen=True)
class SnapshotAnalysisResult:
    cards: list
    card_count: int
    diagnostics: dict | None = None


class SnapshotAnalyzer:
    def __init__(self, find_quads=None, crop_card=None, recognize_crop=None,
                 scene_width=26.0, scene_height=15.6, background_model=None):
        self.find_quads = find_quads or self._find_quads_default
        self.crop_card = crop_card or deskew_card_crop
        self.recognize_crop = recognize_crop
        self.scene_width = scene_width
        self.scene_height = scene_height
        self.background_model = background_model

    def _find_quads_default(self, frame):
        return find_card_quads_multi_profile(frame, background_model=self.background_model).quads

    def analyze(self, frame):
        cards = []
        diagnostics = {
            "quads_found": 0,
            "recognition_attempts": 0,
            "recognition_rejections": 0,
        }
        frame_height, frame_width = frame.shape[:2]
        
        # DIAGNOSTYKA DETEKCJI
        from tarotvision.card_detection_profiles import find_card_quads_multi_profile
        result_multi = find_card_quads_multi_profile(frame, background_model=self.background_model)
        quads = result_multi.quads
        
        try:
            import logging
            import cv2
            import os
            log_dir_env = os.environ.get("TAROTVISION_LOG_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "logs")))
            os.makedirs(log_dir_env, exist_ok=True)
            
            logging.info(f"[DIAGNOSTYKA DETEKCJI] Znalazlem finalnie quads: {len(quads)}")
            for prof in result_multi.debug.get("profiles", []):
                logging.info(f"  - Profil: {prof['name']} | mode: {prof['mode']} | quads: {prof['quads']} | contours: {prof['contours_total']} | candidates: {prof['candidates_after_quad']}")
                
            if self.background_model is not None and self.background_model.active:
                mask = self.background_model.foreground_mask(frame)
                if mask is not None:
                    mask_path = os.path.join(log_dir_env, "debug_mask.jpg")
                    cv2.imwrite(mask_path, mask)
                    logging.info(f"  [OK] Zapisano debug_mask.jpg w {mask_path}")
        except Exception as e:
            pass

        diagnostics["quads_found"] = len(quads)
        for quad in quads:
            crop = self.crop_card(frame, quad)
            diagnostics["recognition_attempts"] += 1
            
            # DIAGNOSTYKA: Zapisz crop na dysku
            import cv2
            import os
            try:
                log_dir_env = os.environ.get("TAROTVISION_LOG_DIR", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "logs")))
                os.makedirs(log_dir_env, exist_ok=True)
                crop_path = os.path.join(log_dir_env, f"debug_crop_{diagnostics['recognition_attempts']}.jpg")
                cv2.imwrite(crop_path, crop)
            except Exception:
                pass
                
            recognition = self.recognize_crop(crop) if self.recognize_crop else None
            if not recognition:
                diagnostics["recognition_rejections"] += 1
                continue
            center_x, center_y = _quad_center(quad)
            scene_x, scene_y = _frame_to_scene(
                center_x,
                center_y,
                frame_width,
                frame_height,
                self.scene_width,
                self.scene_height,
            )
            cards.append({
                "name": recognition["name"],
                "x": scene_x,
                "y": scene_y,
                "angle": _layout_angle(
                    quad,
                    recognition.get("orientation", "unknown"),
                ),
                "confidence": recognition.get("confidence", 0.0),
                "orientation": recognition.get("orientation", "unknown"),
                "homography_angle_deg": recognition.get("homography_angle_deg", 0.0),
            })
        return SnapshotAnalysisResult(
            cards=cards,
            card_count=len(cards),
            diagnostics=diagnostics,
        )


def _quad_points(quad):
    return np.asarray(quad, dtype=np.float32).reshape(4, 2)


def _quad_center(quad):
    points = _quad_points(quad)
    center = np.mean(points, axis=0)
    return float(center[0]), float(center[1])


def _quad_angle(quad):
    points = _order_quad_points(quad)
    top_left = points[0]
    top_right = points[1]
    vector = top_right - top_left
    return -float(np.arctan2(vector[1], vector[0]))


def _layout_angle(quad, orientation):
    angle = _quad_angle(quad)
    if orientation == "reversed":
        angle += math.pi
    return angle


def _order_quad_points(quad):
    points = _quad_points(quad)
    sums = points.sum(axis=1)
    diffs = np.diff(points, axis=1).reshape(4)
    ordered = np.zeros((4, 2), dtype=np.float32)
    ordered[0] = points[np.argmin(sums)]
    ordered[1] = points[np.argmin(diffs)]
    ordered[2] = points[np.argmax(sums)]
    ordered[3] = points[np.argmax(diffs)]
    return ordered


def _frame_to_scene(center_x, center_y, frame_width, frame_height,
                    scene_width, scene_height):
    scene_x = (center_x / frame_width * 2.0 - 1.0) * (scene_width / 2.0)
    scene_y = (1.0 - center_y / frame_height * 2.0) * (scene_height / 2.0)
    return float(scene_x), float(scene_y)
