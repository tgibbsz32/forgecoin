# miniFORGE 500M — Step 27 handoff: signed offline checkpoint chain

Date: October 28, 2026. Repository: tgibbsz32/forgecoin.

## Delivered
- `tools/mfrg_signed_checkpoint_chain.py`: validates domain-separated Ed25519 signatures on a contiguous linked record chain with previous-checkpoint SHA-256, sequence numbers, declared ledger/backup SHA-256, consumed and result counts. Requires a caller-provided checkpoint anchor, checks it appears in the chain and rejects truncation below the anchor, tampering, gaps, replayed entries and decreasing consumed counts.
- Ten adversarial/success synthetic tests with generated ephemeral keys; Step 26 regression CI.
- New workflow and this handoff.

## Crucial limitations
This tool does NOT produce checkpoints, hash live ledger bytes, compare signed hashes to restored files, authenticate the pinned signer or independent anchor, or anchor anything externally. An attacker controlling the anchor and public key can create a convincing but false chain. A valid signed sequence cannot prove a real mainnet mint, RPC integrity, treasury custody, owner identity, multisig/PDA rights or beneficial ownership. The anchor must be independently authenticated and stored outside the local database; this prototype provides only *verification of submitted signed records*. Do not use for production funds or security-critical authorization.

## NEXT — STEP 28
Add a strict local ledger-to-signed-checkpoint binding validator and a read-only signed checkpoint creation workflow with externally approved signer provisioning, then test honest restore and altered data. Keep live mint and treasury verification holds. Intended SPL mFRG remains 500M, 50M fundraising lifetime (5M pilot), same-founder 30M/6%, nine budgets; native FRG unchanged.
