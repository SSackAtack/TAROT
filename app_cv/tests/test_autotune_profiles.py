import unittest

from tarotvision.autotune_profiles import generate_candidate_profiles


class AutotuneProfilesTest(unittest.TestCase):
    def test_generates_small_safe_profile_set(self):
        profiles = generate_candidate_profiles()

        self.assertGreaterEqual(len(profiles), 5)
        self.assertLessEqual(len(profiles), 30)
        for profile in profiles:
            self.assertIn("CARD_DETECT_MIN_AREA_RATIO", profile)
            self.assertIn("CARD_DETECT_MAX_CANDIDATES", profile)
            self.assertIn("WORKSPACE_INFLATE_PERCENT", profile)

    def test_profiles_do_not_change_orb_thresholds_in_mvp(self):
        profiles = generate_candidate_profiles()

        forbidden = {"MIN_MATCH_COUNT", "RATIO_THRESH", "MIN_INLIER_RATIO"}
        for profile in profiles:
            self.assertFalse(forbidden.intersection(profile.keys()))


if __name__ == "__main__":
    unittest.main()
