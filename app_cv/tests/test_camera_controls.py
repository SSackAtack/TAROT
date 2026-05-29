import unittest

from tarotvision.camera_controls import probe_camera_control


class FakeCapture:
    def __init__(self, supported=True):
        self.supported = supported
        self.value = 0.0

    def get(self, prop):
        return self.value if self.supported else -1.0

    def set(self, prop, value):
        if not self.supported:
            return False
        self.value = value
        return True


class CameraControlsTest(unittest.TestCase):
    def test_probe_reports_supported_when_readback_changes(self):
        result = probe_camera_control(FakeCapture(True), prop_id=1, test_value=12.0)

        self.assertTrue(result.supported)
        self.assertEqual(result.readback_value, 12.0)

    def test_probe_reports_unsupported_when_set_fails(self):
        result = probe_camera_control(FakeCapture(False), prop_id=1, test_value=12.0)

        self.assertFalse(result.supported)


if __name__ == "__main__":
    unittest.main()
