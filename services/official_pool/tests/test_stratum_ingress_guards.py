"""Stratum source ingress invariants, not end-to-end accepted-share proof.

No listener or payment keys may be activated by these tests.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
POOL = ROOT / "jtgrassie" / "src" / "pool.c"
HELPER = ROOT / "jtgrassie" / "src" / "frg_stratum_job_bounds.h"
NATIVE = ROOT / "tests" / "test_stratum_job_bounds.c"


def body(source, start, end):
    return source.split(start, 1)[1].split(end, 1)[0]


class StratumIngressSafety(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pool = POOL.read_text(encoding="utf-8")
        cls.helper = HELPER.read_text(encoding="utf-8")
        cls.native = NATIVE.read_text(encoding="utf-8")

    def test_login_stays_single_account_per_connection(self):
        login = body(self.pool, "miner_on_login(json_object *message, client_t *client)",
                     "static void\nminer_on_block_template(")
        self.assertIn("if (client->client_id[0] != '\\0')", login)
        self.assertIn("Already logged in; reconnect to change account", login)
        self.assertLess(login.index("Already logged in; reconnect"),
                        login.index("account_count++"))
        self.assertIn("client->client_id[32] = '\\0';", login)
        self.assertIn("char client_id[33];", self.pool)

    def test_jobs_require_authentication(self):
        submit = body(self.pool, "miner_on_submit(json_object *message, client_t *client)",
                      "static void\nminer_on_read(")
        self.assertIn("if (client->client_id[0] == '\\0')", submit)
        self.assertIn("Log in before submitting a share", submit)
        self.assertLess(submit.index("Log in before submitting"),
                        submit.index("client_find_job(client, jid)"))
        self.assertIn("Log in before requesting a job", self.pool)
        self.assertIn("Log in before setting a template", self.pool)
        self.assertIn("job_id must be exactly 32 hex characters", submit)

    def test_template_bounds_before_memory_write_or_hash(self):
        start = body(self.pool, "miner_send_job(client_t *client, bool response)",
                     "static void\naccounts_moved(")
        submit = body(self.pool, "miner_on_submit(json_object *message, client_t *client)",
                      "static void\nminer_on_read(")
        self.assertIn('#include "frg_stratum_job_bounds.h"', self.pool)
        self.assertIn("frg_stratum_job_bounds_valid(bt->block_blob_size", start)
        self.assertLess(start.index("frg_stratum_job_bounds_valid("),
                        start.index("bstack_push("))
        self.assertIn("frg_stratum_job_bounds_valid(bt->block_blob_size", submit)
        self.assertLess(submit.index("frg_stratum_job_bounds_valid("),
                        submit.index("calloc(bt->block_blob_size"))
        self.assertIn("bstack_drop(client->active_jobs);", start)
        self.assertIn("get_hashing_blob(block, bt->block_blob_size, &hashing_blob,", start)
        self.assertIn("frg_stratum_job_bounds_valid", self.helper)
        self.assertIn("blob_size - reserved_offset >= required", self.helper)
        self.assertIn("SIZE_MAX", self.native)

    def test_public_pool_identity_and_payouts_still_locked(self):
        self.assertIn("if (!frg_matches_frozen_mainnet()", self.pool)
        self.assertIn("#ifndef FRG_REVIEWED_PUBLIC_POOL", self.pool)
        self.assertIn("#ifndef FRG_TESTED_WALLET_PAYOUTS", self.pool)


if __name__ == "__main__":
    unittest.main()
