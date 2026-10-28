# ForgeCoin

> **Adopted mFRG pilot sale planning figures (October 28, 2026):** 5M mFRG in five equal rounds at $0.08/$0.10/$0.12/$0.14/$0.16, yielding a **maximum $600,000 gross** if fully subscribed. Intended 80% project / 20% founder proceeds allocation ($120,000 founder total, half immediately and half over six months). These figures are **not an active offering, promised proceeds or permission to receive funds**. See [fixed pilot pricing and all nine token allocations](PILOT_PRICE_AND_USE_OF_PROCEEDS.md).


> **October 28 update:** Native FRG remains prelaunch. The separate **500,000,000 mFRG Solana token is planned but not yet deployed**. Current work focuses on deployment preflight, security and treasury controls, and native mining/wallet/pool validation. [Unified project status](docs/project-status.html). No live mFRG sale, staking or mint.

> **Current mainnet specification:** [October 26 frozen identity, tokenomics and release status](docs/CURRENT_MAINNET.md). Public launch is not authorized.

![ForgeCoin mark](docs/images/forgecoin-logo.png)

ForgeCoin is an experimental, privacy-preserving, proof-of-work cryptocurrency derived from Monero v0.18.5.1. It uses RandomX CPU mining, private transactions, a two-minute target block time, and a desktop wallet that can run a node, wallet, miner, and local blockchain explorer from one application.

ForgeCoin’s selected October 26 mainnet is genesis-frozen and unlaunched. The old chains are retired. Main-branch runtime code still reflects the legacy implementation; new-mainnet source remains under review in draft PR #111.

## Current assets and mFRG economic policy (October 28, 2026)

**ForgeCoin (FRG)** is the separate native RandomX-mined privacy chain. Its **50,000,000 FRG primary-emission reference is not a hard cap**; the documented consensus has a 0.20 FRG per 120-second block tail reward. Native mainnet activation is still gated by public-release checks.

**miniFORGE (mFRG)** is a separate proposed Solana SPL token with **500,000,000 target fixed supply** (6 decimals). Allocations: 50M (10%) staged crypto-denominated fundraising; 100M (20%) long-term operations; 100M (20%) adoption; 85M (17%) staking/participation; 60M (12%) liquidity; 65M (13%) engineering/security; **15M (3%) founder unlocked at launch**; **15M (3%) founder-beneficial team-labeled vesting, 625k monthly months 13–36**; 10M (2%) emergency.

No Solana mainnet mint, fixed-supply authority, sale, staking, LP or price is verified active by this documentation. **mFRG is neither native FRG nor a wrapped, redeemable or pegged FRG asset.** See [full 500M lifetime policy](docs/MFRG_LIFETIME_TOKENOMICS_500M.md), [treasury overview](docs/MINIFORGE_SPL_TREASURIES.md), [sale readiness](docs/MINIFORGE_SALE_MECHANISM.md), [website](docs/miniforge-tokenomics.html) and [mainnet release state](docs/CURRENT_MAINNET.md).

## Mission

ForgeCoin aims to provide private, CPU-accessible peer-to-peer digital cash that people can validate, mine, and explore on their own computers without relying on a central custodian or hosted block-explorer website.

## Current network parameters

| Parameter | Frozen mainnet specification |
| --- | --- |
| Status | Prelaunch; release_authorized=false |
| Native asset | FRG, 8 decimals |
| Proof of work / target | RandomX / 120 seconds |
| Genesis nonce | 20261026 |
| Genesis hash | `4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c` |
| UUID | `bd936359-09e4-4fdb-8ec0-12fa9d6ef090` |
| Address prefixes | 190 / 191 / 192 |
| P2P / daemon RPC / ZMQ RPC | 39480 / 39481 / 39482 |
| Protocol | v1 genesis; v19 at height 1 |
| Initial / minimum difficulty | 500,000 / 400,000 |
| Adjustment | Progressive LWMA90 from height 16 |
| Primary emission reference | 50,000,000 FRG; no fixed cap |
| Initial height-1 base reward | 23.84185222 FRG before penalties/fees |
| Tail / coinbase maturity | 0.20 FRG per block / 60 blocks |

See [current mainnet specification](docs/CURRENT_MAINNET.md) for source provenance, exact tokenomics, launch blockers and the [documentation manifest](docs/mainnet.identity.json). The genesis contains 11.92092895 FRG whose permanent unspendability remains unproven.

## Desktop and joining status

Windows Forms private prelaunch create/restore tests passed as recorded in the feature-branch handoffs. Tauri compilation and a local debug installer build passed; clean-machine installation and runtime validation remain open. Mining remains locked. No official new-mainnet public peer or pool is approved. Do not use the retired peer or main-branch binaries as a new-mainnet release. Never expose wallet RPC or unrestricted daemon RPC publicly.

## Source layout

- `src` contains the ForgeCoin daemon, wallet, consensus, and networking code.
- `apps/desktop` contains the Windows desktop wallet and local explorer.
- `docs/WHITEPAPER.md` contains the technical and economic overview.
- `docs/NETWORK_GROWTH.md` contains the zero-cost distribution plan.
- `GOVERNANCE.md` explains how network upgrades are proposed and adopted.
- `SECURITY.md` explains responsible vulnerability reporting.

## Building

See [BUILDING.md](BUILDING.md) for this source snapshot and [PUBLICATION.md](PUBLICATION.md) before publishing. The core inherits Monero's CMake build system. Build requirements and platform-specific instructions remain under [`docs`](docs). The desktop application uses the .NET Framework C# compiler and expects locally built `forged.exe` and `forge-wallet-rpc.exe`; see [`apps/desktop/BUILDING.md`](apps/desktop/BUILDING.md).

Release binaries should be attached to a tagged GitHub Release instead of committed to the source repository. Publish SHA-256 checksums for every release asset.

## Project status

The current source removes inherited Monero mainnet checkpoints and seed nodes, accepts ForgeCoin's eight-decimal precision at source level, and contains legacy runtime network identity pending the separately reviewed new-mainnet implementation. Testnet and stagenet still need ForgeCoin-specific identities before they should be advertised for public use.

## Contributing and security

Read [CONTRIBUTING.md](CONTRIBUTING.md) before proposing changes. Report security-sensitive problems using the process in [SECURITY.md](SECURITY.md); do not publish exploitable details in a public issue.

## License and attribution

ForgeCoin is distributed under the BSD 3-Clause license in [LICENSE](LICENSE). It is derived from Monero and CryptoNote code. See [NOTICE.md](NOTICE.md) for attribution and bundled-component notes.

## Planned pool and explorer delivery

The official native FRG pool (1% operator fee), Tauri official-pool integration alongside solo/custom-pool mining, pool website/dashboard, standalone Pool Observer and completed online blockchain explorer are tracked in the [implementation plan](docs/POOL_EXPLORER_IMPLEMENTATION_PLAN.md) and [roadmap](ROADMAP.md). Existing desktop controls, the offline pool-accounting model and recovered explorer source do not prove these public services are live. Tests, security review, private staging, controlled beta and operational rollout remain release gates.
