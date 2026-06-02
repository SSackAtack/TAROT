import unittest

from tarotvision.operator_explainability import build_cv_explainability


class OperatorExplainabilityTest(unittest.TestCase):
    def test_requires_active_deck(self):
        result = build_cv_explainability(
            cards=[],
            metrics={},
            runtime={},
            layout={},
            operator={"active_decks": []},
            warnings=[],
        )

        self.assertEqual(result["severity"], "error")
        self.assertEqual(result["next_action"], "Wybierz 1-3 talie w Studio.")

    def test_no_camera_points_to_camera_check(self):
        result = build_cv_explainability(
            cards=[],
            metrics={},
            runtime={},
            layout={"state": "no_camera"},
            operator={"active_decks": ["gilded"]},
            warnings=[],
        )

        self.assertEqual(result["severity"], "error")
        self.assertEqual(result["next_action"], "Sprawdz kamere i launcher CV.")

    def test_settling_snapshot_requests_still_table(self):
        result = build_cv_explainability(
            cards=[],
            metrics={},
            runtime={"aruco_calibrated": True, "aruco_markers": 4},
            layout={"state": "settling"},
            operator={"active_decks": ["gilded"]},
            warnings=[],
        )

        self.assertEqual(result["severity"], "warn")
        self.assertEqual(result["next_action"], "Zostaw mate nieruchomo przez kilka sekund.")

    def test_detected_cards_are_ok(self):
        result = build_cv_explainability(
            cards=[{"id": "card-1"}],
            metrics={},
            runtime={"aruco_calibrated": True, "aruco_markers": 4},
            layout={"state": "holding_last_good"},
            operator={"active_decks": ["gilded"]},
            warnings=[],
        )

        self.assertEqual(result["severity"], "ok")
        self.assertEqual(result["next_action"], "Mozna prowadzic sesje.")

    def test_candidate_gap_explains_rejected_cards(self):
        result = build_cv_explainability(
            cards=[{"id": "gilded_01"}, {"id": "gilded_02"}],
            metrics={"snapshot_quads_found": 3},
            runtime={"aruco_calibrated": True, "aruco_markers": 4, "candidate_count": 3},
            layout={"state": "holding_last_good"},
            operator={"active_decks": ["gilded"]},
            warnings=[],
        )

        recognition_step = next(step for step in result["steps"] if step["id"] == "recognition")
        self.assertEqual(recognition_step["state"], "warn")
        self.assertIn("2/3", recognition_step["value"])
        self.assertIn("1", recognition_step["message"])
        self.assertEqual(result["severity"], "warn")
        self.assertIn("jedna karta", result["next_action"].lower())

    def test_candidate_gap_mentions_shape_validation_rejection(self):
        result = build_cv_explainability(
            cards=[{"id": "gilded_01"}],
            metrics={
                "snapshot_quads_found": 2,
                "snapshot_candidate_validation_rejections": 1,
            },
            runtime={"aruco_calibrated": True, "aruco_markers": 4},
            layout={"state": "holding_last_good"},
            operator={"active_decks": ["gilded"]},
            warnings=[],
        )

        recognition_step = next(step for step in result["steps"] if step["id"] == "recognition")
        self.assertEqual(recognition_step["state"], "warn")
        self.assertIn("bez cech karty", recognition_step["message"])
        self.assertIn("odblask", result["next_action"].lower())

    def test_aruco_step_counts_marker_ids_from_table_status(self):
        result = build_cv_explainability(
            cards=[{"id": "gilded_01"}],
            metrics={},
            runtime={"table": {"calibrated": True, "marker_ids": [10, 11, 12, 13]}},
            layout={"state": "holding_last_good"},
            operator={"active_decks": ["gilded"]},
            warnings=[],
        )

        aruco_step = next(step for step in result["steps"] if step["id"] == "aruco")
        self.assertEqual(aruco_step["state"], "ok")
        self.assertEqual(aruco_step["value"], "4/4")
        self.assertEqual(aruco_step["message"], "Stol skalibrowany")

    def test_aruco_step_warns_when_using_cached_calibration_without_visible_markers(self):
        result = build_cv_explainability(
            cards=[{"id": "gilded_01"}],
            metrics={},
            runtime={"table": {"calibrated": True, "marker_ids": []}},
            layout={"state": "holding_last_good"},
            operator={"active_decks": ["gilded"]},
            warnings=[],
        )

        aruco_step = next(step for step in result["steps"] if step["id"] == "aruco")
        self.assertEqual(aruco_step["state"], "warn")
        self.assertEqual(aruco_step["value"], "0/4")
        self.assertIn("ostatniej kalibracji", aruco_step["message"])
        self.assertEqual(result["severity"], "warn")
        self.assertEqual(result["next_action"], "Pokaz wszystkie markery ArUco w kadrze.")


if __name__ == "__main__":
    unittest.main()
