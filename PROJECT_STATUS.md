# ForgeCoin project status — October 26, 2026

> **November 2 local recovery:** The latest recovered Windows development files, isolated test evidence, pool-settlement prototype, and exact source patch are indexed in the [local preservation handoff](docs/handoffs/local-preservation-2026-11-02/README.md). This is not mainnet launch approval; the main branch runtime still needs the frozen network integration.

> **November 2 consensus continuation:** [Draft PR #185](https://github.com/tgibbsz32/forgecoin/pull/185) integrates frozen 20261026 mainnet identity and the compiled prelaunch lock. [Native GitHub CI](https://github.com/tgibbsz32/forgecoin/actions/runs/41436434338) passed isolated genesis/block-rejection, fixed-difficulty, legacy DB refusal, native numerical difficulty, genesis ring-membership policy, and two-node localhost handshake checks. The [MAINNET-005 handoff](https://github.com/tgibbsz32/forgecoin/blob/integration/frozen-mainnet-prelaunch-20261102/docs/handoffs/MAINNET-005-2026-11-02-frozen-consensus-integration.md) records exact evidence and limits. Full signed genesis-output spending rejection, live consensus/reorg testing, and native pool payouts remain **unverified**. PR #185 is still unmerged and not authorized for launch.

> **November 2 desktop integration:** [Draft PR #186](https://github.com/tgibbsz32/forgecoin/pull/186) removes retired desktop peer defaults, retargets Tauri and Windows Forms to mainnet P2P 39480 and daemon RPC 39481, separates Windows wallet RPC **39484** from XMRig status API **39483**, and preserves selected-chain settings migration. The [desktop CI](https://github.com/tgibbsz32/forgecoin/actions/runs/41439191273) passed endpoint regressions, TypeScript/Vite and Windows Forms C# compilation. The [desktop handoff](https://github.com/tgibbsz32/forgecoin/blob/integration/desktop-retired-peer-ports-20261102/docs/handoffs/DESKTOP-IDENTITY-2026-11-02-retired-peer-wallet-rpc.md) documents remaining release gates. The Tauri Rust build is **blocked by missing reviewed native sidecars**, intentionally not bypassed. PR #186 is unmerged; no public peer is preconfigured.

The selected mainnet is genesis-frozen and **not launched**. [Current parameters and tokenomics](docs/CURRENT_MAINNET.md) are authoritative for documentation. The main branch still carries the legacy runtime implementation; the new-mainnet implementation in draft PR #111 remains unmerged. Documentation publication is not network activation.

## Completed evidence and open gates

- Frozen nonce 20261026, exact genesis hash and native Windows binary hashes recorded in the selected source manifest.
- Windows Forms create/restore passed in feature-branch handoffs; 14 mainnet/desktop source checks and 20 pool source/build guards passed in the subsequent isolated review.
- Tauri matching binary hashes and Windows imports audited; Rust/frontend builds and local debug NSIS construction passed. Installer was not installed or runtime-tested. Draft #114 contains the packaging audit update.
- Genesis output permanent unspendability, real solo/pool acceptance and payouts, funded transfers, clean-machine packaging, matching ARM64 consensus and independent security review remain unresolved.
- Old Oracle explorer and pool preparation pages are not new-mainnet infrastructure. No public pool, payout service or approved bootstrap peer is available for this identity.

## Delivery direction

After native FRG launch verification and the formal adoption of governance procedures, the project intends a **50M standard Solana SPL miniFORGE (mFRG)** token (5M presale, 5M DEX liquidity, 40M combined ecosystem/staking/collateral reserve) and an **audited 1 FRG : 1 eligible mFRG backed bridge** to support faster Solana transfers, supported DEXs, optional finite-reserve staking and purchases of CITY packs in ForgeCoin's planned Discover Your City game. Native FRG backing must independently cover every mFRG represented as 1:1 redeemable; a fixed 50M SPL supply caps bridge capacity even as FRG's tail emission continues. No mint, reserves, bridge, DEX pool, staking, game checkout or sale is verified active. The preferred later native privacy upgrade is an in-place FCMP++/CARROT hard fork preserving FRG history and balances; additional proposals include swaps, secured L2 and L3 services.

<small>Proposed future upgrades; implementation and timing are not guaranteed.</small>

See [roadmap](ROADMAP.md), [future architecture](docs/SOLANA_FCMP_CARROT_FUTURE_ARCHITECTURE.md), and [release gates](docs/POOL_EXPLORER_IMPLEMENTATION_PLAN.md). No mining or public launch is authorized.
