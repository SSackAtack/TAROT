# -*- coding: utf-8 -*-
import unittest
from unittest.mock import MagicMock, patch, mock_open
import os
import tempfile
import shutil
import json
from tarotvision.camera import CameraSession

class TestCameraSession(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.session = CameraSession(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('cv2.VideoCapture')
    def test_open_success(self, mock_vc_class):
        mock_vc = MagicMock()
        mock_vc.isOpened.return_value = True
        mock_vc.get.side_effect = lambda prop_id: 1280 if prop_id == 3 else (720 if prop_id == 4 else -1.0)
        mock_vc_class.return_value = mock_vc
        
        opened = self.session.open(0)
        
        self.assertTrue(opened)
        self.assertEqual(mock_vc_class.call_count, 1)
        self.assertTrue(self.session.is_opened())
        self.assertEqual(self.session.frame_width, 1280)
        self.assertEqual(self.session.frame_height, 720)

    @patch('tarotvision.camera.camera_session.platform.system')
    @patch('cv2.VideoCapture')
    def test_open_uses_directshow_backend_on_windows(self, mock_vc_class, mock_system):
        mock_system.return_value = "Windows"
        mock_vc = MagicMock()
        mock_vc.isOpened.return_value = True
        mock_vc.get.side_effect = lambda prop_id: 1280 if prop_id == 3 else (720 if prop_id == 4 else -1.0)
        mock_vc_class.return_value = mock_vc

        opened = self.session.open(0)

        self.assertTrue(opened)
        mock_vc_class.assert_called_once_with(0, 700)

    @patch('tarotvision.camera.camera_session.platform.system')
    @patch('cv2.VideoCapture')
    def test_configure_capture_prefers_mjpg_before_resolution_on_windows(self, mock_vc_class, mock_system):
        mock_system.return_value = "Windows"
        mock_vc = MagicMock()
        mock_vc.isOpened.return_value = True
        mock_vc.get.side_effect = lambda prop_id: 1280 if prop_id == 3 else (720 if prop_id == 4 else -1.0)
        mock_vc_class.return_value = mock_vc

        opened = self.session.open(0)

        self.assertTrue(opened)
        mock_vc.set.assert_any_call(6, 1196444237)
        calls = mock_vc.set.call_args_list
        fourcc_index = calls.index(((6, 1196444237),))
        width_index = calls.index(((3, 1280),))
        height_index = calls.index(((4, 720),))
        self.assertLess(fourcc_index, width_index)
        self.assertLess(fourcc_index, height_index)

    @patch('tarotvision.camera.camera_session.platform.system')
    @patch('cv2.VideoCapture')
    def test_open_falls_back_to_default_backend_when_directshow_fails(self, mock_vc_class, mock_system):
        mock_system.return_value = "Windows"
        dshow_capture = MagicMock()
        dshow_capture.isOpened.return_value = False
        default_capture = MagicMock()
        default_capture.isOpened.return_value = True
        default_capture.get.side_effect = lambda prop_id: 1280 if prop_id == 3 else (720 if prop_id == 4 else -1.0)
        mock_vc_class.side_effect = [dshow_capture, default_capture]

        opened = self.session.open(0)

        self.assertTrue(opened)
        self.assertEqual(mock_vc_class.call_count, 2)
        mock_vc_class.assert_any_call(0, 700)
        mock_vc_class.assert_any_call(0)
        dshow_capture.release.assert_called_once()
        self.assertIs(self.session.capture, default_capture)

    @patch('cv2.VideoCapture')
    def test_open_failed(self, mock_vc_class):
        mock_vc = MagicMock()
        mock_vc.isOpened.return_value = False
        mock_vc_class.return_value = mock_vc
        
        opened = self.session.open(0)
        
        self.assertFalse(opened)
        self.assertFalse(self.session.is_opened())

    @patch('cv2.VideoCapture')
    def test_read(self, mock_vc_class):
        mock_vc = MagicMock()
        mock_vc.isOpened.return_value = True
        mock_vc.read.return_value = (True, "fake_frame")
        mock_vc_class.return_value = mock_vc
        
        self.session.open(0)
        success, frame = self.session.read()
        
        self.assertTrue(success)
        self.assertEqual(frame, "fake_frame")

    @patch('cv2.resize')
    @patch('cv2.VideoCapture')
    def test_read_resizes_frame_when_camera_ignores_requested_resolution(self, mock_vc_class, mock_resize):
        frame = MagicMock()
        frame.shape = (1080, 1920, 3)
        resized = MagicMock()
        resized.shape = (720, 1280, 3)
        mock_resize.return_value = resized

        mock_vc = MagicMock()
        mock_vc.isOpened.return_value = True
        mock_vc.read.return_value = (True, frame)
        mock_vc.get.side_effect = lambda prop_id: 1920 if prop_id == 3 else (1080 if prop_id == 4 else -1.0)
        mock_vc_class.return_value = mock_vc

        self.session.open(0)
        success, output = self.session.read()

        self.assertTrue(success)
        self.assertIs(output, resized)
        mock_resize.assert_called_once_with(frame, (1280, 720))
        self.assertEqual(self.session.frame_width, 1280)
        self.assertEqual(self.session.frame_height, 720)

    @patch('cv2.VideoCapture')
    def test_close_saves_settings(self, mock_vc_class):
        mock_vc = MagicMock()
        mock_vc.isOpened.return_value = True
        # Zwraca 50.0 dla FOCUS i 1.0 dla AUTOFOCUS
        mock_vc.get.side_effect = lambda prop_id: 50.0 if prop_id == 28 else (1.0 if prop_id == 21 else -1.0)
        mock_vc_class.return_value = mock_vc
        
        self.session.open(0)
        self.session.close()
        
        mock_vc.release.assert_called_once()
        self.assertIsNone(self.session.capture)
        
        # Sprawdzamy, czy plik ustawień został zapisany
        settings_file = os.path.join(self.test_dir, "camera_settings.json")
        self.assertTrue(os.path.exists(settings_file))
        with open(settings_file, "r") as f:
            settings = json.load(f)
        self.assertEqual(settings.get("CAP_PROP_FOCUS"), 50.0)

    @patch('cv2.VideoCapture')
    def test_switch_camera(self, mock_vc_class):
        mock_vc1 = MagicMock()
        mock_vc1.isOpened.return_value = True
        
        mock_vc2 = MagicMock()
        mock_vc2.isOpened.return_value = True
        
        # Pierwsze wywołanie VideoCapture zwraca mock_vc1, drugie mock_vc2
        mock_vc_class.side_effect = [mock_vc1, mock_vc2]
        
        self.session.open(0)
        self.assertEqual(self.session.camera_index, 0)
        
        # Przełączamy na kamerę 1
        switched = self.session.switch(1)
        
        self.assertTrue(switched)
        self.assertEqual(self.session.camera_index, 1)
        mock_vc1.release.assert_called_once()
        self.assertEqual(mock_vc_class.call_count, 2)

    @patch('cv2.VideoCapture')
    def test_set_control(self, mock_vc_class):
        mock_vc = MagicMock()
        mock_vc.isOpened.return_value = True
        mock_vc_class.return_value = mock_vc
        
        self.session.open(0)
        success = self.session.set_control("CAP_PROP_FOCUS", 75.0)
        
        self.assertTrue(success)
        mock_vc.set.assert_any_call(28, 75.0) # 28 to cv2.CAP_PROP_FOCUS
        self.assertEqual(self.session.camera_set_cache.get("CAP_PROP_FOCUS"), 75.0)

    @patch('cv2.VideoCapture')
    def test_save_settings_prefers_operator_set_value_over_stale_readback(self, mock_vc_class):
        mock_vc = MagicMock()
        mock_vc.isOpened.return_value = True
        mock_vc.get.side_effect = lambda prop_id: 0.0 if prop_id == 28 else -1.0
        mock_vc_class.return_value = mock_vc

        self.session.open(0)
        self.session.set_control("CAP_PROP_FOCUS", 185.0)

        with open(os.path.join(self.test_dir, "camera_settings.json"), "r") as f:
            settings = json.load(f)

        self.assertEqual(settings["CAP_PROP_FOCUS"], 185.0)

if __name__ == '__main__':
    unittest.main()
