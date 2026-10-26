> **Current specification — 2026-10-26:** [Frozen mainnet parameters, tokenomics and release status](../CURRENT_MAINNET.md). Public launch is not authorized. Main-branch executables still implement legacy rules; these instructions are not proof of new-mainnet compatibility.

# System architecture and trust boundaries

ForgeCoin includes multiple codebases with **different maturity levels**. Do not infer that every source directory corresponds to a deployed service.

## Native blockchain and wallets

- `src/`: Monero-derived C++ consensus rules, RandomX mining, networking, daemon RPC and native wallets.
- `forged`: full node, maintains chain, validates blocks, exposes P2P and (when configured) RPC. Selected frozen-mainnet P2P is **39480**; daemon RPC is **39481**. Legacy main-branch executables do not implement this selected identity. Wallet RPC is distinct from daemon RPC.
- `forge-wallet-rpc`: local wallet process for addresses, balances and transactions. Wallet data and private keys must remain local and protected.
- `tests/`: native and fork-specific tests. Source-level changes are **not** release acceptance without cross-platform and candidate-binary test evidence.

**Critical isolation:** the Oracle daemon's publicly accessible legacy P2P endpoint is **not** a fresh-mainnet bootstrap identity. Do not expose unrestricted RPC or wallet RPC to the internet.

## Windows desktop

- `apps/desktop-tauri/`: current Tauri 2 application, Rust host/backend plus React/TypeScript UI.
- Rust owns permitted child-process launches and wallet RPC transactions; Tauri packages native sidecars whose identities must be digest-pinned and reviewed.
- The UI provides wallet, node, Solo mining, and **user-configured** Pool/XMRig controls. These features exist in code; production-compatible Solo/Pool acceptance is still a release gate.
- `apps/desktop/`: legacy Windows Forms implementation, retained for historical reference, **not** the primary current desktop implementation.

## Explorer and web frontends

- `apps/explorer/`: separate read-only block/transaction lookup service. The publicly hosted explorer corresponds to the **old** development chain.
- `apps/pool-site/`: static readiness website available at [Oracle pool page](https://150.136.209.227/pool/). It is **not** mining infrastructure.
- `docs/` also contains GitHub Pages site assets and documentation. Static pages cannot verify RandomX, sign payouts or maintain authoritative pool state on their own.

## Mining pool research

- `services/pool_research/`: synthetic Stratum-shaped protocol, fixed-work native RandomX experiments, limits, SQLite synthetic journal, offline reward models.
- A native RandomX worker is bounded and invoked by synthetic test logic. Synthetic journal writes are forced to `synthetic=1`, `credited=0`; these checks represent neither mined blocks nor financial balances.
- No approved path currently joins **public miner → canonical candidate template → independently verified share → actual block found → canonical chain maturity → authenticated payout**.
- Mining-pool research is **not** a production Stratum/payout server. Official public pool and 1% fee remain planned.

## Governance, service infrastructure and security

- `services/governance_api/`, `GOVERNANCE.md`, `governance-charter.md`: governance experiments and policy drafting. Do not treat mock/proposed votes as consensus authority.
- Oracle ARM64 VM hosts older development-chain node/explorer and static public pool page; existing live services must not be repointed or retired without verified backups and rollback.
- Trust boundaries: wallet secrets never enter website, miner telemetry or synthetic test evidence; consensus RPC must not be exposed to Internet clients; credentials are not public addresses; a published SHA-256 alone does not prove artifact origin.
- The proposed Solana bridge is **future research**, not an existing network, pool, native token issuance path, or custody service.

## Where to start investigating

| Symptom / goal | Primary code/docs |
| --- | --- |
| Node sync, difficulty, emission | `src/`, [roadmap](Roadmap.md), [fresh-mainnet evidence](../FRESH_MAINNET_RELEASE_EVIDENCE.md) |
| Windows wallet and local miner | `apps/desktop-tauri/`, [desktop guide](../../apps/desktop-tauri/README.md) |
| Block explorer issues | `apps/explorer/`, [pool/explorer plan](../POOL_EXPLORER_IMPLEMENTATION_PLAN.md) |
| Stratum protocol or share math | `services/pool_research/`, [research README](../../services/pool_research/README.md) |
| Releases and tests | [Testing and release verification](Testing-and-Release.md), [release checklist](../RELEASE_CHECKLIST.md) |
| Security-sensitive discovery | [SECURITY.md](../../SECURITY.md), not a public issue with exploit details |
