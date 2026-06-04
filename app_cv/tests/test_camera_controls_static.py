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

    def test_studio_cv_explainability_panel_renders_next_action(self):
        source = self._read_frontend_file(
            os.path.join("app_ar", "src", "studio", "studioConsole.js")
        )

        self.assertIn("CV Explain", source)
        self.assertIn("renderCvExplainability", source)
        self.assertIn("operator?.explainability", source)
        self.assertIn('id="studio-cv-explain-next"', source)
        self.assertIn("studio-cv-explain-step--", source)

    def test_studio_autotune_panel_sends_operator_commands(self):
        source = self._read_frontend_file(
            os.path.join("app_ar", "src", "studio", "studioConsole.js")
        )

        self.assertIn("studio-autotune-panel", source)
        self.assertIn("renderStudioAutotune", source)
        self.assertIn("operator?.calibration?.autotune", source)
        self.assertIn("autotune_start", source)
        self.assertIn("autotune_calibrate", source)
        self.assertIn("autotune_apply", source)
        self.assertIn("autotune_save", source)
        self.assertIn("autotune_cancel", source)

    def test_studio_sidebar_uses_collapsible_separate_sections(self):
        source = self._read_frontend_file(
            os.path.join("app_ar", "src", "studio", "studioConsole.js")
        )

        self.assertIn('data-studio-section="decks"', source)
        self.assertIn('data-studio-section="autotune"', source)
        self.assertIn('data-studio-section="cv-diagnostics"', source)
        self.assertIn("initializeStudioSidebarAccordions", source)
        self.assertIn("studio:sidebarCollapsedSections", source)
        self.assertIn("data-studio-accordion-toggle", source)

    def test_studio_preview_modes_support_table_camera_and_pip(self):
        source = self._read_frontend_file(
            os.path.join("app_ar", "src", "studio", "studioConsole.js")
        )

        self.assertIn("setStudioPreviewMode", source)
        self.assertIn('data-preview-mode="table"', source)
        self.assertIn('data-preview-mode="camera"', source)
        self.assertIn('data-preview-mode="pip"', source)
        self.assertIn("'preview'", source)
        self.assertIn("Wirtualny stół", source)
        self.assertIn("studio-preview-mode-btn--active", source)
        self.assertIn("setStudioPipSize", source)
        self.assertIn('id="studio-pip-size-slider"', source)
        self.assertIn("--studio-pip-width", source)
        self.assertIn("studio:pipSize", source)

    def test_studio_pip_slider_is_not_capped_before_maximum_value(self):
        source = self._read_frontend_file(os.path.join("app_ar", "studio.css"))

        self.assertIn("--studio-pip-width", source)
        self.assertIn("calc(100% - 56px)", source)
        self.assertNotIn(
            "width: min(var(--studio-pip-width, 30%), 560px)",
            source,
        )


if __name__ == "__main__":
    unittest.main()
