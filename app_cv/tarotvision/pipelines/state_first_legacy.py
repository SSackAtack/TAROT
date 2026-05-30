# -*- coding: utf-8 -*-
"""
Moduł rurociągu Legacy State-First (StateFirstLegacyPipeline) TarotVision.
"""
import time
import math
import logging
import cv2
import numpy as np

from tarotvision.pipelines.base import VisionPipeline
from tarotvision.matching_schedule import choose_cards_to_match, get_schedule_mode
from tarotvision.motion import MotionDetector
from tarotvision.audit_policy import should_reverify
from tarotvision.table_state import PHASE_LOCKED, PHASE_NEEDS_REVERIFY
from tarotvision.roi_map import filter_boxes_outside_occupied
from tarotvision.contour_tracking import assign_boxes_to_cards

class StateFirstLegacyPipeline(VisionPipeline):
    def __init__(
        self,
        camera_session,
        opencv_preview,
        status_store,
        diagnostics_writer,
        table_calibration,
        table_state,
        runtime_metrics,
        runtime_config,
        build_operator_snapshot_fn,
        operator_warnings,
        log_dir,
        reference_cards,
        orb,
        flann,
        clahe,
        runtime_profile="default"
    ):
        self.camera_session = camera_session
        self.opencv_preview = opencv_preview
        self.status_store = status_store
        self.diagnostics_writer = diagnostics_writer
        self.table_calibration = table_calibration
        self.table_state = table_state
        self.runtime_metrics = runtime_metrics
        self.runtime_config = runtime_config
        self.build_operator_snapshot_fn = build_operator_snapshot_fn
        self.operator_warnings = operator_warnings
        self.log_dir = log_dir
        self.reference_cards = reference_cards
        self.orb = orb
        self.flann = flann
        self.clahe = clahe
        self.runtime_profile = runtime_profile

        # Zmienne stanu rurociągu
        self.debounce_state = {}
        self.inactive_index = 0
        self.prev_time = time.time()
        self.last_diagnostics_time = 0.0
        self.frame_counter = 0
        self.boost_frames_remaining = 0
        self.previous_active_card_names = set()
        self.motion_detector = MotionDetector(min_changed_ratio=0.02, settle_frames=2)
        self.tracked_boxes_by_name = {}

        # Parametry detekcji i śledzenia
        self.lock_after_frames = 8
        self.lock_dead_zone_pos = 3.0
        self.lock_dead_zone_angle = 0.5
        self.debounce_frames = 3
        self.loss_frames = 8
        self.inactive_per_frame_empty = 4
        self.inactive_per_frame_active = 2
        self.inactive_per_frame_boost = 3
        self.boost_after_layout_change_frames = 12
        self.reverify_interval_frames = 180
        self.tracking_iou_threshold = 0.35
        self.tracking_reverify_gap_frames = 24
        self.card_aspect_ratio = 1.72
        self.card_aspect_tolerance = 0.65
        self.detection_iou_threshold = 0.35
        self.ema_alpha = 0.4

    def process_frame(self, frame, gray_frame, motion_result, des_frame, kp_frame, frame_width, frame_height, frame_loop_start):
        """
        Przetwarza klatkę w trybie Legacy State-First.
        
        Args:
            frame (numpy.ndarray): Klatka wejściowa BGR z kamery.
            gray_frame (numpy.ndarray): Klatka w odcieniach szarości z aplikowanym CLAHE.
            motion_result (MotionResult): Wynik detektora ruchu.
            des_frame (numpy.ndarray): Deskryptory cech obecnej klatki.
            kp_frame (list): Punkty kluczowe obecnej klatki.
            frame_width (int): Szerokość klatki.
            frame_height (int): Wysokość klatki.
            frame_loop_start (float): Czas rozpoczęcia pętli klatki.
            
        Returns:
            dict: Wynik sterujący orkiestracją pętli głównej.
        """
        self.frame_counter += 1
        config_values = self.runtime_config.values

        # Aktywne, dynamiczne parametry
        min_match_count = int(config_values.get("MIN_MATCH_COUNT", 12.0))
        ratio_thresh = config_values.get("RATIO_THRESH", 0.79)
        min_inlier_ratio = config_values.get("MIN_INLIER_RATIO", 0.25)
        
        # Detekcja ruchu (wynik przekazany z zewnątrz)
        self.runtime_metrics.add("motion_changed_ratio", motion_result.changed_ratio)
        
        if motion_result.scene_settled:
            self.boost_frames_remaining = max(self.boost_frames_remaining, self.boost_after_layout_change_frames)

        # Inicjalizacja list kandydatów
        detection_candidates = []
        detected_this_frame = {}
        
        all_card_names = list(self.reference_cards.keys())
        candidate_card_names = self.table_state.available_card_ids
        
        self.runtime_metrics.add("available_card_count", len(candidate_card_names))
        self.runtime_metrics.add("tracked_card_count", len(self.table_state.cards))
        self.runtime_metrics.add("boost_frames_remaining", self.boost_frames_remaining)

        # --- KROK 1: Contour tracking przed matchingiem ORB ---
        tracked_boxes = {name: box for name, box in self.tracked_boxes_by_name.items() if name in self.table_state.cards}
        locked_tracked_this_frame = {}
        orb_skipped_locked = 0
        tracking_reverify_count = 0

        if gray_frame is not None and tracked_boxes:
            _, thresh = cv2.threshold(gray_frame, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            min_contour_area = frame_width * frame_height * 0.005
            max_contour_area = frame_width * frame_height * 0.5
            contour_boxes = []
            for cnt in contours:
                area = cv2.contourArea(cnt)
                if min_contour_area <= area <= max_contour_area:
                    contour_boxes.append(cv2.boundingRect(cnt))
            
            assigned_tracked = assign_boxes_to_cards(
                tracked_boxes,
                contour_boxes,
                min_iou=self.tracking_iou_threshold,
            )
            self.runtime_metrics.add("tracked_assignments", len(assigned_tracked))
            
            for card_id, matched_box in assigned_tracked.items():
                tracked_card = self.table_state.cards.get(card_id)
                if tracked_card is None:
                    continue
                
                phase = self.debounce_state.get(card_id, {}).get("phase", "DETECTING")
                
                if phase == "LOCKED" and tracked_card.phase == PHASE_LOCKED:
                    tracked_card.last_seen_frame = self.frame_counter
                    orb_skipped_locked += 1
                    
                    bx, by, bw, bh = matched_box
                    cx = bx + bw / 2.0
                    cy = by + bh / 2.0
                    contour_x = float((cx / frame_width * 2.0 - 1.0) * 13.0)
                    contour_y = float((1.0 - (cy / frame_height) * 2.0) * 7.8)

                    locked_tracked_this_frame[card_id] = {
                        "name": card_id,
                        "x": contour_x,
                        "y": contour_y,
                        "angle": self.debounce_state[card_id].get("locked_angle", tracked_card.angle),
                        "count": 0,
                        "inlier_ratio": 1.0,
                        "area": bw * bh,
                        "dst": None,
                        "tracked_by_contour": True,
                    }
                else:
                    tracked_card.last_seen_frame = self.frame_counter
            
            for card_id, tracked_card in self.table_state.cards.items():
                if card_id in assigned_tracked:
                    continue
                if self.frame_counter - tracked_card.last_seen_frame >= self.tracking_reverify_gap_frames:
                    self.table_state.mark_needs_reverify(card_id, "tracking_gap")
                    tracking_reverify_count += 1
        else:
            self.runtime_metrics.add("tracked_assignments", 0)

        self.runtime_metrics.add("tracking_reverify_count", tracking_reverify_count)
        self.runtime_metrics.add("orb_skipped_locked", orb_skipped_locked)

        # --- KROK 2: Budowa listy kart do ORB matchingu ---
        reverify_card_names = [
            card_id for card_id, tracked_card in self.table_state.cards.items()
            if tracked_card.phase == PHASE_NEEDS_REVERIFY
            or should_reverify(
                frame_index=self.frame_counter,
                last_verified_frame=tracked_card.last_seen_frame,
                interval_frames=self.reverify_interval_frames,
                suspicious=False,
            )
        ]
        self.runtime_metrics.add("reverify_due_count", len(reverify_card_names))

        orb_candidate_names = list(dict.fromkeys(candidate_card_names + reverify_card_names))

        active_count = sum(
            1
            for state in self.debounce_state.values()
            if state.get("stable_count", 0) > 0
        )
        schedule_mode = get_schedule_mode(
            active_count=active_count,
            boost_frames_remaining=self.boost_frames_remaining,
            inactive_per_frame_empty=self.inactive_per_frame_empty,
            inactive_per_frame_active=self.inactive_per_frame_active,
            inactive_per_frame_boost=self.inactive_per_frame_boost,
        )
        schedule_mode_name = schedule_mode.name
        inactive_per_frame = schedule_mode.inactive_per_frame
        
        matching_selection = choose_cards_to_match(
            all_card_names=orb_candidate_names,
            debounce_state=self.debounce_state,
            inactive_index=self.inactive_index,
            frame_counter=self.frame_counter,
            locked_refresh_interval=10, # locked_refresh_interval
            inactive_per_frame=inactive_per_frame,
        )
        active_names = matching_selection.active_names
        inactive_names = matching_selection.inactive_names
        self.inactive_index = matching_selection.next_inactive_index
        cards_to_check = matching_selection.names
        self.runtime_metrics.add("cards_checked", len(cards_to_check))

        # --- KROK 3: Matching ORB/FLANN ---
        matching_start = time.perf_counter()
        if des_frame is not None and len(des_frame) > min_match_count:
            for name in cards_to_check:
                ref_data = self.reference_cards.get(name)
                if ref_data is None:
                    continue

                best_orientation_result = None

                for orientation, des_key, kp_key, img_key in [
                    ("upright", "descriptors", "keypoints", "image"),
                    ("reversed", "reversed_descriptors", "reversed_keypoints", "reversed_image"),
                ]:
                    des_ref = ref_data.get(des_key)
                    if des_ref is None:
                        continue

                    try:
                        matches = self.flann.knnMatch(des_ref, des_frame, k=2)
                    except cv2.error:
                        continue

                    good_matches = []
                    for match_pair in matches:
                        if len(match_pair) == 2:
                            m, n = match_pair
                            if m.distance < ratio_thresh * n.distance:
                                good_matches.append(m)

                    if len(good_matches) < min_match_count:
                        if self.frame_counter % 60 == 0:
                            logging.debug(
                                "MATCH_REJECT %s[%s]: good_matches=%d < min=%d (total_raw=%d)",
                                name, orientation, len(good_matches), min_match_count, len(matches)
                            )
                        continue

                    ref_kp = ref_data[kp_key]
                    src_pts = np.float32([ref_kp[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                    dst_pts = np.float32([kp_frame[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

                    M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)

                    if M is None or mask is None:
                        continue

                    inlier_ratio = np.sum(mask) / len(mask)
                    if inlier_ratio < min_inlier_ratio:
                        if self.frame_counter % 60 == 0:
                            logging.debug(
                                "INLIER_REJECT %s[%s]: inlier_ratio=%.3f < min=%.3f (matches=%d)",
                                name, orientation, inlier_ratio, min_inlier_ratio, len(good_matches)
                            )
                        continue

                    ref_img = ref_data[img_key]
                    h, w = ref_img.shape
                    pts = np.float32([[0, 0], [0, h-1], [w-1, h-1], [w-1, 0]]).reshape(-1, 1, 2)
                    dst = cv2.perspectiveTransform(pts, M)

                    is_convex = cv2.isContourConvex(np.int32(dst))
                    area = cv2.contourArea(dst)
                    max_area = frame_width * frame_height * 0.9
                    min_area = frame_width * frame_height * 0.008
                    is_reasonable_size = (min_area <= area <= max_area)

                    if is_convex and is_reasonable_size and self._validate_quadrilateral(dst):
                        score = len(good_matches) * inlier_ratio
                        if best_orientation_result is None or score > best_orientation_result["score"]:
                            cx = float(np.mean(dst[:, 0, 0]))
                            cy = float(np.mean(dst[:, 0, 1]))
                            pos_x = float((cx / frame_width * 2.0 - 1.0) * 13.0)
                            pos_y = float((1.0 - (cy / frame_height) * 2.0) * 7.8)
                            x0, y0 = dst[0][0][0], dst[0][0][1]
                            x3, y3 = dst[3][0][0], dst[3][0][1]
                            angle = -float(math.atan2(y3 - y0, x3 - x0))

                            if orientation == "reversed":
                                angle += math.pi
                                if angle > math.pi:
                                    angle -= 2 * math.pi

                            best_orientation_result = {
                                "name": name,
                                "count": len(good_matches),
                                "inlier_ratio": float(inlier_ratio),
                                "area": float(area),
                                "dst": dst,
                                "x": pos_x,
                                "y": pos_y,
                                "angle": angle,
                                "orientation": orientation,
                                "score": score,
                            }
                        if orientation == "upright":
                            break
                    else:
                        if self.frame_counter % 60 == 0:
                            logging.debug(
                                "GEOM_REJECT %s[%s]: convex=%s size=%s area=%.0f (matches=%d inlier=%.3f)",
                                name, orientation, is_convex, is_reasonable_size, area,
                                len(good_matches), inlier_ratio
                            )

                if best_orientation_result is not None:
                    detection_candidates.append(best_orientation_result)
            
            detected_this_frame = self._deduplicate_detections(detection_candidates)

        # --- KROK 4: Scalenie wyników ORB + contour tracking ---
        for card_id, tracked_data in locked_tracked_this_frame.items():
            if card_id not in detected_this_frame:
                detected_this_frame[card_id] = tracked_data
        self.runtime_metrics.add("locked_tracked_count", len(locked_tracked_this_frame))

        observed_boxes = [
            self._quad_to_box(item["dst"]) for item in detected_this_frame.values()
            if item.get("dst") is not None
        ]
        unoccupied_observed_boxes = filter_boxes_outside_occupied(
            observed_boxes,
            list(tracked_boxes.values()),
            max_iou=0.1,
        )
        self.runtime_metrics.add("unoccupied_observed_boxes", len(unoccupied_observed_boxes))
        self.runtime_metrics.add("matching_ms", (time.perf_counter() - matching_start) * 1000.0)

        # 6. Dwufazowa stabilizacja: DETECTING -> LOCKED
        active_detected_cards = []
        
        for name in self.reference_cards.keys():
            if name not in self.debounce_state:
                self.debounce_state[name] = {
                    "stable_count": 0, 
                    "loss_count": 0,
                    "phase": "DETECTING"
                }
                
            if name in detected_this_frame:
                self.debounce_state[name]["stable_count"] += 1
                self.debounce_state[name]["loss_count"] = 0
                
                new_x = detected_this_frame[name]["x"]
                new_y = detected_this_frame[name]["y"]
                new_angle = detected_this_frame[name]["angle"]
                
                phase = self.debounce_state[name]["phase"]
                
                if phase == "DETECTING":
                    old_x = self.debounce_state[name].get("last_x", new_x)
                    old_y = self.debounce_state[name].get("last_y", new_y)
                    old_angle = self.debounce_state[name].get("last_angle", new_angle)
                    
                    self.debounce_state[name]["last_x"] = self.ema_alpha * new_x + (1 - self.ema_alpha) * old_x
                    self.debounce_state[name]["last_y"] = self.ema_alpha * new_y + (1 - self.ema_alpha) * old_y
                    
                    diff_angle = abs(new_angle - old_angle)
                    if diff_angle > math.pi:
                        diff_angle = 2 * math.pi - diff_angle
                    
                    if diff_angle > 1.0:
                        self.debounce_state[name]["last_angle"] = new_angle
                    else:
                        self.debounce_state[name]["last_angle"] = self.ema_alpha * new_angle + (1 - self.ema_alpha) * old_angle
                    
                    if self.debounce_state[name]["stable_count"] >= self.lock_after_frames:
                        self.debounce_state[name]["phase"] = "LOCKED"
                        self.debounce_state[name]["locked_x"] = self.debounce_state[name]["last_x"]
                        self.debounce_state[name]["locked_y"] = self.debounce_state[name]["last_y"]
                        self.debounce_state[name]["locked_angle"] = self.debounce_state[name]["last_angle"]
                        
                elif phase == "LOCKED":
                    locked_x = self.debounce_state[name]["locked_x"]
                    locked_y = self.debounce_state[name]["locked_y"]
                    locked_angle = self.debounce_state[name]["locked_angle"]
                    
                    dx = abs(new_x - locked_x)
                    dy = abs(new_y - locked_y)
                    
                    d_angle = abs(new_angle - locked_angle)
                    if d_angle > math.pi:
                        d_angle = 2 * math.pi - d_angle
                    
                    if dx > self.lock_dead_zone_pos or dy > self.lock_dead_zone_pos or d_angle > self.lock_dead_zone_angle:
                        self.debounce_state[name]["phase"] = "DETECTING"
                        self.debounce_state[name]["stable_count"] = 0
                        self.debounce_state[name]["last_x"] = new_x
                        self.debounce_state[name]["last_y"] = new_y
                        self.debounce_state[name]["last_angle"] = new_angle
                        self.boost_frames_remaining = max(self.boost_frames_remaining, self.boost_after_layout_change_frames)
                        self.table_state.mark_needs_reverify(name, "motion_detected")
                        logging.info(f"[RUCH] Karta {name} przesunela sie (dx={dx:.2f}, dy={dy:.2f}). Odblokowanie i zgloszenie do ORB.")
                    else:
                        self.debounce_state[name]["last_x"] = locked_x
                        self.debounce_state[name]["last_y"] = locked_y
                        self.debounce_state[name]["last_angle"] = locked_angle
            elif name in cards_to_check:
                self.debounce_state[name]["loss_count"] += 1
                if self.debounce_state[name]["loss_count"] >= self.loss_frames:
                    self.debounce_state[name]["stable_count"] = 0
                    self.debounce_state[name]["phase"] = "DETECTING"
            else:
                pass
                    
            if self.debounce_state[name]["stable_count"] >= self.debounce_frames:
                active_detected_cards.append({
                    "name": name,
                    "x": round(self.debounce_state[name].get("last_x", 0.0), 4),
                    "y": round(self.debounce_state[name].get("last_y", 0.0), 4),
                    "angle": round(self.debounce_state[name].get("last_angle", 0.0), 4)
                })

        active_card_names = {card["name"] for card in active_detected_cards}
        for card in active_detected_cards:
            self.table_state.upsert_locked(
                card_id=card["name"],
                x=card["x"],
                y=card["y"],
                angle=card["angle"],
                confidence=1.0,
                frame_index=self.frame_counter,
            )
        
        for name in list(self.table_state.cards.keys()):
            if name in self.debounce_state and self.debounce_state[name]["loss_count"] >= self.loss_frames:
                self.table_state.remove_card(name)
                logging.info(f"[USUNIECIE] Karta {name} zniknela ze stolu. Usuniecie ze stanu.")
        
        for name, item in detected_this_frame.items():
            if item.get("dst") is not None:
                self.tracked_boxes_by_name[name] = self._quad_to_box(item["dst"])
        
        newly_active_cards = active_card_names - self.previous_active_card_names
        if newly_active_cards:
            self.boost_frames_remaining = max(self.boost_frames_remaining, self.boost_after_layout_change_frames)
            self.previous_active_card_names = active_card_names
        elif active_card_names != self.previous_active_card_names:
            self.previous_active_card_names = active_card_names
        elif self.boost_frames_remaining > 0:
            self.boost_frames_remaining -= 1
                
        # Aktualizacja statusu
        metrics_snapshot = self.runtime_metrics.snapshot()
        runtime_snapshot = {
            "profile": self.runtime_profile,
            "camera_index": self.camera_session.camera_index,
            "capture_width": frame_width,
            "capture_height": frame_height,
            "camera_focus_locked": self.runtime_config.values.get("CAMERA_FOCUS_LOCKED", False),
            "camera_exposure_locked": self.runtime_config.values.get("CAMERA_EXPOSURE_LOCKED", False)
        }
        runtime_snapshot["schedule_mode"] = schedule_mode_name
        runtime_snapshot["boost_frames_remaining"] = self.boost_frames_remaining
        runtime_snapshot["available_card_count"] = len(self.table_state.available_card_ids)
        runtime_snapshot["tracked_card_count"] = len(self.table_state.cards)
        runtime_snapshot["reverify_interval_frames"] = self.reverify_interval_frames
        runtime_snapshot["tracking_iou_threshold"] = self.tracking_iou_threshold
        runtime_snapshot["table"] = self.table_calibration.status()
        
        status_update_start = time.perf_counter()
        self.status_store.update_cv_state(
            cards=active_detected_cards,
            metrics=metrics_snapshot,
            runtime=runtime_snapshot,
            operator=self.build_operator_snapshot_fn(),
            warnings=list(self.operator_warnings[-8:])
        )
        self.runtime_metrics.add("status_update_ms", (time.perf_counter() - status_update_start) * 1000.0)

        diagnostics_time = time.time()
        if diagnostics_time - self.last_diagnostics_time >= 1.0:
            self.diagnostics_writer.append(metrics_snapshot, runtime_snapshot, active_detected_cards)
            self.last_diagnostics_time = diagnostics_time

        # Rysowanie ramek
        display_frame = frame.copy()
        for name, data in detected_this_frame.items():
            dst = data.get("dst")
            match_count = data["count"]
            is_contour_tracked = data.get("tracked_by_contour", False)
            
            phase = self.debounce_state.get(name, {}).get("phase", "DETECTING")
            
            if is_contour_tracked:
                box_color = (200, 200, 0)
                text_color = (200, 200, 0)
                status_text = "TRACKED"
            elif phase == "LOCKED":
                box_color = (255, 180, 0)
                text_color = (255, 180, 0)
                status_text = "LOCKED"
            else:
                box_color = (0, 255, 0)
                text_color = (0, 0, 255)
                status_text = "DETECTING"
            
            if dst is not None:
                display_frame = cv2.polylines(display_frame, [np.int32(dst)], True, box_color, 3, cv2.LINE_AA)
                top_y = min([pt[0][1] for pt in dst])
                top_x = min([pt[0][0] for pt in dst])
            elif name in self.tracked_boxes_by_name:
                bx, by, bw, bh = self.tracked_boxes_by_name[name]
                cv2.rectangle(display_frame, (bx, by), (bx + bw, by + bh), box_color, 3, cv2.LINE_AA)
                top_y = by
                top_x = bx
            else:
                continue
            
            cv2.putText(display_frame, f"{name.upper()} ({match_count} pkt) [{status_text}]", 
                        (int(top_x), int(top_y) - 10), cv2.FONT_HERSHEY_SIMPLEX, 
                        0.7, text_color, 2, cv2.LINE_AA)

        # FPS i HUD
        current_time = time.time()
        time_diff = current_time - self.prev_time
        fps = 1.0 / time_diff if time_diff > 0 else 0.0
        self.prev_time = current_time
        self.runtime_metrics.add("fps", fps)
        self.runtime_metrics.add("frame_loop_ms", (time.perf_counter() - frame_loop_start) * 1000.0)
        
        aruco_label = "TAK" if self.table_calibration.calibrated else "NIE"
        status_line = f"ORB: {len(cards_to_check)} | IoU: {orb_skipped_locked} | Pula: {len(inactive_names)} | ArUco: {aruco_label}"
        self.opencv_preview.draw_hud(display_frame, fps, status_line)
        self.opencv_preview.show(display_frame)

        key_action = self.opencv_preview.handle_keyboard(self.camera_session)
        
        return {
            "action": key_action if key_action else "continue",
            "frame_width": self.camera_session.frame_width,
            "frame_height": self.camera_session.frame_height
        }

    # --- Prywatne helpery rurociągu legacy ---
    
    def _validate_quadrilateral(self, dst):
        """Walidacja geometryczna czworokąta."""
        p0 = dst[0][0] # Gorny-lewy (TL)
        p1 = dst[1][0] # Dolny-lewy (BL)
        p2 = dst[2][0] # Dolny-prawy (BR)
        p3 = dst[3][0] # Gorny-prawy (TR)
        
        side_left = np.linalg.norm(p1 - p0)
        side_bottom = np.linalg.norm(p2 - p1)
        side_right = np.linalg.norm(p3 - p2)
        side_top = np.linalg.norm(p0 - p3)
        
        if min(side_left, side_bottom, side_right, side_top) < 25.0:
            return False
            
        ratio_lr = side_left / side_right if side_left > side_right else side_right / side_left
        ratio_tb = side_top / side_bottom if side_top > side_bottom else side_bottom / side_top
        
        if ratio_lr > 1.95 or ratio_tb > 1.95:
            return False
            
        def get_cos_angle(a, b, c):
            ba = a - b
            bc = c - b
            norm_ba = np.linalg.norm(ba)
            norm_bc = np.linalg.norm(bc)
            if norm_ba == 0 or norm_bc == 0:
                return 1.0
            return np.dot(ba, bc) / (norm_ba * norm_bc)
            
        cos_0 = abs(get_cos_angle(p3, p0, p1))
        cos_1 = abs(get_cos_angle(p0, p1, p2))
        cos_2 = abs(get_cos_angle(p1, p2, p3))
        cos_3 = abs(get_cos_angle(p2, p3, p0))
        
        MAX_COS = 0.82
        if cos_0 > MAX_COS or cos_1 > MAX_COS or cos_2 > MAX_COS or cos_3 > MAX_COS:
            return False
        
        avg_height = (side_left + side_right) / 2.0
        avg_width = (side_top + side_bottom) / 2.0
        if avg_width > 0:
            detected_ratio = avg_height / avg_width
            if abs(detected_ratio - self.card_aspect_ratio) > self.card_aspect_tolerance:
                return False
            
        return True

    def _polygon_iou(self, poly_a, poly_b):
        """Liczy IoU dwóch wypukłych czworokątów."""
        area_a = cv2.contourArea(poly_a)
        area_b = cv2.contourArea(poly_b)
        if area_a <= 0 or area_b <= 0:
            return 0.0
        
        try:
            intersection_area, _ = cv2.intersectConvexConvex(
                np.float32(poly_a).reshape(-1, 2),
                np.float32(poly_b).reshape(-1, 2)
            )
        except cv2.error:
            return 0.0
        
        union_area = area_a + area_b - intersection_area
        if union_area <= 0:
            return 0.0
        return float(intersection_area / union_area)

    def _deduplicate_detections(self, candidates):
        """Usuwa duplikaty przestrzenne detekcji kart."""
        selected = []
        sorted_candidates = sorted(
            candidates,
            key=lambda item: (item["count"], item["inlier_ratio"], item["area"]),
            reverse=True
        )
        
        for candidate in sorted_candidates:
            overlaps_existing = any(
                self._polygon_iou(candidate["dst"], accepted["dst"]) > self.detection_iou_threshold
                for accepted in selected
            )
            if not overlaps_existing:
                selected.append(candidate)
        
        return {candidate["name"]: candidate for candidate in selected}

    def _quad_to_box(self, quad):
        """Konwertuje quad (4, 1, 2) do boxa (x, y, w, h)."""
        xs = quad[:, 0, 0]
        ys = quad[:, 0, 1]
        x_min = int(np.min(xs))
        y_min = int(np.min(ys))
        x_max = int(np.max(xs))
        y_max = int(np.max(ys))
        return (x_min, y_min, max(1, x_max - x_min), max(1, y_max - y_min))
