# ForgeCoin

> **Current mFRG policy (November 2026):** 50,000,000 total mFRG: 5M presale, 5M liquidity, 40M combined ecosystem/staking/collateral reserve. Proposed flat presale $0.12/mFRG; maximum $600,000 gross if all 5M sell. Proceeds: 90% project, 10% founders (half immediate, half over six months). No founder token allocation. No sale or mint authorized. [Current policy](docs/MFRG_50M_CITY_TOKENOMICS.md) · [Discover Your City](docs/discover-your-city.html).

[Current project status](docs/project-status.html) · [Security and future Tari/XMR merged-mining proposals](docs/SECURITY_51_PERCENT_AND_TARI_MERGE_MINING_2026-11-02.md).

> **Current mainnet specification:** [October 26 frozen identity, tokenomics and release status](docs/CURRENT_MAINNET.md). Public launch is not authorized.

> **November 4 release readiness:** [Desktop wallet/miner, Android wallet/miner, native pool, explorer and public deployment acceptance matrix](docs/RELEASE_READINESS_2026-11-04.md). Native FAKECHAIN transaction signature, confirmed receipt and recipient-wallet restart tests **passed**; these do **not** mean public wallet payouts or mainnet mining are enabled. Official Windows/Android public downloads and a live mining pool remain **unavailable**. No seed phrase, private key, wallet password or miner credentials should be submitted to a website or third party.

> **Windows and Android test builds, not public releases:** [Windows native wallet recovery QA #218](https://github.com/tgibbsz32/forgecoin/pull/218) created and restored a 25-word disposable wallet using a genuine hash-pinned Windows wallet RPC, then reopened it after process restart without mining. A private Windows GUI ZIP was built locally, with native sends and mining still locked. [Android RandomX QA #219](https://github.com/tgibbsz32/forgecoin/pull/219) added a one-shot native ARM64 known-answer hash test; the restricted APK and 23 JVM tests passed, but the physical ARM64 hash has not been exercised and the app still has no native FRG wallet/miner. **These tests do not authorize public mainnet activation, Oracle cutover, wallet funding or downloads.**

![ForgeCoin mark](docs/images/forgecoin-logo.png)

ForgeCoin is an experimental, privacy-preserving, proof-of-work cryptocurrency derived from Monero v0.18.5.1. It uses RandomX CPU mining, private transactions, a two-minute target block time, and a desktop wallet that can run a node, wallet, miner, and local blockchain explorer from one application.

ForgeCoin’s selected October 26 mainnet is genesis-frozen and unlaunched. The old chains are retired. Main-branch runtime code still reflects the legacy implementation; new-mainnet source remains under review in draft PR #111.

## Mission

ForgeCoin's mission is to build independently verifiable, privacy-preserving, CPU-mined peer-to-peer money on its native FRG network and extend its utility through a planned Solana miniFORGE (mFRG) token. **After native network validation and the formal adoption of governance procedures**, the project intends an independently audited **1 FRG : 1 mFRG reserve-backed bridge** for eligible assets, faster Solana-side transfers, supported decentralized-exchange (DEX) liquidity and trading, optional mFRG staking, and mFRG payments in ForgeCoin's planned **Discover Your City** game for USD-priced CITY packs.

The current proposed mFRG supply is **50,000,000 six-decimal standard Solana SPL tokens**: 5M presale, 5M liquidity and a combined 40M staking/collateral/ecosystem reserve. Native FRG's 50M primary-emission reference is not a cap because tail rewards continue. To call mFRG 1:1 FRG-redeemable, **every eligible outstanding mFRG—including presale, liquidity or reward inventories presented as backed—must correspond to one verifiably reserved native FRG**. The maximum bridge capacity cannot exceed native backing or the 50M SPL ceiling. No bridge, mint, redemption, staking, DEX liquidity or game payments are live or guaranteed; Solana does not inherit native FRG transaction privacy.

See [current tokenomics](docs/MFRG_50M_CITY_TOKENOMICS.md), [ecosystem roadmap](ROADMAP.md), [exchange design](docs/MFRG_EXCHANGE_DESIGN.md) and [Discover Your City](docs/discover-your-city.html).

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

Windows Forms private prelaunch create/restore tests passed as recorded in feature-branch handoffs. The desktop source compiles, but new-mainnet matching native sidecars and clean-machine installer acceptance remain unresolved. Tauri frontend and a local debug installer have been built, not certified for release. The Android **restricted UI preview** compiles, but deliberately contains no native FRG daemon, spending wallet or functional solo/pool miner. Native C-pool RandomX blocks, exact 1% ledger allocation and deep-reorg quarantine passed isolated FAKECHAIN tests; native **pool wallet payouts have not**. The read-only pool bridge can look up worker count/hashrate by public payout address without login, but public Pages stats stay unconnected until a reviewed backend is deployed. Public mining, network activation, payouts and official Windows/Android downloads remain prohibited. Never use retired peers or legacy binaries as a new-mainnet release; never expose wallet RPC or unrestricted daemon RPC publicly. See [release readiness](docs/RELEASE_READINESS_2026-11-04.md).

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
