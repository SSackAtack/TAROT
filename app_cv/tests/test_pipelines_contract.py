# -*- coding: utf-8 -*-
import unittest
from unittest.mock import MagicMock
import numpy as np
import tarotvision.pipelines as pipelines
from tarotvision.pipelines import VisionPipeline, SnapshotFirstPipeline

class MockVisionPipeline(VisionPipeline):
    def process_frame(self, frame):
        return {
            "cards": [],
            "metrics": {"fps": 30.0},
            "warnings": [],
            "display_frame": frame.copy()
        }


class TestPipelinesContract(unittest.TestCase):
    def _readable_frame(self, value=255):
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        frame[::8, :] = value
        frame[:, ::8] = value
        return frame

    def test_mock_pipeline_satisfies_contract(self):
        pipeline = MockVisionPipeline()
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        result = pipeline.process_frame(frame)
        
        # Weryfikacja kontraktu wyjściowego
        self.assertIn("cards", result)
        self.assertIn("metrics", result)
        self.assertIn("warnings", result)
        self.assertIn("display_frame", result)
        
        self.assertEqual(result["cards"], [])
        self.assertEqual(result["metrics"]["fps"], 30.0)
        self.assertEqual(result["warnings"], [])
        self.assertTrue(isinstance(result["display_frame"], np.ndarray))

    def test_snapshot_pipeline_contract(self):
        camera_session = MagicMock()
        camera_session.frame_width = 1280
        camera_session.frame_height = 720
        
        opencv_preview = MagicMock()
        opencv_preview.handle_keyboard.return_value = None
        status_store = MagicMock()
        diagnostics_writer = MagicMock()
        snapshot_gate = MagicMock()
        snapshot_analyzer = MagicMock()
        table_calibration = MagicMock()
        runtime_metrics = MagicMock()
        
        runtime_config = MagicMock()
        runtime_config.values = {}
        
        pipeline = SnapshotFirstPipeline(
            camera_session=camera_session,
            opencv_preview=opencv_preview,
            status_store=status_store,
            diagnostics_writer=diagnostics_writer,
            snapshot_gate=snapshot_gate,
            snapshot_analyzer=snapshot_analyzer,
            table_calibration=table_calibration,
            runtime_metrics=runtime_metrics,
            runtime_config=runtime_config,
            build_operator_snapshot_fn=MagicMock(),
            operator_warnings=[],
            log_dir="dummy",
            runtime_profile="default"
        )
        
        frame = np.zeros((720, 1280, 3), dtype=np.uint8)
        motion_result = MagicMock()
        motion_result.motion_detected = False
        motion_result.changed_ratio = 0.0
        
        gate_decision = MagicMock()
        gate_decision.state = "HOLDING"
        gate_decision.stable_for_ms = 0
        gate_decision.should_sample = False
        snapshot_gate.update.return_value = gate_decision
        
        result = pipeline.process_frame(
            frame=frame,
            motion_result=motion_result,
            frame_width=1280,
            frame_height=720,
            frame_loop_start=12345.67
        )
        
        self.assertTrue(issubclass(SnapshotFirstPipeline, VisionPipeline))
        self.assertIn("action", result)
        self.assertIn("frame_width", result)
        self.assertIn("frame_height", result)
        self.assertEqual(result["action"], "continue")

    def test_legacy_pipeline_is_not_exported(self):
        self.assertFalse(hasattr(pipelines, "StateFirstLegacyPipeline"))
        self.assertNotIn("StateFirstLegacyPipeline", pipelines.__all__)

    def test_snapshot_pipeline_analyzes_warped_frame_when_table_is_calibrated(self):
        camera_session = MagicMock()
        camera_session.frame_width = 1280
        camera_session.frame_height = 720
        camera_session.camera_index = 0

        opencv_preview = MagicMock()
        opencv_preview.handle_keyboard.return_value = None
        status_store = MagicMock()
        diagnostics_writer = MagicMock()
        snapshot_gate = MagicMock()
        snapshot_analyzer = MagicMock()
        snapshot_analyzer.analyze.return_value.card_count = 0
        snapshot_analyzer.analyze.return_value.cards = []

        table_calibration = MagicMock()
        table_calibration.calibrated = True
        warped = np.full((720, 1280, 3), 77, dtype=np.uint8)
        table_calibration.warp_frame.return_value = warped
        table_calibration.status.return_value = {"calibrated": True, "marker_ids": [10, 11, 12, 13]}

        runtime_metrics = MagicMock()
        runtime_metrics.snapshot.return_value = {}
        runtime_config = MagicMock()
        runtime_config.values = {}

        gate_decision = MagicMock()
        gate_decision.state = "sampling_snapshots"
        gate_decision.stable_for_ms = 700
        gate_decision.should_sample = True
        snapshot_gate.update.return_value = gate_decision

        pipeline = SnapshotFirstPipeline(
            camera_session=camera_session,
            opencv_preview=opencv_preview,
            status_store=status_store,
            diagnostics_writer=diagnostics_writer,
            snapshot_gate=snapshot_gate,
            snapshot_analyzer=snapshot_analyzer,
            table_calibration=table_calibration,
            runtime_metrics=runtime_metrics,
            runtime_config=runtime_config,
            build_operator_snapshot_fn=MagicMock(return_value={}),
            operator_warnings=[],
            log_dir="dummy",
            runtime_profile="default",
        )

        motion_result = MagicMock()
        motion_result.motion_detected = False
        motion_result.changed_ratio = 0.0

        pipeline.process_frame(
            frame=self._readable_frame(),
            motion_result=motion_result,
            frame_width=1280,
            frame_height=720,
            frame_loop_start=12345.67,
        )

        snapshot_analyzer.analyze.assert_called_once()
        analyzed_frame = snapshot_analyzer.analyze.call_args.args[0]
        self.assertTrue(np.array_equal(analyzed_frame, warped))
        runtime_metrics.add.assert_any_call("snapshot_analysis_warped", 1)

    def test_snapshot_pipeline_clears_cards_after_confirmed_empty_snapshots(self):
        camera_session = MagicMock()
        camera_session.frame_width = 1280
        camera_session.frame_height = 720
        camera_session.camera_index = 0

        opencv_preview = MagicMock()
        opencv_preview.handle_keyboard.return_value = None
        status_store = MagicMock()
        diagnostics_writer = MagicMock()
        snapshot_gate = MagicMock()
        snapshot_analyzer = MagicMock()
        table_calibration = MagicMock()
        table_calibration.calibrated = False
        table_calibration.status.return_value = {"calibrated": False, "marker_ids": []}

        runtime_metrics = MagicMock()
        runtime_metrics.snapshot.return_value = {}
        runtime_config = MagicMock()
        runtime_config.values = {}

        gate_decision = MagicMock()
        gate_decision.state = "sampling_snapshots"
        gate_decision.stable_for_ms = 700
        gate_decision.should_sample = True
        snapshot_gate.update.return_value = gate_decision

        visible = MagicMock()
        visible.card_count = 1
        visible.cards = [{"name": "Gilded_73"}]
        visible.diagnostics = {}

        empty = MagicMock()
        empty.card_count = 0
        empty.cards = []
        empty.diagnostics = {}
        snapshot_analyzer.analyze.side_effect = [visible, empty, empty]

        pipeline = SnapshotFirstPipeline(
            camera_session=camera_session,
            opencv_preview=opencv_preview,
            status_store=status_store,
            diagnostics_writer=diagnostics_writer,
            snapshot_gate=snapshot_gate,
            snapshot_analyzer=snapshot_analyzer,
            table_calibration=table_calibration,
            runtime_metrics=runtime_metrics,
            runtime_config=runtime_config,
            build_operator_snapshot_fn=MagicMock(return_value={}),
            operator_warnings=[],
            log_dir="dummy",
            runtime_profile="default",
        )

        motion_result = MagicMock()
        motion_result.motion_detected = False
        motion_result.changed_ratio = 0.0

        for _ in range(3):
            pipeline.process_frame(
                frame=self._readable_frame(),
                motion_result=motion_result,
                frame_width=1280,
                frame_height=720,
                frame_loop_start=12345.67,
            )

        self.assertEqual(pipeline.last_snapshot_cards, [])
        _, kwargs = status_store.update_cv_state.call_args
        self.assertEqual(kwargs["cards"], [])
        self.assertEqual(kwargs["layout"]["card_count"], 0)
        self.assertEqual(kwargs["layout"]["snapshot_reject_reason"], "cards_removed_confirmed")
        runtime_metrics.add.assert_any_call("cards_removed_count", 1)

    def test_snapshot_pipeline_records_autotune_sample_after_analysis(self):
        camera_session = MagicMock()
        camera_session.frame_width = 1280
        camera_session.frame_height = 720
        camera_session.camera_index = 0

        opencv_preview = MagicMock()
        opencv_preview.handle_keyboard.return_value = None
        status_store = MagicMock()
        diagnostics_writer = MagicMock()
        snapshot_gate = MagicMock()

        snapshot_analyzer = MagicMock()
        analyzed = MagicMock()
        analyzed.card_count = 1
        analyzed.cards = [{"name": "Gilded_17"}]
        analyzed.diagnostics = {
            "quads_found": 2,
            "recognition_attempts": 2,
            "recognition_rejections": 1,
            "candidate_validation_rejections": 1,
            "recognition_score": 0.42,
        }
        snapshot_analyzer.analyze.return_value = analyzed

        table_calibration = MagicMock()
        table_calibration.calibrated = False
        table_calibration.status.return_value = {"calibrated": False, "marker_ids": []}

        runtime_metrics = MagicMock()
        runtime_metrics.snapshot.return_value = {}
        runtime_config = MagicMock()
        runtime_config.values = {}

        gate_decision = MagicMock()
        gate_decision.state = "sampling_snapshots"
        gate_decision.stable_for_ms = 700
        gate_decision.should_sample = True
        snapshot_gate.update.return_value = gate_decision

        samples = []
        pipeline = SnapshotFirstPipeline(
            camera_session=camera_session,
            opencv_preview=opencv_preview,
            status_store=status_store,
            diagnostics_writer=diagnostics_writer,
            snapshot_gate=snapshot_gate,
            snapshot_analyzer=snapshot_analyzer,
            table_calibration=table_calibration,
            runtime_metrics=runtime_metrics,
            runtime_config=runtime_config,
            build_operator_snapshot_fn=MagicMock(return_value={}),
            operator_warnings=[],
            log_dir="dummy",
            runtime_profile="default",
            autotune_sample_recorder=samples.append,
        )

        motion_result = MagicMock()
        motion_result.motion_detected = False
        motion_result.changed_ratio = 0.0

        pipeline.process_frame(
            frame=self._readable_frame(),
            motion_result=motion_result,
            frame_width=1280,
            frame_height=720,
            frame_loop_start=12345.67,
        )

        self.assertEqual(len(samples), 1)
        self.assertEqual(samples[0]["candidate_count"], 2)
        self.assertEqual(samples[0]["accepted_count"], 1)
        self.assertEqual(samples[0]["recognition_score"], 0.42)
        self.assertEqual(samples[0]["recognition_rejections"], 1)
        self.assertEqual(samples[0]["candidate_validation_rejections"], 1)
        self.assertIn("matching_ms", samples[0])
        runtime_metrics.add.assert_any_call("snapshot_candidate_validation_rejections", 1)

    def test_snapshot_pipeline_requests_next_autotune_sample_after_rejected_empty_snapshot(self):
        camera_session = MagicMock()
        camera_session.frame_width = 1280
        camera_session.frame_height = 720
        camera_session.camera_index = 0

        opencv_preview = MagicMock()
        opencv_preview.handle_keyboard.return_value = None
        status_store = MagicMock()
        diagnostics_writer = MagicMock()
        snapshot_gate = MagicMock()

        snapshot_analyzer = MagicMock()
        analyzed = MagicMock()
        analyzed.card_count = 0
        analyzed.cards = []
        analyzed.diagnostics = {"quads_found": 0, "recognition_score": 0.0}
        snapshot_analyzer.analyze.return_value = analyzed

        table_calibration = MagicMock()
        table_calibration.calibrated = False
        table_calibration.status.return_value = {"calibrated": False, "marker_ids": []}

        runtime_metrics = MagicMock()
        runtime_metrics.snapshot.return_value = {}
        runtime_config = MagicMock()
        runtime_config.values = {}

        gate_decision = MagicMock()
        gate_decision.state = "sampling_snapshots"
        gate_decision.stable_for_ms = 700
        gate_decision.should_sample = True
        snapshot_gate.update.return_value = gate_decision

        pipeline = SnapshotFirstPipeline(
            camera_session=camera_session,
            opencv_preview=opencv_preview,
            status_store=status_store,
            diagnostics_writer=diagnostics_writer,
            snapshot_gate=snapshot_gate,
            snapshot_analyzer=snapshot_analyzer,
            table_calibration=table_calibration,
            runtime_metrics=runtime_metrics,
            runtime_config=runtime_config,
            build_operator_snapshot_fn=MagicMock(return_value={}),
            operator_warnings=[],
            log_dir="dummy",
            runtime_profile="default",
            autotune_sample_recorder=MagicMock(return_value={"request_next_sample": True}),
        )

        motion_result = MagicMock()
        motion_result.motion_detected = False
        motion_result.changed_ratio = 0.0

        pipeline.process_frame(
            frame=self._readable_frame(),
            motion_result=motion_result,
            frame_width=1280,
            frame_height=720,
            frame_loop_start=12345.67,
        )

        snapshot_gate.mark_rejected.assert_called_once()
        snapshot_gate.request_sample.assert_called_once()

    def test_snapshot_pipeline_reports_quality_reason_when_all_samples_rejected(self):
        camera_session = MagicMock()
        camera_session.frame_width = 1280
        camera_session.frame_height = 720
        camera_session.camera_index = 0

        opencv_preview = MagicMock()
        opencv_preview.handle_keyboard.return_value = None
        status_store = MagicMock()
        diagnostics_writer = MagicMock()
        snapshot_gate = MagicMock()
        snapshot_analyzer = MagicMock()

        table_calibration = MagicMock()
        table_calibration.calibrated = False
        table_calibration.status.return_value = {"calibrated": False, "marker_ids": []}

        runtime_metrics = MagicMock()
        runtime_metrics.snapshot.return_value = {}
        runtime_config = MagicMock()
        runtime_config.values = {}

        gate_decision = MagicMock()
        gate_decision.state = "sampling_snapshots"
        gate_decision.stable_for_ms = 700
        gate_decision.should_sample = True
        snapshot_gate.update.return_value = gate_decision

        pipeline = SnapshotFirstPipeline(
            camera_session=camera_session,
            opencv_preview=opencv_preview,
            status_store=status_store,
            diagnostics_writer=diagnostics_writer,
            snapshot_gate=snapshot_gate,
            snapshot_analyzer=snapshot_analyzer,
            table_calibration=table_calibration,
            runtime_metrics=runtime_metrics,
            runtime_config=runtime_config,
            build_operator_snapshot_fn=MagicMock(return_value={}),
            operator_warnings=[],
            log_dir="dummy",
            runtime_profile="default",
        )

        motion_result = MagicMock()
        motion_result.motion_detected = False
        motion_result.changed_ratio = 0.0

        pipeline.process_frame(
            frame=np.zeros((720, 1280, 3), dtype=np.uint8),
            motion_result=motion_result,
            frame_width=1280,
            frame_height=720,
            frame_loop_start=12345.67,
        )

        snapshot_analyzer.analyze.assert_not_called()
        kwargs = status_store.update_cv_state.call_args.kwargs
        self.assertEqual(kwargs["layout"]["snapshot_reject_reason"], "all_samples_rejected")
        self.assertEqual(kwargs["layout"]["snapshot_quality_reject_reason"], "too_dark")
        runtime_metrics.add.assert_any_call("snapshot_quality_brightness", 0.0)
        runtime_metrics.add.assert_any_call("snapshot_quality_contrast", 0.0)

    def test_snapshot_pipeline_passes_change_rois_to_analyzer(self):
        camera_session = MagicMock()
        camera_session.frame_width = 300
        camera_session.frame_height = 200
        camera_session.camera_index = 0

        opencv_preview = MagicMock()
        opencv_preview.handle_keyboard.return_value = None
        status_store = MagicMock()
        diagnostics_writer = MagicMock()
        snapshot_gate = MagicMock()
        gate_decision = MagicMock()
        gate_decision.state = "sampling_snapshots"
        gate_decision.stable_for_ms = 700
        gate_decision.should_sample = True
        snapshot_gate.update.return_value = gate_decision

        snapshot_analyzer = MagicMock()
        analyzed = MagicMock()
        analyzed.card_count = 0
        analyzed.cards = []
        analyzed.diagnostics = {}
        snapshot_analyzer.analyze.return_value = analyzed

        table_calibration = MagicMock()
        table_calibration.calibrated = False
        table_calibration.status.return_value = {"calibrated": False, "marker_ids": []}

        runtime_metrics = MagicMock()
        runtime_metrics.snapshot.return_value = {}
        runtime_config = MagicMock()
        runtime_config.values = {}

        change_detector = MagicMock()
        change_region = MagicMock()
        change_region.kind = "added_or_moved"
        change_region.bbox = (40, 30, 80, 120)
        change_detector.detect.return_value.regions = [change_region]
        change_detector.detect.return_value.mask_nonzero_ratio = 0.08
        change_detector.detect.return_value.global_shift = False
        change_detector.detect.return_value.ignored_small_count = 0
        change_detector.detect.return_value.ignored_large_count = 0

        pipeline = SnapshotFirstPipeline(
            camera_session=camera_session,
            opencv_preview=opencv_preview,
            status_store=status_store,
            diagnostics_writer=diagnostics_writer,
            snapshot_gate=snapshot_gate,
            snapshot_analyzer=snapshot_analyzer,
            table_calibration=table_calibration,
            runtime_metrics=runtime_metrics,
            runtime_config=runtime_config,
            build_operator_snapshot_fn=MagicMock(return_value={}),
            operator_warnings=[],
            log_dir="dummy",
            runtime_profile="default",
            change_detector=change_detector,
        )
        pipeline.previous_stable_snapshot = self._readable_frame()[0:200, 0:300]

        motion_result = MagicMock()
        motion_result.motion_detected = False
        motion_result.changed_ratio = 0.0

        pipeline.process_frame(
            frame=self._readable_frame()[0:200, 0:300],
            motion_result=motion_result,
            frame_width=300,
            frame_height=200,
            frame_loop_start=12345.67,
        )

        snapshot_analyzer.analyze.assert_called_once()
        self.assertEqual(snapshot_analyzer.analyze.call_args.kwargs["roi_hints"], [(40, 30, 80, 120)])
        runtime_metrics.add.assert_any_call("change_region_count", 1)
        runtime_metrics.add.assert_any_call("change_mask_ratio", 0.08)

    def test_snapshot_pipeline_passes_empty_roi_list_without_global_fallback(self):
        camera_session = MagicMock()
        camera_session.frame_width = 300
        camera_session.frame_height = 200
        camera_session.camera_index = 0

        opencv_preview = MagicMock()
        opencv_preview.handle_keyboard.return_value = None
        status_store = MagicMock()
        diagnostics_writer = MagicMock()
        snapshot_gate = MagicMock()
        gate_decision = MagicMock()
        gate_decision.state = "sampling_snapshots"
        gate_decision.stable_for_ms = 700
        gate_decision.should_sample = True
        snapshot_gate.update.return_value = gate_decision

        snapshot_analyzer = MagicMock()
        analyzed = MagicMock()
        analyzed.card_count = 0
        analyzed.cards = []
        analyzed.diagnostics = {}
        snapshot_analyzer.analyze.return_value = analyzed

        table_calibration = MagicMock()
        table_calibration.calibrated = False
        table_calibration.status.return_value = {"calibrated": False, "marker_ids": []}

        runtime_metrics = MagicMock()
        runtime_metrics.snapshot.return_value = {}
        runtime_config = MagicMock()
        runtime_config.values = {}

        removed_region = MagicMock()
        removed_region.kind = "removed"
        removed_region.bbox = (40, 30, 80, 120)
        change_detector = MagicMock()
        change_detector.detect.return_value.regions = [removed_region]
        change_detector.detect.return_value.mask_nonzero_ratio = 0.08
        change_detector.detect.return_value.global_shift = False
        change_detector.detect.return_value.ignored_small_count = 0
        change_detector.detect.return_value.ignored_large_count = 0

        pipeline = SnapshotFirstPipeline(
            camera_session=camera_session,
            opencv_preview=opencv_preview,
            status_store=status_store,
            diagnostics_writer=diagnostics_writer,
            snapshot_gate=snapshot_gate,
            snapshot_analyzer=snapshot_analyzer,
            table_calibration=table_calibration,
            runtime_metrics=runtime_metrics,
            runtime_config=runtime_config,
            build_operator_snapshot_fn=MagicMock(return_value={}),
            operator_warnings=[],
            log_dir="dummy",
            runtime_profile="default",
            change_detector=change_detector,
        )
        pipeline.previous_stable_snapshot = self._readable_frame()[0:200, 0:300]

        motion_result = MagicMock()
        motion_result.motion_detected = False
        motion_result.changed_ratio = 0.0

        pipeline.process_frame(
            frame=self._readable_frame()[0:200, 0:300],
            motion_result=motion_result,
            frame_width=300,
            frame_height=200,
            frame_loop_start=12345.67,
        )

        snapshot_analyzer.analyze.assert_called_once()
        self.assertEqual(snapshot_analyzer.analyze.call_args.kwargs["roi_hints"], [])
        runtime_metrics.add.assert_any_call("change_removed_count", 1)

    def test_snapshot_pipeline_holds_previous_state_on_global_shift(self):
        camera_session = MagicMock()
        camera_session.frame_width = 300
        camera_session.frame_height = 200
        camera_session.camera_index = 0

        opencv_preview = MagicMock()
        opencv_preview.handle_keyboard.return_value = None
        status_store = MagicMock()
        diagnostics_writer = MagicMock()
        snapshot_gate = MagicMock()
        gate_decision = MagicMock()
        gate_decision.state = "sampling_snapshots"
        gate_decision.stable_for_ms = 700
        gate_decision.should_sample = True
        snapshot_gate.update.return_value = gate_decision

        snapshot_analyzer = MagicMock()
        table_calibration = MagicMock()
        table_calibration.calibrated = False
        table_calibration.status.return_value = {"calibrated": False, "marker_ids": []}

        runtime_metrics = MagicMock()
        runtime_metrics.snapshot.return_value = {}
        runtime_config = MagicMock()
        runtime_config.values = {}

        change_detector = MagicMock()
        change_detector.detect.return_value.regions = []
        change_detector.detect.return_value.mask_nonzero_ratio = 0.90
        change_detector.detect.return_value.global_shift = True
        change_detector.detect.return_value.ignored_small_count = 0
        change_detector.detect.return_value.ignored_large_count = 0

        pipeline = SnapshotFirstPipeline(
            camera_session=camera_session,
            opencv_preview=opencv_preview,
            status_store=status_store,
            diagnostics_writer=diagnostics_writer,
            snapshot_gate=snapshot_gate,
            snapshot_analyzer=snapshot_analyzer,
            table_calibration=table_calibration,
            runtime_metrics=runtime_metrics,
            runtime_config=runtime_config,
            build_operator_snapshot_fn=MagicMock(return_value={}),
            operator_warnings=[],
            log_dir="dummy",
            runtime_profile="default",
            change_detector=change_detector,
        )
        previous_snapshot = self._readable_frame()[0:200, 0:300].copy()
        pipeline.previous_stable_snapshot = previous_snapshot.copy()
        pipeline.last_snapshot_cards = [{"name": "17_star"}]

        motion_result = MagicMock()
        motion_result.motion_detected = False
        motion_result.changed_ratio = 0.0

        pipeline.process_frame(
            frame=self._readable_frame(value=128)[0:200, 0:300],
            motion_result=motion_result,
            frame_width=300,
            frame_height=200,
            frame_loop_start=12345.67,
        )

        snapshot_analyzer.analyze.assert_not_called()
        self.assertEqual(pipeline.last_snapshot_cards, [{"name": "17_star"}])
        self.assertTrue(np.array_equal(pipeline.previous_stable_snapshot, previous_snapshot))
        runtime_metrics.add.assert_any_call("change_global_shift", 1)
        _, kwargs = status_store.update_cv_state.call_args
        self.assertEqual(kwargs["cards"], [{"name": "17_star"}])
        self.assertEqual(kwargs["layout"]["snapshot_reject_reason"], "global_shift_detected")

    def test_snapshot_pipeline_preserves_cards_when_no_added_or_removed_regions(self):
        camera_session = MagicMock()
        camera_session.frame_width = 300
        camera_session.frame_height = 200
        camera_session.camera_index = 0

        opencv_preview = MagicMock()
        opencv_preview.handle_keyboard.return_value = None
        status_store = MagicMock()
        diagnostics_writer = MagicMock()
        snapshot_gate = MagicMock()
        gate_decision = MagicMock()
        gate_decision.state = "sampling_snapshots"
        gate_decision.stable_for_ms = 700
        gate_decision.should_sample = True
        snapshot_gate.update.return_value = gate_decision

        snapshot_analyzer = MagicMock()
        table_calibration = MagicMock()
        table_calibration.calibrated = False
        table_calibration.status.return_value = {"calibrated": False, "marker_ids": []}

        runtime_metrics = MagicMock()
        runtime_metrics.snapshot.return_value = {}
        runtime_config = MagicMock()
        runtime_config.values = {}

        change_detector = MagicMock()
        change_detector.detect.return_value.regions = []
        change_detector.detect.return_value.mask_nonzero_ratio = 0.0
        change_detector.detect.return_value.global_shift = False
        change_detector.detect.return_value.ignored_small_count = 0
        change_detector.detect.return_value.ignored_large_count = 0

        pipeline = SnapshotFirstPipeline(
            camera_session=camera_session,
            opencv_preview=opencv_preview,
            status_store=status_store,
            diagnostics_writer=diagnostics_writer,
            snapshot_gate=snapshot_gate,
            snapshot_analyzer=snapshot_analyzer,
            table_calibration=table_calibration,
            runtime_metrics=runtime_metrics,
            runtime_config=runtime_config,
            build_operator_snapshot_fn=MagicMock(return_value={}),
            operator_warnings=[],
            log_dir="dummy",
            runtime_profile="default",
            change_detector=change_detector,
        )
        pipeline.previous_stable_snapshot = self._readable_frame()[0:200, 0:300]
        pipeline.last_snapshot_cards = [{"name": "17_star"}]

        motion_result = MagicMock()
        motion_result.motion_detected = False
        motion_result.changed_ratio = 0.0

        for _ in range(2):
            pipeline.process_frame(
                frame=self._readable_frame()[0:200, 0:300],
                motion_result=motion_result,
                frame_width=300,
                frame_height=200,
                frame_loop_start=12345.67,
            )

        snapshot_analyzer.analyze.assert_not_called()
        self.assertEqual(pipeline.last_snapshot_cards, [{"name": "17_star"}])
        self.assertEqual(pipeline.empty_snapshot_streak, 0)
        _, kwargs = status_store.update_cv_state.call_args
        self.assertEqual(kwargs["cards"], [{"name": "17_star"}])
        self.assertEqual(kwargs["layout"]["snapshot_reject_reason"], "no_change_hold_previous")

    def test_snapshot_pipeline_collects_empty_reference_frames_before_validation(self):
        camera_session = MagicMock()
        camera_session.frame_width = 300
        camera_session.frame_height = 200
        camera_session.camera_index = 0

        opencv_preview = MagicMock()
        opencv_preview.handle_keyboard.return_value = None
        status_store = MagicMock()
        diagnostics_writer = MagicMock()
        snapshot_gate = MagicMock()
        gate_decision = MagicMock()
        gate_decision.state = "sampling_snapshots"
        gate_decision.stable_for_ms = 700
        gate_decision.should_sample = True
        snapshot_gate.update.return_value = gate_decision

        snapshot_analyzer = MagicMock()
        snapshot_analyzer.analyze.return_value.card_count = 0
        snapshot_analyzer.analyze.return_value.cards = []
        snapshot_analyzer.analyze.return_value.diagnostics = {}

        table_calibration = MagicMock()
        table_calibration.calibrated = False
        table_calibration.status.return_value = {"calibrated": False, "marker_ids": []}

        runtime_metrics = MagicMock()
        runtime_metrics.snapshot.return_value = {}
        runtime_config = MagicMock()
        runtime_config.values = {}

        background_model = MagicMock()
        background_model.changed_ratio.return_value = 0.0
        recorder = MagicMock(side_effect=[
            {"collect_empty_reference_frame": True, "request_next_sample": True},
            {"collect_empty_reference_frame": True, "request_next_sample": True},
            {"collect_empty_reference_frame": True, "finalize_empty_reference": True},
        ])

        pipeline = SnapshotFirstPipeline(
            camera_session=camera_session,
            opencv_preview=opencv_preview,
            status_store=status_store,
            diagnostics_writer=diagnostics_writer,
            snapshot_gate=snapshot_gate,
            snapshot_analyzer=snapshot_analyzer,
            table_calibration=table_calibration,
            runtime_metrics=runtime_metrics,
            runtime_config=runtime_config,
            build_operator_snapshot_fn=MagicMock(return_value={}),
            operator_warnings=[],
            log_dir="dummy",
            runtime_profile="default",
            background_model=background_model,
            autotune_sample_recorder=recorder,
        )

        motion_result = MagicMock()
        motion_result.motion_detected = False
        motion_result.changed_ratio = 0.0

        for index in range(2):
            pipeline.process_frame(
                frame=self._readable_frame(value=80 + index)[0:200, 0:300],
                motion_result=motion_result,
                frame_width=300,
                frame_height=200,
                frame_loop_start=12345.67,
            )
            background_model.capture_many.assert_not_called()

        final_frame = self._readable_frame(value=128)[0:200, 0:300]
        pipeline.process_frame(
            frame=final_frame,
            motion_result=motion_result,
            frame_width=300,
            frame_height=200,
            frame_loop_start=12345.67,
        )

        background_model.capture_many.assert_called_once()
        captured_frames = background_model.capture_many.call_args.args[0]
        self.assertEqual(len(captured_frames), 3)
        self.assertTrue(all(frame is not final_frame for frame in captured_frames))

    def test_empty_reference_validation_uses_background_changed_ratio(self):
        camera_session = MagicMock()
        camera_session.frame_width = 300
        camera_session.frame_height = 200
        camera_session.camera_index = 0

        opencv_preview = MagicMock()
        opencv_preview.handle_keyboard.return_value = None
        status_store = MagicMock()
        diagnostics_writer = MagicMock()
        snapshot_gate = MagicMock()
        gate_decision = MagicMock()
        gate_decision.state = "sampling_snapshots"
        gate_decision.stable_for_ms = 700
        gate_decision.should_sample = True
        snapshot_gate.update.return_value = gate_decision

        snapshot_analyzer = MagicMock()
        snapshot_analyzer.analyze.return_value.card_count = 0
        snapshot_analyzer.analyze.return_value.cards = []
        snapshot_analyzer.analyze.return_value.diagnostics = {}

        table_calibration = MagicMock()
        table_calibration.calibrated = False
        table_calibration.status.return_value = {"calibrated": False, "marker_ids": []}

        runtime_metrics = MagicMock()
        runtime_metrics.snapshot.return_value = {}
        runtime_config = MagicMock()
        runtime_config.values = {}

        background_model = MagicMock()
        background_model.active = True
        background_model.changed_ratio.return_value = 0.0
        recorder = MagicMock(return_value={
            "collect_empty_reference_frame": True,
            "finalize_empty_reference": True,
        })

        pipeline = SnapshotFirstPipeline(
            camera_session=camera_session,
            opencv_preview=opencv_preview,
            status_store=status_store,
            diagnostics_writer=diagnostics_writer,
            snapshot_gate=snapshot_gate,
            snapshot_analyzer=snapshot_analyzer,
            table_calibration=table_calibration,
            runtime_metrics=runtime_metrics,
            runtime_config=runtime_config,
            build_operator_snapshot_fn=MagicMock(return_value={}),
            operator_warnings=[],
            log_dir="dummy",
            runtime_profile="default",
            background_model=background_model,
            autotune_sample_recorder=recorder,
        )

        motion_result = MagicMock()
        motion_result.motion_detected = False
        motion_result.changed_ratio = 0.0
        frame = self._readable_frame(value=128)[0:200, 0:300]

        pipeline.process_frame(
            frame=frame,
            motion_result=motion_result,
            frame_width=300,
            frame_height=200,
            frame_loop_start=12345.67,
        )

        background_model.capture_many.assert_called_once()
        background_model.changed_ratio.assert_called_once()
        self.assertTrue(np.array_equal(background_model.changed_ratio.call_args.args[0], frame))
        self.assertEqual(background_model.changed_ratio.call_args.kwargs["threshold"], 20)
        runtime_metrics.add.assert_any_call("background_reference_validation_ratio", 0.0)
        runtime_metrics.add.assert_any_call("background_reference_validation_warning", 0)

    def test_empty_reference_capture_records_frames_when_change_detector_reports_no_change(self):
        camera_session = MagicMock()
        camera_session.frame_width = 300
        camera_session.frame_height = 200
        camera_session.camera_index = 0

        opencv_preview = MagicMock()
        opencv_preview.handle_keyboard.return_value = None
        status_store = MagicMock()
        diagnostics_writer = MagicMock()
        snapshot_gate = MagicMock()
        gate_decision = MagicMock()
        gate_decision.state = "sampling_snapshots"
        gate_decision.stable_for_ms = 700
        gate_decision.should_sample = True
        snapshot_gate.update.return_value = gate_decision

        snapshot_analyzer = MagicMock()
        table_calibration = MagicMock()
        table_calibration.calibrated = False
        table_calibration.status.return_value = {"calibrated": False, "marker_ids": []}

        runtime_metrics = MagicMock()
        runtime_metrics.snapshot.return_value = {}
        runtime_config = MagicMock()
        runtime_config.values = {}

        background_model = MagicMock()
        background_model.changed_ratio.return_value = 0.0
        change_detector = MagicMock()
        change_detector.detect.return_value.regions = []
        change_detector.detect.return_value.mask_nonzero_ratio = 0.0
        change_detector.detect.return_value.global_shift = False
        change_detector.detect.return_value.ignored_small_count = 0
        change_detector.detect.return_value.ignored_large_count = 0
        recorder = MagicMock(side_effect=[
            {"collect_empty_reference_frame": True, "request_next_sample": True},
            {"collect_empty_reference_frame": True, "request_next_sample": True},
            {"collect_empty_reference_frame": True, "finalize_empty_reference": True},
        ])

        pipeline = SnapshotFirstPipeline(
            camera_session=camera_session,
            opencv_preview=opencv_preview,
            status_store=status_store,
            diagnostics_writer=diagnostics_writer,
            snapshot_gate=snapshot_gate,
            snapshot_analyzer=snapshot_analyzer,
            table_calibration=table_calibration,
            runtime_metrics=runtime_metrics,
            runtime_config=runtime_config,
            build_operator_snapshot_fn=MagicMock(return_value={}),
            operator_warnings=[],
            log_dir="dummy",
            runtime_profile="default",
            background_model=background_model,
            change_detector=change_detector,
            autotune_sample_recorder=recorder,
        )
        pipeline.empty_reference_capture_active = True
        pipeline.previous_stable_snapshot = self._readable_frame(value=64)[0:200, 0:300]
        pipeline.last_snapshot_cards = [{"name": "17_star"}]

        motion_result = MagicMock()
        motion_result.motion_detected = False
        motion_result.changed_ratio = 0.0

        for value in (80, 96, 128):
            pipeline.process_frame(
                frame=self._readable_frame(value=value)[0:200, 0:300],
                motion_result=motion_result,
                frame_width=300,
                frame_height=200,
                frame_loop_start=12345.67,
            )

        snapshot_analyzer.analyze.assert_not_called()
        self.assertEqual(recorder.call_count, 3)
        self.assertEqual(
            [call.args[0]["accepted_count"] for call in recorder.call_args_list],
            [0, 0, 0],
        )
        background_model.capture_many.assert_called_once()
        background_model.changed_ratio.assert_called_once()
        self.assertEqual(pipeline.empty_reference_frames, [])
        self.assertFalse(pipeline.empty_reference_capture_active)

    def test_empty_reference_capture_records_false_positive_without_publishing_layout(self):
        camera_session = MagicMock()
        camera_session.frame_width = 300
        camera_session.frame_height = 200
        camera_session.camera_index = 0

        opencv_preview = MagicMock()
        opencv_preview.handle_keyboard.return_value = None
        status_store = MagicMock()
        diagnostics_writer = MagicMock()
        snapshot_gate = MagicMock()
        gate_decision = MagicMock()
        gate_decision.state = "sampling_snapshots"
        gate_decision.stable_for_ms = 700
        gate_decision.should_sample = True
        snapshot_gate.update.return_value = gate_decision

        snapshot_analyzer = MagicMock()
        analyzed = MagicMock()
        analyzed.card_count = 2
        analyzed.cards = [{"name": "false_1"}, {"name": "false_2"}]
        analyzed.diagnostics = {"quads_found": 2, "recognition_score": 0.25}
        snapshot_analyzer.analyze.return_value = analyzed

        table_calibration = MagicMock()
        table_calibration.calibrated = False
        table_calibration.status.return_value = {"calibrated": False, "marker_ids": []}

        runtime_metrics = MagicMock()
        runtime_metrics.snapshot.return_value = {}
        runtime_config = MagicMock()
        runtime_config.values = {}

        samples = []

        def recorder(sample):
            samples.append(sample)
            return {"collect_empty_reference_frame": True, "request_next_sample": True}

        pipeline = SnapshotFirstPipeline(
            camera_session=camera_session,
            opencv_preview=opencv_preview,
            status_store=status_store,
            diagnostics_writer=diagnostics_writer,
            snapshot_gate=snapshot_gate,
            snapshot_analyzer=snapshot_analyzer,
            table_calibration=table_calibration,
            runtime_metrics=runtime_metrics,
            runtime_config=runtime_config,
            build_operator_snapshot_fn=MagicMock(return_value={}),
            operator_warnings=[],
            log_dir="dummy",
            runtime_profile="default",
            autotune_sample_recorder=recorder,
        )
        pipeline.empty_reference_capture_active = True

        motion_result = MagicMock()
        motion_result.motion_detected = False
        motion_result.changed_ratio = 0.0

        pipeline.process_frame(
            frame=self._readable_frame()[0:200, 0:300],
            motion_result=motion_result,
            frame_width=300,
            frame_height=200,
            frame_loop_start=12345.67,
        )

        self.assertEqual(samples[0]["candidate_count"], 2)
        self.assertEqual(samples[0]["accepted_count"], 2)
        self.assertEqual(pipeline.last_snapshot_cards, [])
        kwargs = status_store.update_cv_state.call_args.kwargs
        self.assertEqual(kwargs["cards"], [])
        self.assertEqual(kwargs["layout"]["snapshot_reject_reason"], "empty_reference_capture_hold")
        runtime_metrics.add.assert_any_call("empty_reference_false_positive_hold", 1)

if __name__ == '__main__':
    unittest.main()
