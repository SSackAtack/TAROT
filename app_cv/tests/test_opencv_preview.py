# -*- coding: utf-8 -*-
import unittest
from unittest.mock import MagicMock, patch
import numpy as np
from tarotvision.preview import OpenCvPreview

class TestOpenCvPreview(unittest.TestCase):
    def setUp(self):
        self.preview = OpenCvPreview(window_title="TestWindow")

    @patch('cv2.putText')
    def test_draw_hud(self, mock_put_text):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        self.preview.draw_hud(frame, fps=29.9, status_line="Test Status")
        
        # Sprawdzamy, czy putText został wywołany co najmniej dla FPS oraz status_line
        self.assertTrue(mock_put_text.call_count >= 2)
        
        # Weryfikujemy argumenty (pierwszy to frame, potem tekst zawierający FPS lub Test Status)
        called_texts = [call[0][1] for call in mock_put_text.call_args_list]
        self.assertTrue(any("FPS: 29.9" in txt for txt in called_texts))
        self.assertTrue(any("Test Status" in txt for txt in called_texts))

    @patch('cv2.imshow')
    def test_show(self, mock_imshow):
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        self.preview.show(frame)
        mock_imshow.assert_called_once_with("TestWindow", frame)

    @patch('cv2.destroyAllWindows')
    def test_close(self, mock_destroy):
        self.preview.close()
        mock_destroy.assert_called_once()

    @patch('cv2.waitKey')
    def test_handle_keyboard_quit(self, mock_wait_key):
        mock_wait_key.return_value = ord('q')
        mock_session = MagicMock()
        
        result = self.preview.handle_keyboard(mock_session)
        self.assertEqual(result, "quit")
        mock_session.switch.assert_not_called()

    @patch('cv2.waitKey')
    def test_handle_keyboard_switch(self, mock_wait_key):
        mock_wait_key.return_value = ord('2')
        mock_session = MagicMock()
        mock_session.switch.return_value = True
        
        result = self.preview.handle_keyboard(mock_session)
        self.assertEqual(result, "switch")
        mock_session.switch.assert_called_once_with(2)

    @patch('cv2.waitKey')
    def test_handle_keyboard_none(self, mock_wait_key):
        mock_wait_key.return_value = ord('a')
        mock_session = MagicMock()
        
        result = self.preview.handle_keyboard(mock_session)
        self.assertIsNone(result)
        mock_session.switch.assert_not_called()

if __name__ == '__main__':
    unittest.main()
