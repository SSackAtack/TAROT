# -*- coding: utf-8 -*-
import unittest
from unittest.mock import MagicMock
import numpy as np
import tarotvision.pipelines as pipelines
from tarotvision.pipelines import VisionPipeline, SnapshotFirstPipeline, StateFirstDiffPipeline

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

    def test_state_first_diff_pipeline_is_exported(self):
        self.assertTrue(issubclass(StateFirstDiffPipeline, VisionPipeline))
        self.assertIn("StateFirstDiffPipeline", pipelines.__all__)

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

if __name__ == '__main__':
    unittest.main()
