# -*- coding: utf-8 -*-
import os
import unittest


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class CameraControlsStaticTest(unittest.TestCase):
    def _read_frontend_file(self, relative_path):
        path = os.path.join(PROJECT_ROOT, relative_path)
        self.assertTrue(os.path.exists(path), f"Brak pliku: {path}")
        with open(path, "r", encoding="utf-8") as source_file:
            return source_file.read()

    def test_studio_camera_controls_support_precise_input_and_step_buttons(self):
        source = self._read_frontend_file(
            os.path.join("app_ar", "src", "studio", "studioConsole.js")
        )

        self.assertIn('data-camera-role="number"', source)
        self.assertIn('data-camera-step-direction="-1"', source)
        self.assertIn('data-camera-step-direction="1"', source)
        self.assertIn("applyStudioCameraControlValue", source)

    def test_operator_camera_controls_support_precise_input_and_step_buttons(self):
        source = self._read_frontend_file(
            os.path.join("app_ar", "src", "operator", "operatorPanel.js")
        )

        self.assertIn('data-camera-role="number"', source)
        self.assertIn('data-camera-step-direction="-1"', source)
        self.assertIn('data-camera-step-direction="1"', source)
        self.assertIn("applyOperatorCameraControlValue", source)

    def test_studio_deck_panel_shows_active_deck_status(self):
        source = self._read_frontend_file(
            os.path.join("app_ar", "src", "studio", "studioConsole.js")
        )

        self.assertIn('id="studio-active-decks-status"', source)
        self.assertIn("updateStudioActiveDecksStatus", source)
        self.assertIn("Aktywne teraz:", source)
        self.assertIn("Wybierz 1-3 talie przed kalibracją", source)


if __name__ == "__main__":
    unittest.main()
