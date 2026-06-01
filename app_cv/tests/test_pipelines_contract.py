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

if __name__ == '__main__':
    unittest.main()
