"""End-to-end nonbinding governance rehearsal with a signed disposable wallet."""
import base58
import os
import tempfile
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from nacl.signing import SigningKey
from services.governance_api.app import app
from services.governance_api.admin import create_app


class FullJourneyTests(unittest.TestCase):
    def test_registration_review_snapshot_vote_and_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.dict(os.environ, {
                "FORGECOIN_GOVERNANCE_DB": os.path.join(tmp, "journey.sqlite3"),
                "FORGECOIN_ENV": "development",
                "FORGECOIN_ADMIN_ENABLED": "1",
                "FORGECOIN_ADMIN_TOKEN": "x" * 43,
                "FORGECOIN_ADMIN_REVIEWER": "reviewer-rehearsal",
            }):
                with TestClient(app, base_url="http://127.0.0.1:8765", client=("127.0.0.1", 12345)) as member, TestClient(
                    create_app(), base_url="http://127.0.0.1:8766", client=("127.0.0.1", 12345)
                ) as admin:
                    signer = SigningKey.generate()  # disposable, never funded
                    wallet = base58.b58encode(signer.verify_key.encode()).decode()
                    challenge_response = member.post("/auth/challenge", json={"address": wallet})
                    self.assertEqual(challenge_response.status_code, 200)
                    challenge = challenge_response.json()
                    signed = signer.sign(challenge["message"].encode()).signature
                    signature = base58.b58encode(signed).decode()
                    verified = member.post("/auth/verify", json={
                        "address": wallet, "nonce": challenge["nonce"], "signature": signature
                    })
                    self.assertEqual(verified.status_code, 200)
                    member_headers = {"Authorization": "Bearer " + verified.json()["access_token"]}
                    admin_headers = {"Authorization": "Bearer " + "x" * 43}
                    self.assertEqual(member.get("/me", headers=member_headers).json()["verified_roles"], [])
                    submitted = member.post("/applications", headers=member_headers, json={
                        "role": "community", "evidence_reference": "ref:rehearsal-evidence-01",
                        "statement": "Test-only community participation evidence, not a real identity."
                    })
                    self.assertEqual(submitted.status_code, 201)
                    application_id = submitted.json()["application_id"]
                    self.assertEqual(member.get("/applications/mine", headers=member_headers).json()["applications"][0]["status"], "pending")
                    review = admin.post(f"/api/applications/{application_id}/review", headers=admin_headers, json={
                        "action": "approve", "reason": "Disposable integration-test identity only"
                    })
                    self.assertEqual(review.status_code, 200)
                    self.assertIn("community", member.get("/me", headers=member_headers).json()["verified_roles"])
                    election_response = admin.post("/api/elections", headers=admin_headers, json={
                        "category": "community", "title": "Test proposal: no effects"
                    })
                    self.assertEqual(election_response.status_code, 201)
                    election_id = election_response.json()["id"]
                    self.assertEqual(member.post(f"/practice-elections/{election_id}/ballots", json={"choice":"yes"}).status_code, 401)
                    ballot = member.post(f"/practice-elections/{election_id}/ballots", headers=member_headers, json={"choice":"yes"})
                    self.assertEqual(ballot.status_code, 201)
                    self.assertFalse(ballot.json()["binding"])
                    duplicate = member.post(f"/practice-elections/{election_id}/ballots", headers=member_headers, json={"choice":"no"})
                    self.assertEqual(duplicate.status_code, 409)
                    self.assertEqual(admin.get(f"/api/elections/{election_id}/tally", headers=admin_headers).status_code, 409)
                    self.assertEqual(admin.post(f"/api/elections/{election_id}/close", headers=admin_headers, json={}).status_code, 200)
                    tally = admin.get(f"/api/elections/{election_id}/tally", headers=admin_headers)
                    self.assertEqual(tally.status_code, 200)
                    self.assertEqual(tally.json()["results"]["yes"], {"ballots": 1, "weight": 1})
                    self.assertFalse(tally.json()["binding"])
                    self.assertEqual(member.post(f"/practice-elections/{election_id}/ballots", headers=member_headers, json={"choice":"no"}).status_code, 409)


if __name__ == "__main__":
    unittest.main()
