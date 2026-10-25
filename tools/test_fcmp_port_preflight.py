"""Offline tests for FCMP++ source-presence guard; never execute a daemon."""
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from tools import fcmp_port_preflight as probe


class FcmpSourceInventoryTests(unittest.TestCase):
    def test_unported_fork_is_incomplete(self):
        with tempfile.TemporaryDirectory() as td:
            report = probe.inspect(Path(td))
            self.assertEqual(report["present_count"], 0)
            self.assertFalse(report["source_presence_complete"])

    def test_all_markers_report_presence_without_security_claim(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for spec in probe.SURFACES:
                target = root / spec.path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(spec.marker or "existing source", encoding="utf-8")
            report = probe.inspect(root)
            self.assertEqual(report["present_count"], len(probe.SURFACES))
            self.assertTrue(report["source_presence_complete"])
            self.assertNotIn("audited", report)

    def test_require_integrated_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as td, redirect_stdout(io.StringIO()) as out:
            result = probe.main(["--fork-root", td, "--require-integrated"])
            self.assertEqual(result, 2)
            payload = json.loads(out.getvalue())
            self.assertTrue(payload["not_an_audit"])
            self.assertTrue(payload["not_a_release_approval"])
            self.assertFalse(payload["fork"]["source_presence_complete"])

    def test_wrong_upstream_pin_is_rejected(self):
        with tempfile.TemporaryDirectory() as fork, tempfile.TemporaryDirectory() as upstream:
            with patch.object(probe, "commit_of", return_value="0" * 40):
                with redirect_stdout(io.StringIO()) as out:
                    result = probe.main(
                        ["--fork-root", fork, "--upstream-root", upstream]
                    )
            self.assertEqual(result, 3)
            payload = json.loads(out.getvalue())
            self.assertFalse(payload["reference_checkout"]["pinned_commit_matches"])

    def test_marker_change_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            spec = probe.SURFACES[0]
            path = Path(td) / spec.path
            path.parent.mkdir(parents=True)
            path.write_text("no cryptographic verifier here", encoding="utf-8")
            result = probe.inspect(Path(td))
            self.assertFalse(result["surfaces"][0]["present"])


if __name__ == "__main__":
    unittest.main()
