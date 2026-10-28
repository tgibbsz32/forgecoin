# miniFORGE 500M — STEP 08 handoff: safe offline sale-backend reconciliation

**Date:** October 28, 2026
**Result:** Completed and merged; **NO token sale or on-chain financial functionality activated.**

## Source control and test evidence

- **Merged PR:** [#127](https://github.com/tgibbsz32/forgecoin/pull/127)
- **Merged commit:** `913230dc222e08fdeaace2b13df06e7fcc97970c`
- **Reviewed PR head:** `d2ac1ea3dba54af6dee5e89191aae9f272c4079f`
- **Successful PR CI:** [miniFORGE disabled sale prototype tests, run #40657233300](https://github.com/tgibbsz32/forgecoin/actions/runs/40657233300), completed with result `success`.
- **Prior handoff:** [Step 07](MFRG_500M_STEP_07_SALE_PROTOTYPE_RECONCILIATION_2026-10-28.md) / older [PR #122](https://github.com/tgibbsz32/forgecoin/pull/122). PR #122 remains an **old and conflicting draft** and should NOT be merged as-is.
- **Scope:** Exactly eight files in #127, none in `docs/` website source, native FRG consensus code, Rust/Anchor escrow or wallet-signing code.

## Critical three-number distinction

| Economic definition | mFRG | Six-decimal atomic units | Use |
| --- | ---: | ---: | --- |
| **Total fixed supply target** | 500,000,000 | 500,000,000,000,000 | Project policy; not independently verified mainnet supply |
| **Lifetime fundraising allocation** | 50,000,000 | 50,000,000,000,000 | Multiround maximum, not available to one escrow |
| **Initial pilot sale maximum** | 5,000,000 | 5,000,000,000,000 | Unchanged **SQLite and offline order/escrow cap** |

The planned 500M allocation retains nine separate categories, including 30M (6%) **founder-beneficial mFRG**, of which 15M is immediately liquid and 15M is team-labeled but belongs to the **same founder**, vesting at 625k per month from months 13–36. The backend does not distribute those tokens.

## Files brought forward safely from obsolete PR #122

1. `apps/sale/sale_core.py`: nine allocation constants totaling 500M; distinct `SALE_TREASURY_TOKENS=50M`, `PILOT_SALE_TOKENS=5M`, and `MAX_SALE_ATOMIC=5M × 10^6`; existing public-key validation, exact integer arithmetic and pure receipt-verification test primitives. **Production payment collection remains False.**
2. `apps/sale/sale_ledger.py`: disposable **test-only** SQLite quote and reservation ledger. Table-level `mint_units<=5000000000000` and application-level `MAX_SALE_ATOMIC` preserve the initial 5M pilot hard limit. Simulations support expiry, prevention of double reservations, recorded payment signatures, late-payment refund review and no automated fulfillment. No real payments accepted.
3. `apps/sale/wsgi.py`: read-only API, GET `/api/v1/status` and `/api/v1/allocations`; all POST methods reject. Returns nine 500M allocations, 50M lifetime inventory and **5M pilot** as distinct values. Mainnet mFRG minted amount is **unknown (`null`)**, not a purported observed zero. No accepted payment asset, on-chain mint address, price or authorized date.
4. `apps/sale/tests/test_sale.py`: previous adversarial offline receipt, quote, expiry, inventory and anti-replay tests retained and updated, plus 500M/50M/5M separation checks.
5. `apps/sale/tests/test_site.py`: aligns with the published 500M website and verifies strict no-sale status, founder 6% beneficial disclosure, assets, checkout disabled and API/static status consistency.
6. `apps/sale/tests/test_browser.cjs`: read-only wallet connection simulation; no signature or payment, even when status is tampered with.
7. `apps/sale/README.md`: explicitly identifies dev/test-only scope, actual numbers and all prelaunch blockers.
8. `.github/workflows/mfrg-sale-offline.yml`: dedicated GitHub CI running Python offline backend/site tests, Node mock browser assertions and existing lifetime-policy guardrails.

## Verified tests

On PR head `d2ac1ea3dba54af6dee5e89191aae9f272c4079f`, the single CI workflow **completed successfully**. Its commands were:

```sh
python3 apps/sale/tests/test_sale.py
python3 apps/sale/tests/test_site.py
node apps/sale/tests/test_browser.cjs
python3 tools/test_mfrg_policy.py
```

This verifies offline accounting and static safety expectations; it is **not an independent security audit, real Solana finality test or authorization to offer mFRG.**

## Deliberately NOT changed

- No mainnet Solana token minted, burned, transferred, locked, distributed or migrated.
- No founder tokens released and no production vesting escrow deployed.
- No public checkout turned on; existing `docs/sale-status.json` continues with `sale_enabled/payments_enabled/quotes_enabled/fulfillment_enabled=false`, mint and price `null`.
- No Rust Anchor contract copied from legacy PR #122 into `main` and no token sale program deployed. The older Rust pilot cap in that PR remains 5M and its devnet-only build guards must not be loosened.
- No governance/financial right or yield represented as implemented.
- No native FRG supply, RandomX consensus, mining, pool or daemon settings changed.

## Next step — STEP 09

**Verify the user's actual mFRG Solana mainnet mint and treasury reality before any on-chain change.** Locate the correct, user-authorized mainnet mint address (the documented devnet mint is not proof of a mainnet asset); independently inspect token program, 6 decimals, supply, current mint authority, freeze authority, holders, verified metadata and whether authority is revocable. Reconcile the requested 500M **target** against actual mint state and test wallet setup.

If no authoritative mainnet mint is available, stop at a written checklist and preserve all disabled financial controls — do **not** assume token absence or create a replacement mint.

The next economic implementation would be **custody and founder vesting specification** (15M liquid, 15M months 13–36), followed by qualified legal/tax and independent security reviews before any token-for-crypto sale, audited atomic swap or staking service.

**Handoff rule:** Every completed step gets a numbered `docs/handoffs/MFRG_500M_STEP_NN_YYYY-MM-DD.md` describing exact files/PR/commit, tests actually run, unperformed financial actions and the immediate next step.
