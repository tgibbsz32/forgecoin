"""Explicit binary opt-in: each run creates a new wallet and genesis database."""
import json
import os
from pathlib import Path
import tempfile
import unittest

from services.pool_research.integration_capture import run


class CandidateIntegrationTests(unittest.TestCase):
    def test_real_candidate_template(self):
        daemon = os.environ.get("FORGECOIN_DAEMON_BIN")
        wallet = os.environ.get("FORGECOIN_WALLET_CLI_BIN")
        if not daemon or not wallet:
            self.skipTest("Set both candidate binary paths to run disposable integration")
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "evidence.json"
            evidence = run(daemon, wallet, output)
            self.assertEqual(json.loads(output.read_text()), evidence)
        self.assertTrue(evidence["offline"])
        self.assertEqual(evidence["daemon_exit_code"], 0)
        self.assertEqual(evidence["template"]["height"], 1)
        self.assertEqual(evidence["template"]["seed_hash"], evidence["genesis_hash"])
        self.assertEqual(evidence["template"]["previous_hash"], evidence["genesis_hash"])
        self.assertEqual(evidence["template"]["transaction_count"], 1)
        self.assertGreater(evidence["template"]["difficulty"], 0)
        self.assertGreater(evidence["template"]["expected_reward"], 0)
        self.assertLessEqual(evidence["template"]["reserved_offset"] + 8,
                             evidence["template"]["blocktemplate_bytes"])
        self.assertEqual(evidence["incoming_connections"], 0)
        self.assertEqual(evidence["outgoing_connections"], 0)


if __name__ == "__main__":
    unittest.main()

