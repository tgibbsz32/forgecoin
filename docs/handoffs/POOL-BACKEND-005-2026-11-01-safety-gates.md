# POOL-BACKEND-005 — November 1, 2026 — native pool fail-closed safeguards

## Scope

- Prevent the jtgrassie research fork from starting with legacy ForgeCoin native address prefixes or RPC port defaults. The selected new-mainnet constants are 190 / 191 / 192 and 39480 / 39481 / 39482, but the current native source header still has the legacy values; **runtime startup is deliberately blocked**.
- Require a fixed-length eight-hex-digit nonce before parsing.
- Do not increment accepted worker/account hashrate for rejected low-difficulty work.
- Do not report/store an unconfirmed/rejected submit_block callback as a pool block.
- Do not debit wallet balances or record payments when transfer_split returns malformed JSON, an error or no transaction-hash list.
- Preserve research-only default localhost binds and disabled wallet payouts.

## Limits

No native chain activation or full daemon/XMRig acceptance test was possible in this change. The old source constants still need a separately reviewed new-mainnet consensus transition. No audited transactional payout or reorg-safe ledger exists; the legacy callback uses independent database transactions, so the pool may not send actual payments yet.

## Tests and next action

Source guard tests now assert identity, rejection and wallet callback safeguards. Run the repository's Python and C monetary tests and the ARM64/x86 native link CI. Then use an authorized disposable FRG chain and two test wallets for canonical accepted block, 60-block maturation, PPLNS conservation, 1% fee, payout retry/idempotency and reorg recovery. Never disable release guards to simulate success.
