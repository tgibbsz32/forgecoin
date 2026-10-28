# miniFORGE (mFRG) 500M — STEP 14 handoff: SPL multisig/PDA custody preflight

**Date:** October 28, 2026
**Repository:** `tgibbsz32/forgecoin`
**PR:** [#133 — offline SPL multisig threshold and PDA authority preflight](https://github.com/tgibbsz32/forgecoin/pull/133)
**Status:** Offline custody structure tooling and tests developed. No on-chain funds, authority, account or sale was changed. Check final PR CI and merge state separately.

## Scope and prerequisite evidence

[Step 13](MFRG_500M_STEP_13_OWNER_PURPOSE_ATTESTATIONS_2026-10-28.md) supplied an offline Ed25519 **direct-wallet consent** checker. A multisig authority requires **separate SPL program account inspection**, and a PDA has **no private key**: it cannot make a direct Ed25519 attestation. The genuine existing mFRG Solana **mainnet mint address**, mint creation signature, total issuance, founder and treasury account beneficial ownership, wallet signers and actual multisig/PDA contracts remain unverified in this repository. This step intentionally does not invent them.

## New files and exact validation logic

1. `tools/verify_mfrg_multisig_pda.py` — read-only, **offline-only** tool accepting saved mint, token-account inventory, claimed authority and (only for SPL multisig) `getAccountInfo(jsonParsed)` authority evidence. For normal project treasury categories it checks exactly **3-of-5** distinct listed signer public keys. For the proposed emergency treasury it checks exactly **4-of-5**. Validates the standard SPL Token Program, initialized `multisig` account type, declared and observed signer-set parity, token account's reported owner key, mint and six decimals, nonzero balance within the given planned budget, and absence of a reported delegate, frozen state or close authority. Rejects stale/conflicting mint, token-account and multisig slots (>1,500 gap). These thresholds are **proposals, not ratified controls or evidence that signers exist and are independent**.
2. `tools/test_verify_mfrg_multisig_pda.py` — **20 synthetic unittest methods** checking 3/5 and emergency 4/5, incorrect signer/threshold counts, duplicate/missing signers, wrong SPL account type/program, mismatched custody keys, overbudget supply, delegated/frozen/close-authority states, historical devnet mint, stale snapshots, founder vesting misclassification, and CLI success/failure.
3. `docs/MFRG_MULTISIG_PDA_READINESS.md` — operator read-only example and exact list of preconditions for SPL multisig and program-derived custody.
4. `docs/mfrg-multisig-pda.template.json` — inert manifest with **null mint, signers and token accounts**, all production flags false. No real vault public keys introduced.
5. `docs/index.md` and `docs/MFRG_OWNER_PURPOSE_ATTESTATIONS.md` — cross-links explaining that a signed personal-wallet consent and a multisig structure check are **not substitutable**.
6. `.github/workflows/mfrg-multisig-pda.yml` — the 20 new tests plus preexisting Ed25519, SPL inventory, native mint preflight, 500M accounting, 5M pilot and founder-vesting tests, with read-only GitHub token permissions.
7. This numbered `STEP_14` handoff.

### PDA handling is explicitly blocked

For `authority_type: program_pda`, the tool only produces `BLOCKED_REQUIRE_AUTHENTICATED_PDA_DERIVATION_AND_PROGRAM_AUDIT`; it does **not** try to manufacture a fake private key or assert the address was derived correctly. An actual PDA authorization requires independently verified exact binary seeds, canonical bump, program ID, deployed code, upgrade authority, cross-program invocation controls, governance, beneficiary, and auditable vesting semantics.

The founder **15M team-labeled deferred** bucket is specifically refused as a simple SPL multisig claim, because a 3-of-5 multisig does **not** enforce unlocks in months 13–36. A separate approved, funded, independently audited vesting contract is required.

## CI evidence and correction

- An initial branch test [#40715358468](https://github.com/tgibbsz32/forgecoin/actions/runs/40715358468) **failed one test** because the test fixture intended as a *different* signer was accidentally the same signer public key already in the set. This was **a fixture error**, not a reported production on-chain issue.
- Corrected in commit `fc461ac263da8ca660fdd2a1c2ef265a72571534` using a genuinely different valid Solana public key, and reran:
  - [Step 14 multisig/PDA CI #40715503597](https://github.com/tgibbsz32/forgecoin/actions/runs/40715503597) — **success**.
  - [Step 13 owner-purpose CI #40715503647](https://github.com/tgibbsz32/forgecoin/actions/runs/40715503647) — **success**.
  - [Step 12 inventory regression CI #40715503606](https://github.com/tgibbsz32/forgecoin/actions/runs/40715503606) — **success**.
- This handoff commit is after those passing tests. **Final exact-head CI must pass before merge.** No independent security audit of a future mainnet custody program is represented as completed.

## Tokenomics policy preserved, not proven minted

| Budget | Proposed mFRG |
| --- | ---: |
| Fundraising **lifetime total** | 50,000,000 |
| Fundraising **initial pilot maximum** (subset, not added supply) | **5,000,000** |
| Operations | 100,000,000 |
| Ecosystem | 100,000,000 |
| Finite staking/participation | 85,000,000 |
| Liquidity | 60,000,000 |
| Engineering, security and audits | 65,000,000 |
| Founder unrestricted once **actually distributed** at legitimate launch | 15,000,000 (3%) |
| Team-labeled, beneficially owned by **same founder**, vesting 625,000 monthly ends of months 13–36 | 15,000,000 (3%) |
| Emergency | 10,000,000 |
| **Nine allocation total** | **500,000,000** |

Founder beneficial control is **30M / 6%**, rather than 3% founder plus 3% independent team. The projected 500M total supply is not an independently verified mainnet mint balance. The 50M **lifetime** fundraising allocation does **not** widen the 5M first-pilot hard cap.

## What this step did NOT do

- No verified mainnet mFRG mint ID, actual holder inventory, funded multisig account, ratified list of five independent signers, program ID or PDA.
- No project or founder custody, verified beneficial ownership, contract upgrade authority, vault funding, staking, exchange, LP or audited vesting deployment.
- No signed transaction, token minting, moving tokens, delegating authority, revoking a signer, collecting USDC/SOL or enabling payment/checkout.
- No changes to native FRG PoW, tail emission, consensus or mainnet daemon.

## NEXT — Step 15: authenticated mainnet identity and actual custody evidence

1. Retrieve the **real existing mFRG mainnet mint public key and creation transaction signature** from authorized issuance records, not a name/ticker search. Owner-approved sources must not expose secret keys, backups or mnemonics.
2. Authenticate actual **mainnet** RPC and independent explorer records; compare current supply, six decimals, mint/freeze authorities and token accounts with Steps 9, 11 and 12. A previously revoked mint authority **cannot** mint additional tokens, even if proposed policy targets 500M.
3. For each claimed account, distinguish direct key consent (Step 13), SPL multisig structural state (Step 14), PDA/vesting program control (requires actual derivation + audit), and ultimately legal beneficial ownership. Cryptographically authentic keys do not establish independent human signers.
4. If public keys and program bytecode can be independently authenticated, prepare **separate** approved treasury/vesting authority records and real custody integration tests; otherwise remain read-only.
5. Keep 5M pilot sale limit, 500M proposed supply, nine budgets, founder 6% disclosure, and disabled production payment/mint/vesting/staking gates intact.

**Continuation rule:** each subsequent user “continue” completes one testable implementation step, commits a numbered handoff, validates GitHub CI, and stops.
