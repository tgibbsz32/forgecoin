# miniFORGE (mFRG) — STEP 12 handoff: offline token-account inventory

**Date:** October 28, 2026
**Repository:** tgibbsz32/forgecoin
**Pull request:** [#131 — token-account inventory reconciliation](https://github.com/tgibbsz32/forgecoin/pull/131)
**Status:** Offline parser, synthetic tests and operator guide complete. Mainnet mint and holder identities remain unauthenticated.

## Progress from Step 11

[Step 11](MFRG_500M_STEP_11_DUAL_SOURCE_MINT_PREFLIGHT_2026-10-28.md) introduced offline comparison of two SPL mint account snapshots, but mint supply is not a holder inventory. The next separate check must ensure that all **listed** SPL token accounts have the right mint/program and their account balances add up to the mint supply, without assuming any public owner address has been identified as the founder or a project treasury.

No real mFRG mainnet mint public key or creation transaction is authenticated in GitHub. No actual mainnet RPC evidence was available for this step; **all automated test fixtures are synthetic**.

## Files changed

1. **tools/reconcile_mfrg_token_accounts.py** — read-only three-file reconciliation: one saved getAccountInfo(jsonParsed) mint snapshot plus two getProgramAccounts(withContext=true, jsonParsed) SPL Token Program scans. Checks exact mint, six decimals, unsigned integer atomic amounts, duplicate token accounts, cross-mint injection, token owner authorities, delegates, frozen status, close authority, slot gaps, conflicting records, and equality of listed account totals to observed mint supply. Delegated balances counted **once**.
2. **tools/test_reconcile_mfrg_token_accounts.py** — **21 synthetic tests**, including missing/duplicated accounts, total less than supply, mismatched balances/delegation/ownership, invalid program/mint/decimals, frozen accounts, snapshot slot conflicts, zero-supply scenario and UTF-8 BOM interoperability.
3. **docs/MFRG_TOKEN_ACCOUNT_INVENTORY.md** — PowerShell read-only instructions to collect getProgramAccounts with mint filter (memcmp offset 0), 165-byte standard SPL token accounts and withContext at finalized commitment. Warns that the public RPC service may refuse the query, that **all source labels are untrusted**, that missing responses are not evidence of zero balances, and that beneficial ownership/complete holder coverage cannot be established from these files alone.
4. **.github/workflows/mfrg-token-account-inventory.yml** — runs the 21 new tests and existing Step 9, 10, 11 / allocation and disabled-sale suites, with read-only repo permissions.
5. **docs/index.md** — navigation link to new operator instructions.
6. This **numbered Step 12 handoff**.

## Tests performed and evidence

- Initial PR head **221016559e05d0963280d34b8d2030e5d9f339fc** passed [GitHub Actions inventory workflow #40709207027](https://github.com/tgibbsz32/forgecoin/actions/runs/40709207027).
- The handoff commit follows that initial test. Review latest [PR #131 checks](https://github.com/tgibbsz32/forgecoin/pull/131/checks) and confirm success for the final head SHA **before merge**.
- CI covers offline accounting, consistency, parser edge cases and false-positive state, **not** authenticated provider integrity or a blockchain security audit.

## Accounting and founder policy preserved

| Allocation | Proposed quantity |
| --- | ---: |
| Cryptocurrency fundraising — lifetime maximum | 50,000,000 mFRG |
| **Pilot checkout cap**, distinct subset of fundraising | **5,000,000 mFRG** |
| Long-term operations | 100,000,000 mFRG |
| Ecosystem grants | 100,000,000 mFRG |
| Finite staking participation rewards | 85,000,000 mFRG |
| Liquidity | 60,000,000 mFRG |
| Engineering/security | 65,000,000 mFRG |
| Founder unrestricted when actually issued/received | 15,000,000 mFRG (3%) |
| Team-labeled deferred but beneficially owned by **same founder** | 15,000,000 mFRG (3%), 625k at ends of months 13–36 |
| Emergency reserve | 10,000,000 mFRG |
| **Nine distinct allocations total** | **500,000,000 mFRG** |

Founder beneficial control remains **30M mFRG (6%)**. The 5M pilot cap must never be raised to 50M merely because lifetime fundraising reserve is 50M. No price, sale, staking reward APY, project treasury deposit or founder release is on-chain verified by this step.

## Proven vs not proven

The **only** positive conclusion a successful validator permits is: two supplied files list the same parsed token-account records, and the sum of listed balances matches the supplied mint snapshot's raw supply. The tool reports matched account count, distinct token authority addresses, delegated and frozen account counts.

It **does not establish**:

- That source responses are genuine or came from independent Solana mainnet RPC providers.
- That the RPC applied the mint/dataSize filters or returned every token account.
- That token-account owner addresses correspond to the project's founder, multisig, treasury, LPs or vesting contracts, or that any listed token is project-controlled.
- That the intended 500M mint has actually been created, minted, is immutable, or properly distributed.
- That any account is funded or any sale, vesting contract, staking contract, exchange or liquidity feature is live.

No minting, token transfer, SOL/USDC payment, on-chain signing, account creation, founder payout, frozen-account action or FRG native mining consensus change occurred.

## Next step — Step 13

**Blocker:** First get the authentic Solana **mainnet** mFRG mint address and creation transaction from the owner's real issuance or verifiable wallet records. Then:

1. Independently authenticate two RPC mainnet providers and the mint account state (program, decimals, supply, mint/freeze authorities).
2. Obtain real finalized getProgramAccounts results, cross-check all token-account balances and verify provider completeness/authentication beyond mere identical JSON.
3. Independently verify owner/beneficial authority for every claimed treasury, founder and vesting address. Produce a separate signed **authority-to-purpose** ledger, distinguishing circulating versus reserve tokens and delegated/escrow/LP-held amounts.
4. Reconcile actual supply (which might be below the 500M policy target); if mint authority is permanently revoked below target, stop issuance planning pending explicit policy and migration decision.
5. Only after legal, security and owner-signature approvals, specify audited custody accounts and founder vesting deployments, then consider the 5M pilot sale. All production payment and signing flags must remain disabled until then.

Continue recording a numbered handoff at the end of each independently completed step.
