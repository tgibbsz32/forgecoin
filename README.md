# ForgeCoin

> **Current mainnet specification:** [October 26 frozen identity, tokenomics and release status](docs/CURRENT_MAINNET.md). Public launch is not authorized.

![ForgeCoin mark](docs/images/forgecoin-logo.png)

ForgeCoin is an experimental, privacy-preserving, proof-of-work cryptocurrency derived from Monero v0.18.5.1. It uses RandomX CPU mining, private transactions, a two-minute target block time, and a desktop wallet that can run a node, wallet, miner, and local blockchain explorer from one application.

ForgeCoin’s selected October 26 mainnet is genesis-frozen and unlaunched. The old chains are retired. Main-branch runtime code still reflects the legacy implementation; new-mainnet source remains under review in draft PR #111.

## Current assets, sale plans and future privacy work (October 27, 2026)

**Native ForgeCoin (FRG)** remains an independent Monero-derived RandomX Proof-of-Work cryptocurrency. The frozen October 26 mainnet identity still requires security, chain-consensus and infrastructure release verification. Native FRG has no founder/team ICO premine or Solana-issued mining rewards.

**miniFORGE (mFRG)** is a separate proposed **50,000,000 unit** Solana standard SPL token, with three non-overlapping intended allocations:
- **5,000,000 mFRG for the initial sale** (not open; no approved start/end dates, price or payment recipient).
- **5,000,000 mFRG in a separate post-sale liquidity/staking treasury**, activated only after reviewed governance, contracts and custody procedures. No staking yield is offered.
- **40,000,000 mFRG in the future issuance and development treasury**, to be released later under publicly approved controls, not minted in excess of the intended 50M total.

Governance is an **open design**. The project intends to select and publish a governance solution **before the mFRG sale concludes**. There is no currently approved fixed-size chamber, FRG bond, voting entitlement or mFRG treasury authority.

The former planned wrapped-FRG bridge was superseded by the separate miniFORGE program and is **not on the current delivery roadmap**. Later native privacy objectives remain FCMP++ and CARROT with a preferred audited in-place hard fork where feasible; future independently reviewed L1 atomic swaps, L2 settlement and possible L3 applications are research stages.

See [project roadmap](ROADMAP.md), [technical whitepaper](docs/WHITEPAPER.md), [miniFORGE sale information](docs/miniforge-sale.html), [mFRG treasury details](docs/MINIFORGE_SPL_TREASURIES.md), [future privacy architecture](docs/SOLANA_FCMP_CARROT_FUTURE_ARCHITECTURE.md), and [governance design charter](governance-charter.md).

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
