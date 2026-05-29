import unittest

from tarotvision.audit_policy import should_reverify


class AuditPolicyTest(unittest.TestCase):
    def test_reverifies_when_suspicious(self):
        self.assertTrue(
            should_reverify(
                frame_index=100,
                last_verified_frame=95,
                interval_frames=120,
                suspicious=True,
            )
        )

    def test_reverifies_on_interval(self):
        self.assertTrue(
            should_reverify(
                frame_index=240,
                last_verified_frame=100,
                interval_frames=120,
                suspicious=False,
            )
        )

    def test_skips_when_recent_and_not_suspicious(self):
        self.assertFalse(
            should_reverify(
                frame_index=150,
                last_verified_frame=100,
                interval_frames=120,
                suspicious=False,
            )
        )


if __name__ == "__main__":
    unittest.main()
