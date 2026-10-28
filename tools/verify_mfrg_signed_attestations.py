#!/usr/bin/env python3
"""Step 19 offline signed-claim verification. No RPC, keys, transfers, or authorization."""
import argparse
import base64
import json
import sys
from reconcile_mfrg_holder_purposes import reconcile, ReconciliationError, BUDGETS

DOMAIN = b"FORGECOIN-MFRG-PURPOSE-ATTESTATION-V1\\n".replace(b"\\n", b"\n")

def check(cond, message):
    if not cond:
        raise ReconciliationError(message)

def decode64(value, count):
    check(isinstance(value, str), "missing base64 signature or key")
    try:
        data = base64.b64decode(value, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise ReconciliationError("invalid base64") from exc
    check(len(data) == count, "invalid key/signature length")
    return data

def canonical(claim):
    return DOMAIN + json.dumps(claim, sort_keys=True, ensure_ascii=True, separators=(",", ":"), allow_nan=False).encode("ascii")

def verify(manifest, trust):
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    check(isinstance(trust, dict), "trust policy must be object")
    keys = trust.get("trusted_signers")
    check(isinstance(keys, dict), "trusted_signers must be explicit mapping")
    check(isinstance(manifest, dict) and isinstance(manifest.get("accounts"), list), "manifest accounts required")
    expected_mint = manifest.get("mint")
    expected_sig = manifest.get("initialization_signature")
    check(isinstance(expected_mint, str) and isinstance(expected_sig, str), "mint and initialization transaction required")
    entries = manifest.get("signed_attestations")
    check(isinstance(entries, list), "signed_attestations required")
    validated = set()
    for entry in entries:
        check(isinstance(entry, dict), "attestation must be object")
        claim = entry.get("claim")
        check(isinstance(claim, dict), "claim must be object")
        check(set(claim) == {"version","network","mint","initialization_signature","token_account","purpose","amount_atomic","role"}, "claim fields must match strict schema")
        check(claim["version"] == 1 and type(claim["version"]) is int and claim["network"] == "solana-mainnet-beta", "claim version/network mismatch")
        check(claim["mint"] == expected_mint and claim["initialization_signature"] == expected_sig, "claim mint or initialization mismatch")
        check(claim["purpose"] in BUDGETS and claim["role"] in ("owner", "governance"), "claim purpose or role invalid")
        check(type(claim["amount_atomic"]) is int and claim["amount_atomic"] >= 0, "claim balance invalid")
        identity = entry.get("signer_id")
        check(isinstance(identity, str) and identity in keys, "signer absent from independent trust policy")
        signer = keys[identity]
        check(isinstance(signer, dict) and signer.get("role") == claim["role"], "untrusted role assignment")
        public = decode64(signer.get("public_key_base64"), 32)
        signature = decode64(entry.get("signature_base64"), 64)
        try:
            Ed25519PublicKey.from_public_bytes(public).verify(signature, canonical(claim))
        except (ValueError, InvalidSignature) as exc:
            raise ReconciliationError("invalid Ed25519 claim signature") from exc
        key = (claim["token_account"], claim["role"])
        check(key not in validated, "duplicate role attestation for account")
        validated.add(key)
    # Fail closed for purpose-assigned accounts. Booleans from Step 18 are discarded.
    sanitized = json.loads(json.dumps(manifest))
    for account in sanitized["accounts"]:
        check(isinstance(account, dict), "account must be object")
        purpose = account.get("purpose")
        if purpose in BUDGETS:
            for role in ("owner", "governance"):
                check((account.get("token_account"), role) in validated, "required signed attestation missing")
                matching = [x["claim"] for x in entries if x["claim"]["token_account"] == account["token_account"] and x["claim"]["role"] == role]
                check(len(matching) == 1 and matching[0]["purpose"] == purpose and matching[0]["amount_atomic"] == account.get("amount_atomic"), "claim/account snapshot mismatch")
            account["owner_attestation_verified"] = True
            account["governance_authorization_verified"] = True
            # Beneficial ownership cannot be established solely by two signatures.
            check(account.get("beneficial_owner_verified") is True, "external beneficial-owner review required")
    result = reconcile(sanitized)
    result["status"] = "SIGNED_OPERATOR_CLAIMS_CHECKED_OFFLINE_NOT_CUSTODY_PROOF"
    result["valid_signatures"] = len(validated)
    result["signatures_checked_against_operator_trust_policy"] = True
    result["onchain_control_verified"] = False
    result["beneficial_ownership_cryptographically_verified"] = False
    return result

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("manifest")
    ap.add_argument("trust_policy")
    args = ap.parse_args()
    try:
        with open(args.manifest, encoding="utf8") as f: manifest = json.load(f)
        with open(args.trust_policy, encoding="utf8") as f: trust = json.load(f)
        print(json.dumps(verify(manifest, trust), sort_keys=True, indent=2))
    except (OSError, ValueError, TypeError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
