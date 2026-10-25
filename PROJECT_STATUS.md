# ForgeCoin Project Status

## Pool and explorer completion status — October 24, 2026

The official native FRG pool is **planned, not deployed or payout-validated**. Its intended operator fee is **1% of eligible pooled rewards**; solo mining has no project-pool fee. The 100-worker target remains unverified. Tauri has local solo and user-configured XMRig pool controls, but verified official-pool integration is pending. Pool website/dashboard and standalone Pool Observer completion are pending. The recovered online explorer source still requires tests, security review, HTTPS and verified public deployment.

See the [implementation plan](docs/POOL_EXPLORER_IMPLEMENTATION_PLAN.md) for build, isolated integration, private staging, security, beta and rollout gates. No live service or successful production payout is established by this documentation update.

The initial desktop release requires both Solo and Pool mining, including verified official-pool integration while retaining custom pools. This is a release dependency, not a completed feature; see the [acceptance requirements](docs/POOL_EXPLORER_IMPLEMENTATION_PLAN.md#initial-desktop-release-solo-and-pool-are-required).

## October source recovery

The repository now includes the Tauri desktop 0.1.6, standalone read-only explorer,
and existing mainnet upgrades v17/500, v18/600 and v19/700. See
[SOURCE_RECOVERY.md](docs/SOURCE_RECOVERY.md) for provenance, exact rules and
validation limits. These are recovered implementations, not a newly tested release.
Historical Phase 3 component descriptions below refer to the Windows Forms app.

## Working components

- ForgeCoin mainnet identity and genesis block
- Version 16 consensus from height 1
- RandomX proof-of-work mining
- Eight-decimal FRG accounting
- Historical Windows Forms desktop: node, wallet, address book, solo miner, pool-miner interface and local explorer. Current Tauri scope is documented in [its README](apps/desktop-tauri/README.md); the online explorer is a separate service.
- Local-only daemon and wallet RPC defaults in the desktop application

## Completed source cleanup

- Removed inherited Monero mainnet checkpoints
- Removed inherited Monero DNS and IP seed nodes
- Added native support for eight-decimal FRG formatting
- Preserved the Phase 3 genesis, network UUID, rewards, and emission policy

## Before broad public-value use

- Obtain independent review of fork-specific consensus and wallet changes
- Publish stable seed nodes operated by more than one party
- Produce signed, reproducible release builds
- Create ForgeCoin-specific testnet and stagenet identities
- Test upgrades, reorganizations, backup recovery, and multi-node synchronization
- Establish multiple independent miners and pools
- Document the spendability and intended treatment of the genesis transaction output
