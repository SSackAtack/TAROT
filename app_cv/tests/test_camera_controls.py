import unittest

from tarotvision.camera_controls import read_camera_control


class FakeCapture:
    def __init__(self, value=0.0):
        self.value = value
        self.set_calls = []

    def get(self, prop):
        return self.value

    def set(self, prop, value):
        self.set_calls.append((prop, value))
        return True


class CameraControlsTest(unittest.TestCase):
    def test_read_camera_control_does_not_mutate_capture(self):
        capture = FakeCapture(value=42.0)

        result = read_camera_control(capture, prop_id=1)

        self.assertFalse(result.supported)
        self.assertEqual(result.readback_value, 42.0)
        self.assertEqual(capture.set_calls, [])

    def test_read_camera_control_reports_invalid_readback_as_unsupported(self):
        result = read_camera_control(FakeCapture(value=-1.0), prop_id=1)

        self.assertFalse(result.supported)
        self.assertEqual(result.readback_value, -1.0)

    def test_read_camera_control_reports_current_value_when_zero(self):
        result = read_camera_control(FakeCapture(value=0.0), prop_id=1)

        # Zero can be a valid camera value; read-only probe must not infer support from mutation.
        self.assertFalse(result.supported)
        self.assertEqual(result.readback_value, 0.0)


if __name__ == "__main__":
    unittest.main()
