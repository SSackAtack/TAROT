import os
import tempfile
import unittest

import cv2
import numpy as np

from tarotvision.image_io import imread_grayscale_unicode, imwrite_unicode


class ImageIoTest(unittest.TestCase):
    def test_round_trip_polish_path_grayscale(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "Światło_i_Cień_00.jpg")
            source = np.full((12, 16), 127, dtype=np.uint8)

            self.assertTrue(imwrite_unicode(path, source))
            loaded = imread_grayscale_unicode(path)

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.shape, (12, 16))
        self.assertEqual(loaded.dtype, np.uint8)

    def test_missing_path_returns_none(self):
        loaded = imread_grayscale_unicode("Z:\\missing\\Światło_i_Cień.jpg")

        self.assertIsNone(loaded)

    def test_color_file_can_be_loaded_as_grayscale(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "kolor_ąę.jpg")
            source = np.zeros((10, 10, 3), dtype=np.uint8)
            source[:, :, 1] = 255

            self.assertTrue(imwrite_unicode(path, source))
            loaded = imread_grayscale_unicode(path)

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.ndim, 2)


if __name__ == "__main__":
    unittest.main()
