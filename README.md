# ForgeCoin

> **Documentation hub (2026-10-25):** [Wiki home](docs/wiki/Home.md) · [Current status](docs/wiki/Current-Status.md) · [Roadmap](docs/wiki/Roadmap.md) · [Software guide](docs/wiki/Software-Guide.md) · [Testing/release](docs/wiki/Testing-and-Release.md). The proposed fresh mainnet is **not launched**; the Oracle pool page is informational and the research share journal is **not** a payment system.

> **Current owner direction (2026-10-24):** Restored native-only fair launch: 50M FRG primary-emission reference, no allocated premine, 100% PoW miner subsidy and perpetual 0.20 FRG/block tail. The 55M/5M genesis treasury proposal is withdrawn. Native trading and user-deposit-backed Solana interoperability are future research. See [roadmap](ROADMAP.md).


![ForgeCoin mark](docs/images/forgecoin-logo.png)

> **Owner policy update (2026-10-24):** Owner policy: no automatic balance migration from the existing development chain; fresh-mainnet identity and difficulty parameters remain provisional. Native PoW miners receive 100% of block subsidy, no founder/team/ICO premine is authorized, and 0.20 FRG per-block tail emission is retained subject to source audit. Genesis output must be independently proven permanently unspendable before release. See docs/OWNER_POLICY_DECISIONS_2026-10-24.md.


> **Documentation status (2026-10-24):** The repository currently describes the public development-chain source. A separately identified fresh-mainnet candidate passed offline mining through RPC height 17 and a competing-chain reorganization repeat, but has NOT been approved or deployed. See docs/RELEASE_STATUS_2026-10-24.md.


> Source restored October 20, 2026, including the existing October 0.1.6 work.
> See [source provenance and validation limits](docs/SOURCE_RECOVERY.md).
> The current desktop is [Tauri/Rust/React](apps/desktop-tauri); the Phase 3
> Windows Forms application remains available as historical source.

ForgeCoin is an experimental, privacy-preserving, proof-of-work cryptocurrency derived from Monero v0.18.5.1. It uses RandomX CPU mining, private transactions, a two-minute target block time, and a desktop wallet that can run a node, wallet, miner, and local blockchain explorer from one application.

ForgeCoin is in the bootstrap stage. The chain is operational, but the network currently has limited independent hash power and has not received an independent security audit. Do not treat it as suitable for substantial value until multiple independent nodes and miners are operating and the release process has been reviewed.

## Current asset scope (October 2026)

**ForgeCoin V1 is native FRG only.** There is no Solana token, bridge or additional mining reward at launch. Solana market interoperability remains a **future research option**, not a commitment. The governance draft proposes native **FRG governance bonds** combined with independently verified mining participation for miner representatives; the bonding mechanism is not implemented and has no effect on native proof of work.

See [roadmap](ROADMAP.md), [zero-cost pool research](docs/ZERO_COST_MINING_POOL_RESEARCH.md), and [revised governance charter](governance-charter.md).

## Mission

ForgeCoin aims to provide private, CPU-accessible peer-to-peer digital cash that people can validate, mine, and explore on their own computers without relying on a central custodian or hosted block-explorer website.

## Network parameters

| Parameter | Value |
| --- | --- |
| Ticker | FRG |
| Atomic precision | 8 decimal places |
| Proof of work | RandomX |
| Target block time | 120 seconds |
| Difficulty window | Public development-source schedule: legacy before height 700, LWMA90 from 700; separate fresh candidate proposes LWMA from height 16 (unreleased) |
| Primary emission reference | 50,000,000 FRG |
| Initial post-genesis reward | approximately 23.84185222 FRG |
| Tail reward | 0.20 FRG per block |
| Coinbase maturity | 60 blocks |
| Mainnet P2P port | 19480 |
| Mainnet RPC port | 19481 |
| Mainnet consensus | v16 at height 1; v17 at 500; v18 at 600; v19 at 700 |
| Genesis hash | `a9651ecf2aec7c92443e7e7e8bfd4c6e6d5de3de8a52c04f9a98274d5031f9b9` |

The tail reward means total supply is not permanently capped. See [the whitepaper](docs/WHITEPAPER.md) for the emission formula, estimates, privacy model, governance limits, and risks.

## Desktop application

The current [Tauri desktop](apps/desktop-tauri) supports wallet creation/recovery,
fee review and sending, transaction history, local node operation, solo mining,
and user-configured XMRig pools. It does not embed an explorer.
The separate [read-only explorer](apps/explorer) provides block and transaction
lookup. Native sidecar binaries must be built separately; they are not committed.

The historical Windows Forms desktop is under [`apps/desktop`](apps/desktop). It includes:

- a local ForgeCoin node;
- wallet creation, recovery seed access, receiving addresses, contacts, and transfers;
- built-in RandomX solo mining and optional XMRig pool mining;
- separate node and miner status monitors;
- a decentralized local explorer for recent blocks and block or transaction lookup.

The daemon and wallet RPC bind only to loopback by default in the desktop application. P2P traffic uses TCP port 19480.

## Joining the network

New installations need the address of at least one existing ForgeCoin peer until stable project seed nodes are published. Start the daemon with `--add-peer host:19480` or enter the peer in the desktop application's Node tab. A node stores discovered peers locally for later connections.

Do not expose the wallet RPC or unrestricted daemon RPC to the public internet.

## Source layout

- `src` contains the ForgeCoin daemon, wallet, consensus, and networking code.
- `apps/desktop` contains the Windows desktop wallet and local explorer.
- `docs/WHITEPAPER.md` contains the technical and economic overview.
- `docs/NETWORK_GROWTH.md` contains the zero-cost distribution plan.
- `GOVERNANCE.md` explains how network upgrades are proposed and adopted.
- `SECURITY.md` explains responsible vulnerability reporting.

## Building

See [BUILDING.md](BUILDING.md) for this source snapshot and [PUBLICATION.md](PUBLICATION.md) before publishing. The core inherits Monero's CMake build system. Build requirements and platform-specific instructions remain under [`docs`](docs). The **current** desktop is Tauri/Rust/React and requires reviewed native sidecars; see [`apps/desktop-tauri/README.md`](apps/desktop-tauri/README.md) and the [wiki software guide](docs/wiki/Software-Guide.md). The historical Windows Forms application uses C# and is documented separately in [`apps/desktop/BUILDING.md`](apps/desktop/BUILDING.md).

Release binaries should be attached to a tagged GitHub Release instead of committed to the source repository. Publish SHA-256 checksums for every release asset.

## Project status

The current source removes inherited Monero mainnet checkpoints and seed nodes, accepts ForgeCoin's eight-decimal precision at source level, and preserves the Phase 3 network identity and monetary policy. Testnet and stagenet still need ForgeCoin-specific identities before they should be advertised for public use.

## Contributing and security

Read [CONTRIBUTING.md](CONTRIBUTING.md) before proposing changes. Report security-sensitive problems using the process in [SECURITY.md](SECURITY.md); do not publish exploitable details in a public issue.

## License and attribution

ForgeCoin is distributed under the BSD 3-Clause license in [LICENSE](LICENSE). It is derived from Monero and CryptoNote code. See [NOTICE.md](NOTICE.md) for attribution and bundled-component notes.

## Planned pool and explorer delivery

The official native FRG pool (1% operator fee), Tauri official-pool integration alongside solo/custom-pool mining, pool website/dashboard, standalone Pool Observer and completed online blockchain explorer are tracked in the [implementation plan](docs/POOL_EXPLORER_IMPLEMENTATION_PLAN.md) and [roadmap](ROADMAP.md). Existing desktop controls, the offline pool-accounting model and recovered explorer source do not prove these public services are live. Tests, security review, private staging, controlled beta and operational rollout remain release gates.
