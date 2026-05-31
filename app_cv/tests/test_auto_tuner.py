import unittest
import numpy as np
import cv2

from tarotvision.auto_tuner import AutoTuner, tune_card_detection_params, score_candidate_quad


class AutoTunerTest(unittest.TestCase):
    def test_score_candidate_quad_bounds(self):
        # 1. Stworz klatke 800x600
        frame_shape = (600, 800, 3)
        
        # 2. Tworzymy idealna karte 150x258 (proporcja ~1.72) na srodku
        # srodek obrazu: (400, 300)
        # Bounding box: w=150, h=258 => x = 400 - 75 = 325, y = 300 - 129 = 171
        # punkty idealnego quada:
        quad = np.array([
            [[325, 171]],
            [[475, 171]],
            [[475, 429]],
            [[325, 429]]
        ], dtype=np.int32)
        
        score = score_candidate_quad(quad, frame_shape)
        # Powinien byc bardzo wysoki wynik (blisko 1.0)
        self.assertGreater(score, 0.8)

    def test_autotuner_finds_params_for_synthetic_card(self):
        img = np.zeros((600, 800, 3), dtype=np.uint8)
        # Rysujemy idealna wypelniona karte tarota na srodku
        cv2.rectangle(img, (325, 171), (475, 429), (255, 255, 255), -1)
        
        tuner = AutoTuner()
        result = tuner.tune(img)
        
        # Powinno znalezc przynajmniej jakas konfiguracje
        self.assertGreater(result["best_score"], 0.5)
        self.assertEqual(result["confidence"], "HIGH")
        self.assertGreater(result["candidates_found"], 0)

    def test_autotuner_nested_a4_trap_resolution(self):
        # Symulacja A4 trap:
        img = np.zeros((600, 800, 3), dtype=np.uint8)
        
        # 1. Zewnetrzny A4 (300x430, aspect 1.43 - silny falszywy kandydat)
        cv2.rectangle(img, (250, 85), (550, 515), (255, 255, 255), -1)
        
        # 2. Ciemna mata w srodku A4 (240x350)
        cv2.rectangle(img, (280, 125), (520, 475), (0, 0, 0), -1)
        
        # 3. Karta w srodku maty (150x258, aspect 1.72 - idealna karta)
        cv2.rectangle(img, (325, 171), (475, 429), (255, 255, 255), -1)
        
        # Tunujemy z ograniczonym trybem do tylko external
        space_external = {
            "canny_low": [30],
            "canny_high": [100],
            "min_area_ratio": [0.001],
            "contour_mode": ["external"]
        }
        res_external = tune_card_detection_params(img, search_space=space_external)
        
        # Tunujemy z trybem list
        space_list = {
            "canny_low": [30],
            "canny_high": [100],
            "min_area_ratio": [0.001],
            "contour_mode": ["list"]
        }
        res_list = tune_card_detection_params(img, search_space=space_list)
        
        # Weryfikacja:
        # 1. W trybie list autotuner powinien znalezc zagniezdzona karte o wyzszym score niz external (A4)
        self.assertGreater(res_list["best_score"], res_external["best_score"])
        
        # 2. Zwycieski kandydat w trybie list powinien odpowiadac karcie, a nie A4
        # Area ratio karty tarota to ~0.08 (kiedy caly obraz to 800x600 = 480000, w*h = 38700)
        # Area ratio A4 to ~0.26. A4 powinno zostac odrzucone jako zbyt wielkie
        self.assertLess(res_list["best_candidate_area_ratio"], 0.15)
        self.assertGreater(res_list["best_candidate_area_ratio"], 0.05)
        
        # 3. Proporcje boku zwycieskiego kandydata w trybie list musza byc bardzo bliskie 1.72
        self.assertAlmostEqual(res_list["best_candidate_aspect_ratio"], 1.72, delta=0.1)

    def test_autotuner_low_confidence_for_blank_image(self):
        img = np.zeros((600, 800, 3), dtype=np.uint8)
        
        tuner = AutoTuner()
        result = tuner.tune(img)
        
        self.assertEqual(result["best_score"], 0.0)
        self.assertEqual(result["confidence"], "LOW")
        self.assertEqual(result["candidates_found"], 0)

    def test_autotuner_respects_budget(self):
        img = np.zeros((600, 800, 3), dtype=np.uint8)
        cv2.rectangle(img, (325, 171), (475, 429), (255, 255, 255), -1)
        
        # Sprawdzmy budzet 15 iteracji
        tuner = AutoTuner(max_iterations=15)
        result = tuner.tune(img)
        
        self.assertLessEqual(result["iterations"], 15)


if __name__ == "__main__":
    unittest.main()
