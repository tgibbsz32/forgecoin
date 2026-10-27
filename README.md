# ForgeCoin

> **Current mainnet specification:** [October 26 frozen identity, tokenomics and release status](docs/CURRENT_MAINNET.md). Public launch is not authorized.

![ForgeCoin mark](docs/images/forgecoin-logo.png)

ForgeCoin is an experimental, privacy-preserving, proof-of-work cryptocurrency derived from Monero v0.18.5.1. It uses RandomX CPU mining, private transactions, a two-minute target block time, and a desktop wallet that can run a node, wallet, miner, and local blockchain explorer from one application.

ForgeCoin’s selected October 26 mainnet is genesis-frozen and unlaunched. The old chains are retired. Main-branch runtime code still reflects the legacy implementation; new-mainnet source remains under review in draft PR #111.

## Current asset scope (October 2026)

**ForgeCoin V1 is native FRG only.** There is no Solana token, bridge or additional mining reward at launch. The intended post-launch Solana asset is **mFRG**, with a proposed future FRG staking/locking and 1:1 FRG backing mechanism; no separate wFRG token is planned. After that, the project intends to research FCMP++/CARROT privacy upgrades, **preferably by hard-forking the existing L1 rather than replacing its blockchain**. A separate successor and opt-in migration are a fallback only if chain continuity is infeasible. The governance draft proposes native **FRG governance bonds** combined with independently verified mining participation for miner representatives; the bonding mechanism is not implemented and has no effect on native proof of work.

See [roadmap](ROADMAP.md), [zero-cost pool research](docs/ZERO_COST_MINING_POOL_RESEARCH.md), and [revised governance charter](governance-charter.md).

## Intended evolution: mFRG presale, later FRG-linked staking/backing, then FCMP++/CARROT

<small>Proposed future upgrades; implementation and timing are not guaranteed.</small>

**Future development only.** ForgeCoin intends to offer a distinct Solana SPL asset **mFRG**, with a separately reviewed future mechanism to stake/lock native FRG and work toward **1:1 FRG backing of mFRG** after mining and price discovery. The presale does not create FRG backing or redemption rights. After that, the preferred FCMP++/CARROT upgrade is a **coordinated in-place hard fork** preserving native FRG chain history and funds if technically sound; a separate successor and opt-in bridge/migration is the fallback. Any interim wFRG wind-down must protect redemption and outstanding reserve obligations.

Future engineering requirements: incremental authenticated curve-tree databases; consensus verification of FCMP++ membership proofs and Generalized Bulletproofs components; CARROT wallet/address and legacy-output compatibility; mempool revalidation across hard-fork activation; and a unique heavy-load stressnet. Further research includes **native atomic swaps with ETH/USDC, backed privacy-shielded synthetic stable assets, TSS/MPC-secured private block-trade routing with potential basis-point fees, L2 payment/settlement systems and L3 applications**. All require separate design, audits, custody, security and compliance reviews. Neither perfect privacy nor immediate settlement is guaranteed.

See [the full interoperability, migration and successor plan](docs/SOLANA_FCMP_CARROT_FUTURE_ARCHITECTURE.md) and [ROADMAP.md](ROADMAP.md).

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


**Revised mFRG-first policy (October 27, 2026):** No separate wFRG token is currently planned. miniFORGE (mFRG), a distinct Solana SPL asset, is intended to serve as the ecosystem's FRG-linked asset. Following the mFRG presale and a period of native FRG public mining and observed price discovery, a separately audited protocol may allow FRG holders to lock or stake native FRG for mFRG-related rights. The **target is an eventual 1:1 FRG-backed relationship**, but this is a future design goal, not an existing 1 FRG = 1 mFRG redeemability promise. Because mFRG presale tokens may circulate before FRG collateral exists, the project must define how unbacked presale supply, reserves, new issuance, redemption rights and total circulating supply will be reconciled before calling mFRG fully backed. No bridge, staking, 1:1 reserve, conversion or redemption is live; native FRG mining rules are unchanged.
