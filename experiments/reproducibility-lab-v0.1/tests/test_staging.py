import unittest

from vap_lab.engine import assert_staged_snapshot_matches
from vap_lab.source import SourceSnapshot


class StagingSnapshotTests(unittest.TestCase):
    def test_matching_staged_snapshot_is_accepted(self):
        staged = SourceSnapshot(
            digest="sha256:" + "a" * 64,
            file_count=1,
            total_bytes=12,
            entries=({"path": "solution.py", "size": 12, "sha256": "sha256:" + "b" * 64},),
        )
        assert_staged_snapshot_matches(staged.digest, staged)

    def test_changed_source_between_initial_snapshot_and_staging_is_rejected(self):
        staged = SourceSnapshot(
            digest="sha256:" + "a" * 64,
            file_count=1,
            total_bytes=12,
            entries=({"path": "solution.py", "size": 12, "sha256": "sha256:" + "b" * 64},),
        )
        with self.assertRaisesRegex(ValueError, "changed between initial snapshot and staging"):
            assert_staged_snapshot_matches("sha256:" + "c" * 64, staged)


if __name__ == "__main__":
    unittest.main()
