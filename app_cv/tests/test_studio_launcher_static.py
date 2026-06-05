# -*- coding: utf-8 -*-
import os
import unittest


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class StudioLauncherStaticTest(unittest.TestCase):
    def _read_launcher(self):
        launcher_path = os.path.join(PROJECT_ROOT, "start_tarotvision_studio.bat")
        self.assertTrue(os.path.exists(launcher_path), f"Brak launchera: {launcher_path}")
        with open(launcher_path, "r", encoding="utf-8") as launcher_file:
            return launcher_file.read()

    def test_studio_launcher_does_not_prompt_for_deck_choice(self):
        source = self._read_launcher()

        self.assertNotIn("WYBÓR TALII", source)
        self.assertNotIn("DECK_CHOICE", source)
        self.assertNotIn("Twój wybór [1-7]", source)

    def test_studio_launcher_keeps_backend_deck_fallback(self):
        source = self._read_launcher()

        self.assertIn('set "TAROTVISION_DECK=rider-waite-smith"', source)
        self.assertIn("set TAROTVISION_DECK=%TAROTVISION_DECK%", source)
        self.assertIn("Aktywne talie wybierasz w Studio", source)

    def test_studio_launcher_checks_frontend_websocket_and_preview_ports(self):
        source = self._read_launcher()

        self.assertIn("Get-NetTCPConnection -LocalPort 5173,8765,8766", source)
        self.assertIn("portach 5173, 8765 i 8766", source)


if __name__ == "__main__":
    unittest.main()
