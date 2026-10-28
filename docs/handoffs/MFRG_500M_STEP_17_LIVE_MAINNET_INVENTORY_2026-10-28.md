# miniFORGE 500M — STEP 17 handoff: opt-in LIVE read-only holder inventory

**Date:** October 28, 2026
**Repository:** `tgibbsz32/forgecoin`
**PR:** [#137 — opt-in live holder inventory](https://github.com/tgibbsz32/forgecoin/pull/137)
**Status:** Read-only tool, 16 synthetic tests, CI and operator instructions complete. Real Solana mint and holder identities remain unverified.

## Step sequence and repository reconciliation

At the start of this turn [Step 15 evidence intake PR #136](https://github.com/tgibbsz32/forgecoin/pull/136) was still open but mergeable; its documentation-only hold record was squash-merged to `main` as `c614491ccc6d54622e34ceb2b7707e111e94d312`. The repository had **already advanced independently through Step 16**, implementing the [opt-in live Solana mainnet provenance checker](../MFRG_LIVE_MAINNET_PROVENANCE.md) as `tools/read_mfrg_mainnet_provenance.py`. That code had successful GitHub CI as of current main `3773165be00733f3398003dc20fc803bcdb129bc` before Step 15 merge.

Step 17 deliberately **reuses**, rather than duplicates, the Step 16 six-call genesis + mint account + initialization transaction checker and extends it with a real SPL token-account inventory check requiring two RPC providers. No program addresses or source-provenance claims are invented.

## Implemented files

1. `tools/read_mfrg_mainnet_inventory.py` — operator-invoked, opt-in, **ten-read** Solana RPC procedure, with no signing or financial writes. The existing Step 16 gate performs `getGenesisHash`, `getAccountInfo`, and `getTransaction` against each of two public HTTPS origins (six calls). Step 17 requests two fresh mint `getAccountInfo` snapshots and two `getProgramAccounts` holder scans. The scans filter the original SPL Token Program to **165-byte accounts of exactly the intended mint (memcmp at offset zero)** at finalized commitment with context slot. Uses existing Step 11/12 parsers to compare exact token-account sets, balances, delegates/freeze/close authorities, freshness and mint-supply conservation; requires no discrepancy with Step 16's earlier supply.
2. `tools/test_read_mfrg_mainnet_inventory.py` — **16 no-network mocked transport tests** covering the ten-request sequence, exact program and mint filters, wrong genesis/devnet address/missing creation signature, failed initialization, supply conflict, missing/duplicated/malformed holders, altered delegation, stale slots, wrong mint, oversupply, coincidentally identical provider responses, and midstream RPC failure.
3. `.github/workflows/mfrg-live-holder-inventory.yml` — read-only GitHub Actions job exercising new synthetic tests plus Step 16 live-provenance mocks, Step 12 offline token-account accounting, Step 9/11 initialization proof and Step 10 policy/vesting/sale-disabled guards.
4. `docs/MFRG_LIVE_MAINNET_INVENTORY.md` — exact opt-in PowerShell invocation, limits and network/accounting provenance warnings; explains that a `getProgramAccounts` response exceeding 2MB or blocked by provider rate limits fails closed rather than saying there are zero holders.
5. `docs/index.md` — adds navigation link to Step 17 procedure.
6. This numbered `STEP_17` handoff.

## Verification performed

PR review head `913837cb0007b95dca67f8be81beef6bb74d587a` passed:
- [New Step 17 opt-in holder inventory CI #40723733698](https://github.com/tgibbsz32/forgecoin/actions/runs/40723733698) — **success**, no live Solana queries in CI.
- [Existing Step 16 opt-in mainnet provenance tests #40723733350](https://github.com/tgibbsz32/forgecoin/actions/runs/40723733350) — **success**.
- [Existing mint initialization evidence tests #40723733456](https://github.com/tgibbsz32/forgecoin/actions/runs/40723733456) — **success**.

**This handoff commit follows those passing tests.** Check the CI results for the **final PR head commit** and merge status before declaring Step 17 merged. A mock transport is not a real external blockchain audit or mainnet issuance proof.

## What is and is not verified

The strongest positive finding available to the script is only: two user-selected, TLS-connected public HTTPS RPC services *reported* the expected genesis and mutually consistent mint initialization and supply data, with **both reported** full filtered SPL token-account arrays summing to their reported mint supply and agreeing on each listed token account. The code does **not** cryptographically prove that the providers are independent or honest, that every real token account was enumerated, or that a given token account belongs to the project.

The output explicitly reports **false** for RPC cryptographic provenance, transaction-signature cryptographic verification, independent provider identity, independent account-scan completeness, issuer/beneficial ownership, nine-treasury custody evidence, founder vesting funding and sale/issuance authorization.

The script requires the real **owner-authenticated existing mFRG mainnet mint address** and genuine mint initialization transaction signature. Those identifiers **remain unavailable** in verified project data; do not substitute the recorded devnet test address or pretend the 500M budget is minted. This step made no real mainnet RPC calls.

## Tokenomics preserved

500M intended SPL mFRG total at six decimals. Nine budgets: **50M lifetime fundraising** (only **5M initial pilot cap**), 100M operations, 100M ecosystem, 85M finite staking rewards, 60M liquidity, 65M engineering/security, 15M founder immediate/unrestricted if actually distributed at launch, another 15M **team-labeled but same founder beneficial owner** subject to proposed 625k/month vesting at ends of months 13–36, and 10M emergency. **Founder total intended beneficial ownership: 30M / 6%.**

No actual token creation, mint authority change, 3/5 or 4/5 multisig deployment, account funding, transfer, founder vesting, staking, sale/USDC/SOL checkout, on-chain liquidity, native FRG mainnet or consensus change occurred.

## NEXT — STEP 18: authenticated holder-to-purpose reconciliation

1. Obtain the genuine existing mFRG mainnet **mint public key and mint initialization signature** from owner-authorized public deployment records, not a ticker or logo.
2. After independent verification of those exact identifiers, execute `python tools/read_mfrg_mainnet_inventory.py --mint ... --signature ... --rpc-one https://... --rpc-two https://...`. Record external provider source and UTC slot details; protect credentials and never request seeds.
3. Corroborate reported account list and mint signature using independent trusted Solana public explorers or other verifiable chain history, including token account owners, program-derived authorities and existing non-project holders.
4. Tie actual treasury or founder address claims to owner-backed cryptographic/governance and beneficial-owner attestations before claiming nine allocations are funded; Step 13 signed consent, Step 14 SPL multisig and PDA tests are not automatic ownership proofs.
5. If the real mint exists with immutable supply below 500M, stop any claim of 500M issued and obtain a separate publicly disclosed migration/policy decision. No sale/issuance or treasury transactions without security/legal and owner approvals.

**Workflow convention:** Each subsequent "continue" should complete the next testable step with GitHub CI, an auditable numbered handoff, and a clear record of actions not performed.
