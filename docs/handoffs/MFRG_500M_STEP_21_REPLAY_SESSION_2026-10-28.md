# mFRG 500M — Step 21 handoff: bounded offline challenge replay journal

**Date:** October 28, 2026; **repo:** tgibbsz32/forgecoin. This step is synthetic-only and does not authenticate any mainnet mFRG deployment.

## Implemented
- `tools/verify_mfrg_challenge_session.py`: checks a declared challenge session (exact mint, initialization signature, slot, token-account-to-nonce map); UTC issuance/expiry and maximum 10-minute validity, session ID and nonce replay against a persistent local JSON journal.
- On POSIX hosts uses an exclusive `fcntl.flock` to serialize one local journal and atomic file replacement after successful verification. Returns nonzero on verification failure and does not consume nonce on failure.
- Reuses Step 20 pinned trust, owner-key challenge signatures, Step 19 owner/governance claims and Step 18 account-purpose conservation. Thirteen synthetic tests plus Step 20 regressions in CI.
- No signing, new transaction, RPC calls, key generation for the project, treasury changes or sales.

## Important limitations
- **Local replay safety only.** No remote-distributed locking; operators must not use separate journals on multiple hosts. Losing or rolling back the journal destroys replay evidence. The JSON file and its parent directory need trusted local filesystem permissions and durable backups. `--now-utc` is for tests only and must never be used as a trust bypass.
- Session inputs are NOT authenticated as being issued by ForgeCoin; an arbitrary operator can construct a self-consistent session. The nonce is not bound into the Step 20 governance/owner attestation signatures, only into the account-key challenge; a trusted issuer, authenticated session delivery, live chain state and nonce lifecycle are still required.
- Only single-key token-account owner claims are checked; PDA, multisig, beneficial custody and signer identity are unverified. No asserted live mint or holder inventory has been cryptographically authenticated.
- Never treat the output as a production security clearance.

## Command
`python3 -m pip install 'cryptography>=43,<47'`

`python3 tools/verify_mfrg_challenge_session.py manifest.json verified-signers.json snapshot-and-challenges.json session.json /secure/local/mfrg-journal.json --trusted-policy-sha256 OUT_OF_BAND_AUTHENTICATED_DIGEST`

## NEXT — Step 22
Build a trusted challenge issuer and authenticated issuance/expiration protocol with durable nonce reservation and anti-replay across multiple verifier processes. Independently authenticate the real mFRG mainnet mint and initialization transaction before any live ownership claim. Native FRG and mainnet parameters unchanged.

**Economic and security holds:** intended 500M supply, 50M lifetime fundraising with 5M pilot, founder same-person 30M/6%, nine treasury budgets. Production minting, issuance, staking, treasury transfers and presale remain disabled.
