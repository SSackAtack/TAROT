import tempfile
import unittest

from tarotvision.profile_store import ProfileStore


class ProfileStoreTest(unittest.TestCase):
    def test_save_and_load_profile(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ProfileStore(tmpdir)
            store.save("studio_day", {"LOCK_DEAD_ZONE_POS": 3.5})

            profile = store.load("studio_day")

        self.assertEqual(profile["LOCK_DEAD_ZONE_POS"], 3.5)

    def test_rejects_path_traversal_name(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ProfileStore(tmpdir)

            with self.assertRaises(ValueError):
                store.save("../bad", {"LOCK_DEAD_ZONE_POS": 3.5})

    def test_rejects_unknown_parameter(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ProfileStore(tmpdir)

            with self.assertRaises(ValueError):
                store.save("studio_day", {"UNKNOWN_PARAM": 1.0})


if __name__ == "__main__":
    unittest.main()
