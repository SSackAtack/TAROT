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

    def test_parses_studio_set_recording_dir(self):
        message = parse_control_message(
            '{"type": "studio_set_recording_dir", "path": "D:\\\\TarotRecordings"}'
        )
        self.assertEqual(message.type, "studio_set_recording_dir")
        self.assertEqual(message.path, "D:\\TarotRecordings")

    def test_rejects_studio_set_recording_dir_without_path(self):
        with self.assertRaises(ControlMessageError):
            parse_control_message('{"type": "studio_set_recording_dir"}')

    def test_parses_studio_start_recording(self):
        message = parse_control_message(
            '{"type": "studio_start_recording", "recording_id": "rec_2026-05-30"}'
        )
        self.assertEqual(message.type, "studio_start_recording")
        self.assertEqual(message.recording_id, "rec_2026-05-30")

    def test_rejects_studio_start_recording_without_id(self):
        with self.assertRaises(ControlMessageError):
            parse_control_message('{"type": "studio_start_recording"}')

    def test_parses_studio_stop_recording(self):
        message = parse_control_message('{"type": "studio_stop_recording"}')
        self.assertEqual(message.type, "studio_stop_recording")

    def test_parses_studio_update_recording_status(self):
        message = parse_control_message(
            '{"type": "studio_update_recording_status", "recording_id": "rec_2026-05-30", "recording_state": "recording", "elapsed_ms": 12500, "dropped_frames": 2}'
        )
        self.assertEqual(message.type, "studio_update_recording_status")
        self.assertEqual(message.recording_id, "rec_2026-05-30")
        self.assertEqual(message.recording_state, "recording")
        self.assertEqual(message.elapsed_ms, 12500)
        self.assertEqual(message.dropped_frames, 2)

    def test_rejects_studio_update_recording_status_missing_field(self):
        with self.assertRaises(ControlMessageError):
            parse_control_message(
                '{"type": "studio_update_recording_status", "recording_id": "rec_2026", "recording_state": "recording", "elapsed_ms": 12000}'
            )

    def test_parses_studio_set_director_scene(self):
        message = parse_control_message(
            '{"type": "studio_set_director_scene", "scene": "wow"}'
        )
        self.assertEqual(message.type, "studio_set_director_scene")
        self.assertEqual(message.scene, "wow")

    def test_rejects_studio_set_director_scene_without_scene(self):
        with self.assertRaises(ControlMessageError):
            parse_control_message('{"type": "studio_set_director_scene"}')

    def test_parses_studio_set_audio_volume(self):
        message = parse_control_message(
            '{"type": "studio_set_audio_volume", "channel": "bgm", "volume": 0.45}'
        )
        self.assertEqual(message.type, "studio_set_audio_volume")
        self.assertEqual(message.channel, "bgm")
        self.assertEqual(message.volume, 0.45)

    def test_rejects_studio_set_audio_volume_out_of_range(self):
        with self.assertRaises(ControlMessageError):
            parse_control_message('{"type": "studio_set_audio_volume", "channel": "bgm", "volume": 1.2}')
        with self.assertRaises(ControlMessageError):
            parse_control_message('{"type": "studio_set_audio_volume", "channel": "bgm", "volume": -0.1}')

    def test_rejects_studio_set_audio_volume_invalid_channel(self):
        with self.assertRaises(ControlMessageError):
            parse_control_message('{"type": "studio_set_audio_volume", "channel": "invalid", "volume": 0.5}')

    def test_parses_studio_set_audio_mute(self):
        message = parse_control_message(
            '{"type": "studio_set_audio_mute", "channel": "mic", "muted": true}'
        )
        self.assertEqual(message.type, "studio_set_audio_mute")
        self.assertEqual(message.channel, "mic")
        self.assertTrue(message.muted)

    def test_rejects_studio_set_audio_mute_invalid_format(self):
        with self.assertRaises(ControlMessageError):
            parse_control_message('{"type": "studio_set_audio_mute", "channel": "mic", "muted": "yes"}')

    def test_parses_studio_update_audio_peak(self):
        message = parse_control_message(
            '{"type": "studio_update_audio_peak", "peak_db": -15.6}'
        )
        self.assertEqual(message.type, "studio_update_audio_peak")
        self.assertEqual(message.peak_db, -15.6)
        
        # Test null peak_db
        message_null = parse_control_message(
            '{"type": "studio_update_audio_peak", "peak_db": null}'
        )
        self.assertIsNone(message_null.peak_db)


if __name__ == "__main__":
    unittest.main()
