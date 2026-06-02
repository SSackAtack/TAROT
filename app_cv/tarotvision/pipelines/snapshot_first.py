# -*- coding: utf-8 -*-
"""
Moduł rurociągu Snapshot-First (SnapshotFirstPipeline) TarotVision.
"""
import time
import numpy as np
from tarotvision.pipelines.base import VisionPipeline
from tarotvision.detection_diagnostics import summarize_detection_diagnostics
from tarotvision.snapshot_quality import choose_best_snapshot

class SnapshotFirstPipeline(VisionPipeline):
    def __init__(
        self,
        camera_session,
        opencv_preview,
        status_store,
        diagnostics_writer,
        snapshot_gate,
        snapshot_analyzer,
        table_calibration,
        runtime_metrics,
        runtime_config,
        build_operator_snapshot_fn,
        operator_warnings,
        log_dir,
        runtime_profile="default",
        autotune_sample_recorder=None,
        change_detector=None,
        background_model=None,
    ):
        self.camera_session = camera_session
        self.opencv_preview = opencv_preview
        self.status_store = status_store
        self.diagnostics_writer = diagnostics_writer
        self.snapshot_gate = snapshot_gate
        self.snapshot_analyzer = snapshot_analyzer
        self.table_calibration = table_calibration
        self.runtime_metrics = runtime_metrics
        self.runtime_config = runtime_config
        self.build_operator_snapshot_fn = build_operator_snapshot_fn
        self.operator_warnings = operator_warnings
        self.log_dir = log_dir
        self.runtime_profile = runtime_profile
        self.autotune_sample_recorder = autotune_sample_recorder
        self.change_detector = change_detector
        self.background_model = background_model

        # Zmienne stanu rurociągu
        self.last_snapshot_cards = []
        self.previous_stable_snapshot = None
        self.snapshot_layout_id = 0
        self.last_motion_started_ms = None
        self.last_diagnostics_time = 0.0
        self.prev_time = time.time()
        self.empty_snapshot_streak = 0
        self.empty_snapshot_clear_threshold = 2

        # Stałe konfiguracyjne snapshotów (pobierane z parametrów)
        self.snapshot_sample_count = 1
        self.snapshot_sample_interval_ms = 250

    def process_frame(self, frame, motion_result, frame_width, frame_height, frame_loop_start):
        """
        Przetwarza klatkę w trybie Snapshot-First.
        
        Args:
            frame (numpy.ndarray): Klatka wejściowa BGR.
            motion_result (MotionResult): Wynik detektora ruchu.
            frame_width (int): Szerokość klatki.
            frame_height (int): Wysokość klatki.
            frame_loop_start (float): Czas startu pętli przetwarzania klatki.
            
        Returns:
            dict: Wynik sterujący orkiestracją pętli głównej.
        """
        now_ms = int(time.time() * 1000)
        if motion_result.motion_detected:
            self.last_motion_started_ms = now_ms

        gate_decision = self.snapshot_gate.update(
            now_ms=now_ms,
            motion_detected=motion_result.motion_detected,
            changed_ratio=motion_result.changed_ratio,
        )
        
        # Inicjalizacja słownika układu
        layout_snapshot = {
            "layout_id": self.snapshot_layout_id,
            "source": "snapshot",
            "state": gate_decision.state,
            "stable_for_ms": gate_decision.stable_for_ms,
        }
        self.runtime_metrics.add("stable_for_ms", gate_decision.stable_for_ms)

        # Wyznaczenie dynamicznego FPS
        current_time = time.time()
        time_diff = current_time - self.prev_time
        fps = 1.0 / time_diff if time_diff > 0 else 0.0
        self.prev_time = current_time
        self.runtime_metrics.add("fps", fps)

        # Pobieranie próbek (sampling)
        if gate_decision.should_sample:
            samples = [frame.copy()]
            key_action = None
            for i in range(self.snapshot_sample_count - 1):
                start_wait = time.perf_counter()
                target_wait = self.snapshot_sample_interval_ms / 1000.0
                last_read_frame = None
                while time.perf_counter() - start_wait < target_wait:
                    ok, temp_frame = self.camera_session.read()
                    if ok:
                        last_read_frame = temp_frame.copy()
                        display_temp = temp_frame.copy()
                        self.opencv_preview.draw_hud(display_temp, fps, f"ZBIERANIE SNAPSHOTA ({i+2}/{self.snapshot_sample_count})...")
                        self.opencv_preview.show(display_temp)
                    key_action = self.opencv_preview.handle_keyboard(self.camera_session)
                    if key_action in ["quit", "switch"]:
                        break
                if key_action in ["quit", "switch"]:
                    break
                if last_read_frame is not None:
                    samples.append(last_read_frame)

            if key_action in ["quit", "switch"]:
                self.snapshot_gate.mark_rejected()
                return {
                    "action": key_action,
                    "frame_width": self.camera_session.frame_width,
                    "frame_height": self.camera_session.frame_height
                }

            self.runtime_metrics.add("snapshot_samples_taken", len(samples))
            selected = choose_best_snapshot(samples)
            if selected is None:
                self.snapshot_gate.mark_rejected()
                layout_snapshot["state"] = self.snapshot_gate.state
                layout_snapshot["snapshot_reject_reason"] = "all_samples_rejected"
                self.runtime_metrics.add("snapshot_rejected_count", 1)
            else:
                self.snapshot_gate.mark_analyzing()
                
                # Szybki podgląd stanu analizy
                display_analysis = selected.frame.copy()
                self.opencv_preview.draw_hud(display_analysis, fps, "ANALIZOWANIE SNAPSHOTA...")
                self.opencv_preview.show(display_analysis)
                self.opencv_preview.handle_keyboard(self.camera_session)
                
                analysis_frame = selected.frame
                if self.table_calibration.calibrated:
                    warped_frame = self.table_calibration.warp_frame(selected.frame)
                    if warped_frame is not None:
                        analysis_frame = warped_frame
                        self.runtime_metrics.add("snapshot_analysis_warped", 1)
                    else:
                        self.runtime_metrics.add("snapshot_analysis_warped", 0)
                else:
                    self.runtime_metrics.add("snapshot_analysis_warped", 0)

                roi_hints = None
                if self.change_detector is not None and self.previous_stable_snapshot is not None:
                    change_result = self.change_detector.detect(
                        self.previous_stable_snapshot,
                        analysis_frame,
                        empty_reference=self.background_model,
                    )
                    self.runtime_metrics.add("change_region_count", len(change_result.regions))
                    self.runtime_metrics.add("change_mask_ratio", change_result.mask_nonzero_ratio)
                    self.runtime_metrics.add("change_global_shift", 1 if change_result.global_shift else 0)
                    self.runtime_metrics.add("change_ignored_small_count", change_result.ignored_small_count)
                    self.runtime_metrics.add("change_ignored_large_count", change_result.ignored_large_count)
                    self.runtime_metrics.add(
                        "change_added_count",
                        sum(1 for region in change_result.regions if region.kind == "added_or_moved"),
                    )
                    self.runtime_metrics.add(
                        "change_removed_count",
                        sum(1 for region in change_result.regions if region.kind == "removed"),
                    )
                    if not change_result.global_shift:
                        roi_hints = [
                            region.bbox for region in change_result.regions
                            if region.kind == "added_or_moved"
                        ]

                analysis_start = time.perf_counter()
                result = self.snapshot_analyzer.analyze(analysis_frame, roi_hints=roi_hints)
                diagnostics = result.diagnostics if isinstance(result.diagnostics, dict) else {}
                self.runtime_metrics.add("snapshot_quads_found", diagnostics.get("quads_found", 0))
                self.runtime_metrics.add("snapshot_recognition_attempts", diagnostics.get("recognition_attempts", 0))
                self.runtime_metrics.add("snapshot_recognition_rejections", diagnostics.get("recognition_rejections", 0))
                self.runtime_metrics.add("snapshot_candidate_validation_rejections", diagnostics.get("candidate_validation_rejections", 0))
                self.runtime_metrics.add("recognition_score", diagnostics.get("recognition_score", 0.0))
                self.runtime_metrics.add("snapshot_recognition_score", diagnostics.get("recognition_score", 0.0))
                for metric_name, metric_value in summarize_detection_diagnostics(
                        diagnostics.get("detection")).items():
                    self.runtime_metrics.add(metric_name, metric_value)
                analysis_ms = (time.perf_counter() - analysis_start) * 1000.0
                self.runtime_metrics.add("snapshot_analysis_ms", analysis_ms)
                self.runtime_metrics.add("snapshot_quality_score", selected.quality.quality_score)
                autotune_recorder_result = self._record_autotune_sample(
                    diagnostics=diagnostics,
                    accepted_count=result.card_count,
                    analysis_ms=analysis_ms,
                    quality_score=selected.quality.quality_score,
                )

                if result.card_count > 0:
                    self.empty_snapshot_streak = 0
                    self.snapshot_layout_id += 1
                    self.last_snapshot_cards = result.cards
                    self.snapshot_gate.mark_published(
                        layout_id=self.snapshot_layout_id,
                        now_ms=int(time.time() * 1000),
                    )
                    self.runtime_metrics.add("layout_publish_count", 1)
                    self.runtime_metrics.add("layout_changed", 1)
                    if self.last_motion_started_ms is not None:
                        self.runtime_metrics.add(
                            "time_from_motion_to_publish_ms",
                            int(time.time() * 1000) - self.last_motion_started_ms,
                        )
                else:
                    self.empty_snapshot_streak += 1
                    self.snapshot_gate.mark_rejected()
                    layout_snapshot["snapshot_reject_reason"] = "no_cards"
                    self.runtime_metrics.add("snapshot_rejected_count", 1)
                    self.runtime_metrics.add("snapshot_empty_streak", self.empty_snapshot_streak)
                    if (self.last_snapshot_cards
                            and self.empty_snapshot_streak >= self.empty_snapshot_clear_threshold):
                        self.snapshot_layout_id += 1
                        self.last_snapshot_cards = []
                        layout_snapshot["snapshot_reject_reason"] = "cards_removed_confirmed"
                        self.runtime_metrics.add("cards_removed_count", 1)
                        self.runtime_metrics.add("layout_changed", 1)

                if (
                        isinstance(autotune_recorder_result, dict)
                        and autotune_recorder_result.get("request_next_sample")):
                    self.snapshot_gate.request_sample(now_ms=int(time.time() * 1000))

                layout_snapshot.update({
                    "layout_id": self.snapshot_layout_id,
                    "state": self.snapshot_gate.state,
                    "analysis_ms": analysis_ms,
                    "quality_score": selected.quality.quality_score,
                    "card_count": len(self.last_snapshot_cards),
                })
                self.previous_stable_snapshot = analysis_frame.copy()

        metrics_snapshot = self.runtime_metrics.snapshot()
        runtime_snapshot = {
            "profile": self.runtime_profile,
            "camera_index": self.camera_session.camera_index,
            "capture_width": frame_width,
            "capture_height": frame_height,
            "camera_focus_locked": self.runtime_config.values.get("CAMERA_FOCUS_LOCKED", False),
            "camera_exposure_locked": self.runtime_config.values.get("CAMERA_EXPOSURE_LOCKED", False),
            "schedule_mode": "snapshot_first",
            "table": self.table_calibration.status(),
        }
        
        status_update_start = time.perf_counter()
        self.status_store.update_cv_state(
            cards=self.last_snapshot_cards,
            metrics=metrics_snapshot,
            runtime=runtime_snapshot,
            operator=self.build_operator_snapshot_fn(
                cards=self.last_snapshot_cards,
                metrics=metrics_snapshot,
                runtime=runtime_snapshot,
                layout=layout_snapshot,
                warnings=list(self.operator_warnings[-8:]),
            ),
            layout=layout_snapshot,
            warnings=list(self.operator_warnings[-8:])
        )
        self.runtime_metrics.add("status_update_ms", (time.perf_counter() - status_update_start) * 1000.0)

        diagnostics_time = time.time()
        if diagnostics_time - self.last_diagnostics_time >= 1.0:
            self.diagnostics_writer.append(metrics_snapshot, runtime_snapshot, self.last_snapshot_cards)
            self.last_diagnostics_time = diagnostics_time

        self.runtime_metrics.add("frame_loop_ms", (time.perf_counter() - frame_loop_start) * 1000.0)

        display_frame = frame.copy()
        status_line = f"SNAPSHOT: {layout_snapshot['state']} | stable {gate_decision.stable_for_ms} ms | cards {len(self.last_snapshot_cards)}"
        self.opencv_preview.draw_hud(display_frame, fps, status_line)
        self.opencv_preview.show(display_frame)

        key_action = self.opencv_preview.handle_keyboard(self.camera_session)
        
        return {
            "action": key_action if key_action else "continue",
            "frame_width": self.camera_session.frame_width,
            "frame_height": self.camera_session.frame_height
        }

    def _record_autotune_sample(self, diagnostics, accepted_count, analysis_ms, quality_score):
        if self.autotune_sample_recorder is None:
            return None
        sample = {
            "candidate_count": int(diagnostics.get("quads_found", 0)),
            "accepted_count": int(accepted_count),
            "geometry_score": float(quality_score),
            "recognition_score": float(diagnostics.get("recognition_score", 0.0)),
            "false_positive_count": 0,
            "matching_ms": float(analysis_ms),
            "recognition_rejections": int(diagnostics.get("recognition_rejections", 0)),
            "candidate_validation_rejections": int(diagnostics.get("candidate_validation_rejections", 0)),
        }
        return self.autotune_sample_recorder(sample)
