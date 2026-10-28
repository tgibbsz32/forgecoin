# miniFORGE (mFRG) — treasury provisioning and founder vesting readiness

**October 28, 2026 · Step 10 / offline planning only**

This runbook is a **non-transactional implementation specification**, not evidence that any mFRG mint, treasury, payment facility, founder transfer, staking account, vesting contract, or approval exists on Solana mainnet. The project's 500M mFRG proposal is recorded in [lifetime tokenomics](MFRG_LIFETIME_TOKENOMICS_500M.md). The [mint-verification procedure](MFRG_SOLANA_MINT_VERIFICATION.md) remains the prerequisite to every real on-chain action.

## 1. Nine separately accountable token inventories

| Treasury / beneficial holder | Planned mFRG | % | Operational status |
| --- | ---: | ---: | --- |
| Lifetime cryptocurrency-fundraising inventory | 50,000,000 | 10% | Unfunded / unverified; **5M first-pilot cap** |
| Long-term operations | 100,000,000 | 20% | Unfunded / unverified |
| Ecosystem grants | 100,000,000 | 20% | Unfunded / unverified |
| Participation/staking rewards | 85,000,000 | 17% | Unfunded / unverified; finite |
| Liquidity reserve | 60,000,000 | 12% | Unfunded / unverified; matching assets required |
| Engineering, audits, security | 65,000,000 | 13% | Unfunded / unverified |
| **Founder immediate / freely transferable at actual launch** | **15,000,000** | **3%** | No verified transfer |
| **Founder-beneficial allocation labeled “team,” vesting months 13–36** | **15,000,000** | **3%** | No funded vesting contract |
| Emergency reserve | 10,000,000 | 2% | Unfunded / unverified |
| **Total intended fixed supply** | **500,000,000** | **100%** | **Not an on-chain attestation** |

Both 3% founder categories have the **same beneficial owner**. The team label does **not** refer to independently owned employee awards. If future independent contributors receive tokens, they must come from a separately authorized and disclosed grant or budget allocation.

The proposed separate **external crypto proceeds** ledger for SOL, USDC or other legitimately received assets is not counted in the 500M mFRG inventory. Do not double-count mFRG already distributed, staking escrow, or liquidity positions held by third-party programs.

## 2. Exact founder vesting contract design

**Unrestricted 3%:** 15,000,000 mFRG is immediately transferable only once it has actually been issued/transferred in accordance with the launch distribution. *Unrestricted does not mean already received*.

**Vested 3%:** A distinct 15,000,000 mFRG must be secured in an audited escrow under the founder's beneficiary address. There is no release of this portion in months 1–12. There are **24 irrevocably scheduled installments of 625,000 mFRG**, at the **end of each numbered calendar month 13, 14, …, 36** measured from a ratified UTC launch timestamp.

| Boundary relative to launch | New deferred mFRG vested | Cumulative deferred | Total founder-accessible after valid funding |
| --- | ---: | ---: | ---: |
| Launch (T0) | 0 | 0 | 15,000,000 |
| End month 12 | 0 | 0 | 15,000,000 |
| End month 13 | 625,000 | 625,000 | 15,625,000 |
| End month 24 (year 2) | 625,000 | 7,500,000 | 22,500,000 |
| End month 36 (year 3) | 625,000 | 15,000,000 | 30,000,000 |
| Later | 0 | 15,000,000 | 30,000,000 |

**Date arithmetic:** A monthly unlock anniversary is calculated directly from the *original UTC T0*, using calendar-month addition. For dates that do not exist in the target month (for example, January 31 to February), clamp that single anniversary to the target month's last day. Do not base the next anniversary on the prior clamped date. This prevents permanently drifting to February 28 or 29. The tests include leap years and month-end recovery. Each unlock's timestamp and amount must be verifiable from the deployed contract.

**No calendar date is currently approved as T0.** An example simulation date is a test, not an issuance or vesting authorization.

The escrow contract must prevent premature admin withdrawal, unauthorized beneficiary changes, upgrades that bypass locks, overflow or underflow, duplicate claims, time manipulation and loss of principal. Its upgrade authority, pause/recovery process, escrow controls and claim rights require independent security assessment and public disclosure before deployment.

## 3. Read-only registry and planning validator

This implementation adds [an inert nine-account template](mfrg-treasury-registry.template.json) containing **null** mint address, launch date, vault addresses, owner authorities and verified balances. Every custody, audit, funding and legal permission flag is **false**.

Use locally from repository root:

```sh
# Verify all nine budget and custody placeholders; no RPC or wallet access.
python3 tools/mfrg_treasury_vesting_preflight.py

# Optional hypothetical simulation only; NOT a launch declaration.
python3 tools/mfrg_treasury_vesting_preflight.py \
  --hypothetical-launch-utc 2026-11-01T00:00:00Z \
  --as-of-utc 2028-11-01T00:00:00Z

# Synthetic tests of month boundaries, 500M totals, strict 5M pilot cap and failure modes.
python3 tools/test_mfrg_treasury_vesting_preflight.py
```

The output always states `mint_independently_verified: false`, `sale_or_issuance_authorized: false`, and `all_nine_accounts_funded_verified: false`. A successful run validates only **planning-file internal consistency**. There are no network, filesystem write or financial functions in the script.

If authentic on-chain information becomes available, store verified inventory and authority evidence **separately from this inert example** and build an independently tested verification module. Do not make this test template pass by changing its flags to true.

## 4. Execution prerequisites still outstanding

1. Obtain actual **owner-authorized mainnet mFRG mint address**, authenticated issuance record and independent Solana mainnet RPC reads. The historical devnet mint is not usable as mainnet identity.
2. Reconcile actual supply and mint/freeze authorities with intended **500M at six decimals**, and determine whether an existing mint can lawfully and technically support the plan. A previously revoked mint authority cannot be restored.
3. Identify genuine founder beneficiary address and project-controlled signer/multisig public addresses; define independent signer roles, transaction authorization thresholds and custody recovery plan. **Do not collect private keys, mnemonics or wallet backups**.
4. Obtain contract implementation and independent audit for the 15M deferred-founder escrow. Confirm all 24 unlocks and last-day calendar rules; a staged-funding plan must not permit hidden early releases.
5. Establish actual nine accounts and on-chain proof of their assigned balances **only after** owner authorization, supply reconciliation and security controls.
6. Adopt financial, risk, tax and legal controls before any solicitation or mFRG-for-USDC/SOL exchange. Remember the **50M lifetime inventory is not the initial 5M pilot**.
7. Keep the existing website checkout, payment collection, quotes and fulfillment **disabled**; don't deploy the older unreviewed Rust sale prototype from PR #122.
8. After real mint and custody evidence exists, write a separate treasury deployment specification, multisig policy, account verification tests and a new numbered handoff.

## 5. Release gates

**This step may be merged on a passing offline CI run.** It should not require mainnet credentials, wallet funding or transfer approvals. It must not be portrayed as a treasury deployment.

**Following step:** verify the actual user-controlled SPL mint and existing token holders; only then prepare real treasury provisioning and independently audited vesting contracts. If no mint evidence can be obtained, stop on-chain work, preserve current proposal and complete testing/documentation only.

The native FRG chain and its RandomX mining issuance remain unchanged by these files.
