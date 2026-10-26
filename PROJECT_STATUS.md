# ForgeCoin project status — October 26, 2026

The selected mainnet is genesis-frozen and **not launched**. [Current parameters and tokenomics](docs/CURRENT_MAINNET.md) are authoritative for documentation. The main branch still carries the legacy runtime implementation; the new-mainnet implementation in draft PR #111 remains unmerged. Documentation publication is not network activation.

## Completed evidence and open gates

- Frozen nonce 20261026, exact genesis hash and native Windows binary hashes recorded in the selected source manifest.
- Windows Forms create/restore passed in feature-branch handoffs; 14 mainnet/desktop source checks and 20 pool source/build guards passed in the subsequent isolated review.
- Tauri matching binary hashes and Windows imports audited; Rust/frontend builds and local debug NSIS construction passed. Installer was not installed or runtime-tested. Draft #114 contains the packaging audit update.
- Genesis output permanent unspendability, real solo/pool acceptance and payouts, funded transfers, clean-machine packaging, matching ARM64 consensus and independent security review remain unresolved.
- Old Oracle explorer and pool preparation pages are not new-mainnet infrastructure. No public pool, payout service or approved bootstrap peer is available for this identity.

## Delivery direction

The first planned post-launch integration is a user-deposit-backed, redeemable 1:1 Solana wFRG bridge. The preferred later privacy upgrade is an in-place FCMP++/CARROT hard fork preserving native FRG history and balances; a separate successor and voluntary, supply-conserving migration are the fallback. Later work includes native atomic swaps, backed private stable assets, TSS/MPC private trades, L2 settlement and L3 applications.

<small>Proposed future upgrades; implementation and timing are not guaranteed.</small>

See [roadmap](ROADMAP.md), [future architecture](docs/SOLANA_FCMP_CARROT_FUTURE_ARCHITECTURE.md), and [release gates](docs/POOL_EXPLORER_IMPLEMENTATION_PLAN.md). No mining or public launch is authorized.
