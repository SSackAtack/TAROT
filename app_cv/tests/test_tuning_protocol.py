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

    def test_parses_background_capture(self):
        message = parse_control_message('{"type": "background_capture"}')

        self.assertEqual(message.type, "background_capture")

    def test_parses_background_clear(self):
        message = parse_control_message('{"type": "background_clear"}')

        self.assertEqual(message.type, "background_clear")

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

    def test_parses_studio_set_director_mode(self):
        message = parse_control_message(
            '{"type": "studio_set_director_mode", "mode": "auto"}'
        )
        self.assertEqual(message.type, "studio_set_director_mode")
        self.assertEqual(message.mode, "auto")

        message_manual = parse_control_message(
            '{"type": "studio_set_director_mode", "mode": "manual"}'
        )
        self.assertEqual(message_manual.mode, "manual")

    def test_rejects_studio_set_director_mode_invalid(self):
        with self.assertRaises(ControlMessageError):
            parse_control_message('{"type": "studio_set_director_mode", "mode": "invalid"}')
        with self.assertRaises(ControlMessageError):
            parse_control_message('{"type": "studio_set_director_mode"}')

    def test_rejects_studio_set_director_scene_invalid(self):
        with self.assertRaises(ControlMessageError):
            parse_control_message('{"type": "studio_set_director_scene", "scene": "invalid_scene_name"}')

    def test_parses_studio_save_timeline(self):
        # Poprawny marker z dodatkowym poprawnym polem
        message = parse_control_message(
            '{"type": "studio_save_timeline", "recording_id": "rec_123", "markers": [{"timestamp_ms": 0, "type": "recording_started", "scene": "table"}]}'
        )
        self.assertEqual(message.type, "studio_save_timeline")
        self.assertEqual(message.recording_id, "rec_123")
        self.assertEqual(len(message.markers), 1)
        self.assertEqual(message.markers[0]["type"], "recording_started")
        self.assertEqual(message.markers[0]["scene"], "table")

    def test_rejects_studio_save_timeline_invalid_format(self):
        with self.assertRaises(ControlMessageError):
            parse_control_message('{"type": "studio_save_timeline", "recording_id": "rec_123", "markers": "not-a-list"}')
        with self.assertRaises(ControlMessageError):
            parse_control_message('{"type": "studio_save_timeline", "markers": []}')

    def test_rejects_studio_save_timeline_too_many_markers(self):
        # 501 markerów
        markers = [{"timestamp_ms": idx, "type": "operator_marker"} for idx in range(501)]
        import json
        payload = json.dumps({"type": "studio_save_timeline", "recording_id": "rec_123", "markers": markers})
        with self.assertRaises(ControlMessageError):
            parse_control_message(payload)

    def test_rejects_studio_save_timeline_invalid_marker_structure(self):
        # Marker niebędący dictem
        with self.assertRaises(ControlMessageError):
            parse_control_message('{"type": "studio_save_timeline", "recording_id": "rec_123", "markers": [123]}')
        
        # Brak timestamp_ms
        with self.assertRaises(ControlMessageError):
            parse_control_message('{"type": "studio_save_timeline", "recording_id": "rec_123", "markers": [{"type": "operator_marker"}]}')
            
        # Brak type
        with self.assertRaises(ControlMessageError):
            parse_control_message('{"type": "studio_save_timeline", "recording_id": "rec_123", "markers": [{"timestamp_ms": 100}]}')

    def test_rejects_studio_save_timeline_invalid_marker_types(self):
        # timestamp_ms niebędący int (np. float)
        with self.assertRaises(ControlMessageError):
            parse_control_message('{"type": "studio_save_timeline", "recording_id": "rec_123", "markers": [{"timestamp_ms": 10.5, "type": "operator_marker"}]}')
            
        # timestamp_ms jako bool (bool jest podklasą int w Pythonie!)
        with self.assertRaises(ControlMessageError):
            parse_control_message('{"type": "studio_save_timeline", "recording_id": "rec_123", "markers": [{"timestamp_ms": true, "type": "operator_marker"}]}')
            
        # Ujemny timestamp_ms
        with self.assertRaises(ControlMessageError):
            parse_control_message('{"type": "studio_save_timeline", "recording_id": "rec_123", "markers": [{"timestamp_ms": -10, "type": "operator_marker"}]}')
            
        # Niewłaściwy typ type (nie string)
        with self.assertRaises(ControlMessageError):
            parse_control_message('{"type": "studio_save_timeline", "recording_id": "rec_123", "markers": [{"timestamp_ms": 10, "type": 123}]}')

        # Typ spoza allowlisty
        with self.assertRaises(ControlMessageError):
            parse_control_message('{"type": "studio_save_timeline", "recording_id": "rec_123", "markers": [{"timestamp_ms": 10, "type": "invalid_type"}]}')

    def test_rejects_studio_save_timeline_invalid_additional_fields(self):
        # Dodatkowe pole ma zły typ (np. list)
        with self.assertRaises(ControlMessageError):
            parse_control_message('{"type": "studio_save_timeline", "recording_id": "rec_123", "markers": [{"timestamp_ms": 10, "type": "operator_marker", "custom": [1,2]}]}')

    def test_parses_studio_set_active_decks(self):
        message = parse_control_message(
            '{"type": "studio_set_active_decks", "active_decks": ["rider-waite-smith", "zodiak"]}'
        )
        self.assertEqual(message.type, "studio_set_active_decks")
        self.assertEqual(message.active_decks, ["rider-waite-smith", "zodiak"])

    def test_rejects_studio_set_active_decks_invalid(self):
        # Brak active_decks
        with self.assertRaises(ControlMessageError):
            parse_control_message('{"type": "studio_set_active_decks"}')
        # Zły typ (nie lista)
        with self.assertRaises(ControlMessageError):
            parse_control_message('{"type": "studio_set_active_decks", "active_decks": "rider-waite-smith"}')
        # Pusta lista (mniej niż 1)
        with self.assertRaises(ControlMessageError):
            parse_control_message('{"type": "studio_set_active_decks", "active_decks": []}')
        # Zbyt wiele talii (więcej niż 3)
        with self.assertRaises(ControlMessageError):
            parse_control_message('{"type": "studio_set_active_decks", "active_decks": ["1", "2", "3", "4"]}')
        # Zły element (nie string)
        with self.assertRaises(ControlMessageError):
            parse_control_message('{"type": "studio_set_active_decks", "active_decks": ["rider-waite-smith", 123]}')

    def test_parses_autotune_start(self):
        message = parse_control_message('{"type": "autotune_start", "scenario": "three_cards"}')

        self.assertEqual(message.type, "autotune_start")
        self.assertEqual(message.scenario, "three_cards")

    def test_parses_autotune_apply(self):
        message = parse_control_message('{"type": "autotune_apply"}')

        self.assertEqual(message.type, "autotune_apply")

    def test_parses_autotune_cancel(self):
        message = parse_control_message('{"type": "autotune_cancel"}')

        self.assertEqual(message.type, "autotune_cancel")

    def test_parses_autotune_save(self):
        message = parse_control_message('{"type": "autotune_save", "name": "studio_live"}')

        self.assertEqual(message.type, "autotune_save")
        self.assertEqual(message.name, "studio_live")

    def test_rejects_invalid_autotune_scenario(self):
        with self.assertRaises(ControlMessageError):
            parse_control_message('{"type": "autotune_start", "scenario": "twenty_cards"}')

    def test_rejects_autotune_save_without_name(self):
        with self.assertRaises(ControlMessageError):
            parse_control_message('{"type": "autotune_save"}')


if __name__ == "__main__":
    unittest.main()
