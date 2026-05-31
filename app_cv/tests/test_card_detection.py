import unittest

import numpy as np

from tarotvision.card_detection import is_card_aspect_ratio, find_card_quads


class CardAspectRatioTest(unittest.TestCase):
    def test_accepts_tarot_like_ratio_portrait(self):
        # 70x120 = ratio 1.71 — blisko 1.72
        self.assertTrue(is_card_aspect_ratio(width=70, height=120))

    def test_accepts_tarot_like_ratio_landscape(self):
        # Karta obrocona o 90 stopni — aspect ratio ten sam
        self.assertTrue(is_card_aspect_ratio(width=120, height=70))

    def test_rejects_square_ratio(self):
        self.assertFalse(is_card_aspect_ratio(width=100, height=100))

    def test_rejects_very_elongated_ratio(self):
        # 50x300 = ratio 6.0 — zdecydowanie nie karta
        self.assertFalse(is_card_aspect_ratio(width=50, height=300))

    def test_rejects_zero_dimensions(self):
        self.assertFalse(is_card_aspect_ratio(width=0, height=100))
        self.assertFalse(is_card_aspect_ratio(width=100, height=0))

    def test_rejects_negative_dimensions(self):
        self.assertFalse(is_card_aspect_ratio(width=-10, height=100))


class FindCardQuadsTest(unittest.TestCase):
    def test_detects_card_shaped_rectangle(self):
        # Tworzymy syntetyczny obraz z jednym bialym prostokatem o proporcjach karty
        # na czarnym tle — powinien zostac wykryty jako quad
        img = np.zeros((720, 1280, 3), dtype=np.uint8)
        # Karta ~70x120 px (aspect ~1.71) — rysujemy bialy wypelniony prostokat
        cv2.rectangle(img, (400, 200), (470, 320), (255, 255, 255), -1)

        quads = find_card_quads(img)

        self.assertGreaterEqual(len(quads), 1)
        # Sprawdzamy ze znaleziony quad ma 4 wierzcholki
        self.assertEqual(len(quads[0]), 4)

    def test_rejects_square_contour(self):
        # Kwadrat 100x100 — nie ma proporcji karty
        img = np.zeros((720, 1280, 3), dtype=np.uint8)
        cv2.rectangle(img, (400, 200), (500, 300), (255, 255, 255), -1)

        quads = find_card_quads(img)

        self.assertEqual(len(quads), 0)

    def test_returns_empty_for_blank_image(self):
        img = np.zeros((720, 1280, 3), dtype=np.uint8)

        quads = find_card_quads(img)

        self.assertEqual(len(quads), 0)

    def test_detects_multiple_cards(self):
        img = np.zeros((720, 1280, 3), dtype=np.uint8)
        # Dwie karty w roznych miejscach
        cv2.rectangle(img, (100, 100), (170, 220), (255, 255, 255), -1)  # ~70x120
        cv2.rectangle(img, (600, 300), (670, 420), (255, 255, 255), -1)  # ~70x120

        quads = find_card_quads(img)

        self.assertGreaterEqual(len(quads), 2)

    def test_default_backwards_compatibility(self):
        img = np.zeros((720, 1280, 3), dtype=np.uint8)
        cv2.rectangle(img, (400, 200), (470, 320), (255, 255, 255), -1)
        quads = find_card_quads(img)
        self.assertGreaterEqual(len(quads), 1)

    def test_invalid_contour_mode_raises_value_error(self):
        img = np.zeros((720, 1280, 3), dtype=np.uint8)
        with self.assertRaises(ValueError):
            find_card_quads(img, contour_mode="invalid_mode")

    def test_max_candidates_sorting_and_limiting(self):
        img = np.zeros((720, 1280, 3), dtype=np.uint8)
        # Rysujemy 3 karty o roznych powierzchniach
        # Karta duza: 140x240
        cv2.rectangle(img, (100, 100), (240, 340), (255, 255, 255), -1)
        # Karta srednia: 70x120
        cv2.rectangle(img, (400, 100), (470, 220), (255, 255, 255), -1)
        # Karta mala: 35x60
        cv2.rectangle(img, (700, 100), (735, 160), (255, 255, 255), -1)

        # Sprawdzmy, czy z max_candidates=2 zwroci tylko dwie najwieksze
        quads = find_card_quads(img, max_candidates=2, min_area_ratio=0.0001)
        self.assertEqual(len(quads), 2)
        
        # Pierwsza powinna byc najwieksza
        area0 = cv2.contourArea(quads[0])
        area1 = cv2.contourArea(quads[1])
        self.assertGreater(area0, area1)

    def test_return_debug_format(self):
        img = np.zeros((720, 1280, 3), dtype=np.uint8)
        cv2.rectangle(img, (400, 200), (470, 320), (255, 255, 255), -1)
        
        quads, debug_info = find_card_quads(img, return_debug=True)
        self.assertGreaterEqual(len(quads), 1)
        self.assertEqual(debug_info["contour_mode"], "external")
        self.assertEqual(debug_info["canny_low"], 50)
        self.assertEqual(debug_info["canny_high"], 150)
        self.assertIn("contours_total", debug_info)
        self.assertIn("candidates_after_area", debug_info)
        self.assertIn("candidates_after_quad", debug_info)
        self.assertEqual(debug_info["quads_final"], len(quads))

    def test_find_card_quads_with_debug_helper(self):
        img = np.zeros((720, 1280, 3), dtype=np.uint8)
        cv2.rectangle(img, (400, 200), (470, 320), (255, 255, 255), -1)
        
        from tarotvision.card_detection import find_card_quads_with_debug
        quads, debug_info = find_card_quads_with_debug(img)
        self.assertGreaterEqual(len(quads), 1)
        self.assertEqual(debug_info["quads_final"], len(quads))

    def test_nested_contour_a4_trap(self):
        # 1. Stworz syntetyczny obraz BGR 800x600
        img = np.zeros((600, 800, 3), dtype=np.uint8)
        
        # 2. Narysuj duzy prostokat (A4): 300x450 px (stosunek 1.5 - w granicach tolerancji)
        cv2.rectangle(img, (250, 75), (550, 525), (255, 255, 255), -1)
        
        # 3. Wewnatrz narysuj czarna "dziure" (ciemna mata): 240x350 px
        cv2.rectangle(img, (280, 125), (520, 475), (0, 0, 0), -1)
        
        # 4. Wewnatrz dziury narysuj mala biala karte tarota: 180x250 px (stosunek ~1.39 - w granicach tolerancji)
        cv2.rectangle(img, (310, 175), (490, 425), (255, 255, 255), -1)
        
        # Dla contour_mode="external" wykrywany jest tylko zewnetrzny kontur (A4)
        quads_external = find_card_quads(img, contour_mode="external", min_area_ratio=0.001)
        
        # Dla contour_mode="list" lub "tree" powinny byc wykryte oba kontury (A4 i karta)
        quads_list = find_card_quads(img, contour_mode="list", min_area_ratio=0.001)
        quads_tree = find_card_quads(img, contour_mode="tree", min_area_ratio=0.001)
        
        # Weryfikacja:
        self.assertEqual(len(quads_external), 1)
        self.assertGreaterEqual(len(quads_list), 2)
        self.assertGreaterEqual(len(quads_tree), 2)


# Import cv2 tutaj, zeby test_card_aspect_ratio dzialal nawet bez OpenCV
try:
    import cv2
except ImportError:
    cv2 = None


if cv2 is None:
    # Usuwamy testy wymagajace OpenCV jesli nie jest dostepne
    del FindCardQuadsTest


if __name__ == "__main__":
    unittest.main()
