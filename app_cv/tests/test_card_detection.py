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
