import unittest

from tarotvision.tuning_protocol import parse_control_message, ControlMessageError


class TuningProtocolTest(unittest.TestCase):
    def test_parses_tuning_update(self):
        message = parse_control_message(
            '{"type": "tuning_update", "param": "LOCK_DEAD_ZONE_POS", "value": 3.5}'
        )

        self.assertEqual(message.type, "tuning_update")
        self.assertEqual(message.param, "LOCK_DEAD_ZONE_POS")
        self.assertEqual(message.value, 3.5)

    def test_parses_camera_set(self):
        message = parse_control_message(
            '{"type": "camera_set", "param": "CAP_PROP_FOCUS", "value": 150.0}'
        )

        self.assertEqual(message.type, "camera_set")
        self.assertEqual(message.param, "CAP_PROP_FOCUS")
        self.assertEqual(message.value, 150.0)

    def test_rejects_unknown_type(self):
        with self.assertRaises(ControlMessageError):
            parse_control_message('{"type": "unknown"}')

    def test_parses_profile_apply(self):
        message = parse_control_message('{"type": "profile_apply", "name": "studio_day"}')

        self.assertEqual(message.type, "profile_apply")
        self.assertEqual(message.name, "studio_day")

    def test_rejects_invalid_json(self):
        with self.assertRaises(ControlMessageError):
            parse_control_message("{broken")


if __name__ == "__main__":
    unittest.main()
