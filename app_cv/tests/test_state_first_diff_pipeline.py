# -*- coding: utf-8 -*-
import unittest
from unittest.mock import MagicMock, create_autospec

import numpy as np

from tarotvision.change_detection import ChangeDetectionResult, ChangeRegion
from tarotvision.snapshot_session_store import SnapshotSessionStore
from tarotvision.status.status_store import StatusStore
from tarotvision.table_state import TableState
from tarotvision.pipelines.state_first_diff import StateFirstDiffPipeline


class TestStateFirstDiffPipeline(unittest.TestCase):
    def _frame(self, value=0):
        return np.full((120, 160, 3), value, dtype=np.uint8)

    def _gate_decision(self, should_sample=True):
        decision = MagicMock()
        decision.state = "sampling_snapshots"
        decision.stable_for_ms = 700
        decision.should_sample = should_sample
        return decision

    def _analysis_result(self, cards):
        result = MagicMock()
        result.cards = cards
        result.card_count = len(cards)
        result.diagnostics = {}
        return result

    def _pipeline(self, session_store=None, table_state=None, build_operator_snapshot_fn=None):
        session_store = session_store or SnapshotSessionStore(clock_ms=MagicMock(return_value=1000))
        table_state = table_state or TableState(["Gilded_01", "Gilded_02"])
        change_detector = MagicMock()
        snapshot_analyzer = MagicMock()
        snapshot_gate = MagicMock()
        snapshot_gate.update.return_value = self._gate_decision()
        status_store = create_autospec(StatusStore, instance=True)
        table_calibration = MagicMock()
        table_calibration.calibrated = False
        table_calibration.status.return_value = {"calibrated": False, "marker_ids": []}
        runtime_metrics = MagicMock()
        runtime_metrics.snapshot.return_value = {}

        pipeline = StateFirstDiffPipeline(
            snapshot_session_store=session_store,
            change_detector=change_detector,
            snapshot_analyzer=snapshot_analyzer,
            table_state=table_state,
            snapshot_gate=snapshot_gate,
            status_store=status_store,
            table_calibration=table_calibration,
            runtime_metrics=runtime_metrics,
            build_operator_snapshot_fn=build_operator_snapshot_fn,
        )
        return pipeline, session_store, table_state, change_detector, snapshot_analyzer, status_store

    def test_waits_for_locked_empty_reference_without_analyzer_call(self):
        pipeline, _, _, change_detector, snapshot_analyzer, status_store = self._pipeline()
        motion_result = MagicMock()
        motion_result.motion_detected = True
        motion_result.changed_ratio = 0.23

        pipeline.process_frame(
            frame=self._frame(10),
            motion_result=motion_result,
            frame_width=160,
            frame_height=120,
            frame_loop_start=123.0,
        )

        change_detector.detect.assert_not_called()
        snapshot_analyzer.analyze.assert_not_called()
        _, kwargs = status_store.update_cv_state.call_args
        self.assertEqual(kwargs["layout"]["state"], "waiting_for_empty_reference")
        self.assertEqual(kwargs["layout"]["session"]["active"], False)
        self.assertEqual(kwargs["layout"]["session"]["empty_reference_locked"], False)

    def test_updates_snapshot_gate_with_wall_clock_milliseconds_and_motion_fields(self):
        pipeline, _, _, _, _, _ = self._pipeline()
        motion_result = MagicMock()
        motion_result.motion_detected = True
        motion_result.changed_ratio = 0.17

        pipeline.process_frame(
            frame=self._frame(10),
            motion_result=motion_result,
            frame_width=160,
            frame_height=120,
            frame_loop_start=123.0,
        )

        _, kwargs = pipeline.snapshot_gate.update.call_args
        self.assertGreaterEqual(kwargs["now_ms"], 1_000_000_000_000)
        self.assertNotEqual(kwargs["now_ms"], 123.0)
        self.assertEqual(kwargs["motion_detected"], True)
        self.assertEqual(kwargs["changed_ratio"], 0.17)

    def test_operator_snapshot_gets_state_first_runtime_context(self):
        build_operator_snapshot = MagicMock(return_value={"active_decks": ["gilded"]})
        pipeline, _, _, _, _, status_store = self._pipeline(
            build_operator_snapshot_fn=build_operator_snapshot
        )
        pipeline.table_calibration.status.return_value = {
            "calibrated": True,
            "marker_ids": [10, 11, 12, 13],
        }
        motion_result = MagicMock()
        motion_result.motion_detected = True
        motion_result.changed_ratio = 0.17

        pipeline.process_frame(
            frame=self._frame(10),
            motion_result=motion_result,
            frame_width=160,
            frame_height=120,
            frame_loop_start=123.0,
        )

        build_operator_snapshot.assert_called_once()
        _, kwargs = build_operator_snapshot.call_args
        self.assertEqual(kwargs["runtime"]["aruco_calibrated"], True)
        self.assertEqual(kwargs["runtime"]["aruco_markers"], 4)
        self.assertEqual(kwargs["layout"]["state"], "waiting_for_empty_reference")
        self.assertEqual(kwargs["warnings"], [])
        _, status_kwargs = status_store.update_cv_state.call_args
        self.assertEqual(status_kwargs["operator"], {"active_decks": ["gilded"]})

    def test_added_roi_is_analyzed_and_current_snapshot_committed(self):
        store = SnapshotSessionStore(clock_ms=MagicMock(return_value=1000))
        store.start_session()
        store.capture_empty_reference(self._frame(0))
        pipeline, store, table_state, change_detector, snapshot_analyzer, status_store = self._pipeline(
            session_store=store
        )
        region = ChangeRegion((40, 30, 50, 60), 0.15, "added", 0.0, 0.9)
        change_detector.detect.return_value = ChangeDetectionResult([region], 0.15, False, 0, 0)
        snapshot_analyzer.analyze.return_value = self._analysis_result([
            {
                "name": "Gilded_01",
                "x": 55,
                "y": 65,
                "angle": 4,
                "confidence": 0.88,
            }
        ])

        pipeline.process_frame(
            frame=self._frame(50),
            motion_result=MagicMock(),
            frame_width=160,
            frame_height=120,
            frame_loop_start=123.0,
        )

        snapshot_analyzer.analyze.assert_called_once()
        self.assertEqual(snapshot_analyzer.analyze.call_args.kwargs["roi_hints"], [(40, 30, 50, 60)])
        self.assertIsNone(store.current_snapshot)
        self.assertIsNotNone(store.previous_snapshot)
        self.assertIn("Gilded_01", table_state.cards)
        _, kwargs = status_store.update_cv_state.call_args
        self.assertEqual(kwargs["layout"]["state"], "state_updated")
        self.assertEqual(kwargs["layout"]["card_count"], 1)
        self.assertEqual(kwargs["layout"]["session"]["active"], True)
        self.assertEqual(kwargs["layout"]["session"]["empty_reference_locked"], True)
        self.assertEqual(kwargs["layout"]["session"]["previous_snapshot"], True)
        self.assertEqual(kwargs["layout"]["session"]["current_snapshot"], False)

    def test_added_compound_roi_preserves_individual_card_bboxes(self):
        store = SnapshotSessionStore(clock_ms=MagicMock(return_value=1000))
        store.start_session()
        store.capture_empty_reference(self._frame(0))
        pipeline, _, table_state, change_detector, snapshot_analyzer, _ = self._pipeline(
            session_store=store
        )
        region = ChangeRegion((20, 20, 120, 90), 0.30, "added", 0.0, 0.9)
        change_detector.detect.return_value = ChangeDetectionResult([region], 0.30, False, 0, 0)
        snapshot_analyzer.analyze.return_value = self._analysis_result([
            {
                "name": "Gilded_01",
                "x": 40,
                "y": 60,
                "angle": 0,
                "confidence": 0.91,
                "bbox": [30, 30, 40, 60],
            },
            {
                "name": "Gilded_02",
                "x": 100,
                "y": 60,
                "angle": 0,
                "confidence": 0.89,
                "bbox": [90, 30, 40, 60],
            },
        ])

        pipeline.process_frame(
            frame=self._frame(50),
            motion_result=MagicMock(),
            frame_width=160,
            frame_height=120,
            frame_loop_start=123.0,
        )

        self.assertEqual(table_state.cards["Gilded_01"].bbox, (30, 30, 40, 60))
        self.assertEqual(table_state.cards["Gilded_02"].bbox, (90, 30, 40, 60))

    def test_added_roi_deduplicates_overlapping_recognition_candidates(self):
        store = SnapshotSessionStore(clock_ms=MagicMock(return_value=1000))
        store.start_session()
        store.capture_empty_reference(self._frame(0))
        pipeline, _, table_state, change_detector, snapshot_analyzer, status_store = self._pipeline(
            session_store=store
        )
        region = ChangeRegion((20, 20, 80, 90), 0.22, "added", 0.0, 0.9)
        change_detector.detect.return_value = ChangeDetectionResult([region], 0.22, False, 0, 0)
        snapshot_analyzer.analyze.return_value = self._analysis_result([
            {
                "name": "Gilded_01",
                "x": 52,
                "y": 65,
                "angle": 0,
                "confidence": 0.74,
                "bbox": [30, 30, 46, 70],
            },
            {
                "name": "Gilded_02",
                "x": 54,
                "y": 66,
                "angle": 0,
                "confidence": 0.91,
                "bbox": [32, 32, 45, 68],
            },
        ])

        pipeline.process_frame(
            frame=self._frame(50),
            motion_result=MagicMock(),
            frame_width=160,
            frame_height=120,
            frame_loop_start=123.0,
        )

        self.assertNotIn("Gilded_01", table_state.cards)
        self.assertIn("Gilded_02", table_state.cards)
        _, kwargs = status_store.update_cv_state.call_args
        self.assertEqual(kwargs["layout"]["accepted_card_count"], 1)

    def test_removed_roi_updates_table_state_without_analyzer(self):
        store = SnapshotSessionStore(clock_ms=MagicMock(return_value=1000))
        store.start_session()
        store.capture_empty_reference(self._frame(0))
        table_state = TableState(["Gilded_01"])
        table_state.upsert_locked("Gilded_01", 50, 50, 0, 0.9, 1, bbox=(40, 30, 50, 60))
        pipeline, store, table_state, change_detector, snapshot_analyzer, status_store = self._pipeline(
            session_store=store,
            table_state=table_state,
        )
        region = ChangeRegion((40, 30, 50, 60), 0.15, "removed", 0.9, 0.0)
        change_detector.detect.return_value = ChangeDetectionResult([region], 0.15, False, 0, 0)

        pipeline.process_frame(
            frame=self._frame(0),
            motion_result=MagicMock(),
            frame_width=160,
            frame_height=120,
            frame_loop_start=123.0,
        )

        snapshot_analyzer.analyze.assert_not_called()
        self.assertEqual(table_state.cards, {})
        self.assertIsNone(store.current_snapshot)
        _, kwargs = status_store.update_cv_state.call_args
        self.assertEqual(kwargs["cards"], [])
        self.assertEqual(kwargs["layout"]["state"], "state_updated")

    def test_added_regions_take_priority_over_moved_slivers(self):
        store = SnapshotSessionStore(clock_ms=MagicMock(return_value=1000))
        store.start_session()
        store.capture_empty_reference(self._frame(0))
        table_state = TableState(["Gilded_01", "Gilded_02"])
        table_state.upsert_locked("Gilded_01", 50, 50, 0, 0.9, 1, bbox=(70, 30, 40, 60))
        pipeline, _, table_state, change_detector, snapshot_analyzer, _ = self._pipeline(
            session_store=store,
            table_state=table_state,
        )
        added = ChangeRegion((20, 20, 40, 60), 0.10, "added", 0.0, 0.8)
        moved_sliver = ChangeRegion((70, 35, 10, 55), 0.02, "moved_or_replaced", 0.8, 0.9)
        change_detector.detect.return_value = ChangeDetectionResult([added, moved_sliver], 0.12, False, 0, 0)
        snapshot_analyzer.analyze.return_value = self._analysis_result([
            {
                "name": "Gilded_02",
                "x": 30,
                "y": 60,
                "angle": 0,
                "confidence": 0.88,
                "bbox": [20, 20, 40, 60],
            },
        ])

        pipeline.process_frame(
            frame=self._frame(50),
            motion_result=MagicMock(),
            frame_width=160,
            frame_height=120,
            frame_loop_start=123.0,
        )

        self.assertEqual(snapshot_analyzer.analyze.call_args.kwargs["roi_hints"], [(20, 20, 40, 60)])
        self.assertEqual(table_state.cards["Gilded_01"].phase, "needs_reverify")
        self.assertEqual(table_state.cards["Gilded_01"].reverify_reason, "moved_or_replaced")

    def test_noise_discards_current_and_keeps_previous_snapshot(self):
        store = SnapshotSessionStore(clock_ms=MagicMock(return_value=1000))
        store.start_session()
        store.capture_empty_reference(self._frame(0))
        previous_before = store.previous_snapshot.image.copy()
        pipeline, store, _, change_detector, snapshot_analyzer, status_store = self._pipeline(session_store=store)
        region = ChangeRegion((3, 3, 8, 8), 0.01, "noise_or_lighting", 0.0, 0.0)
        change_detector.detect.return_value = ChangeDetectionResult([region], 0.01, False, 0, 0)

        pipeline.process_frame(
            frame=self._frame(5),
            motion_result=MagicMock(),
            frame_width=160,
            frame_height=120,
            frame_loop_start=123.0,
        )

        snapshot_analyzer.analyze.assert_not_called()
        self.assertTrue(np.array_equal(store.previous_snapshot.image, previous_before))
        self.assertIsNone(store.current_snapshot)
        _, kwargs = status_store.update_cv_state.call_args
        self.assertEqual(kwargs["layout"]["state"], "noise_or_lighting")

    def test_global_shift_discards_current_and_requests_resync(self):
        store = SnapshotSessionStore(clock_ms=MagicMock(return_value=1000))
        store.start_session()
        store.capture_empty_reference(self._frame(0))
        previous_before = store.previous_snapshot.image.copy()
        pipeline, store, _, change_detector, snapshot_analyzer, status_store = self._pipeline(session_store=store)
        change_detector.detect.return_value = ChangeDetectionResult([], 0.7, True, 0, 0)

        pipeline.process_frame(
            frame=self._frame(90),
            motion_result=MagicMock(),
            frame_width=160,
            frame_height=120,
            frame_loop_start=123.0,
        )

        snapshot_analyzer.analyze.assert_not_called()
        self.assertTrue(np.array_equal(store.previous_snapshot.image, previous_before))
        self.assertIsNone(store.current_snapshot)
        _, kwargs = status_store.update_cv_state.call_args
        self.assertEqual(kwargs["layout"]["state"], "resync_required")
        self.assertEqual(kwargs["layout"]["resync_reason"], "global_shift_detected")


if __name__ == "__main__":
    unittest.main()
