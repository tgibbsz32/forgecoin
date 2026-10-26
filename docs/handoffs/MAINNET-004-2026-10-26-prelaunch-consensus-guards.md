# MAINNET-004 — draft prelaunch lock and genesis-output exclusion

October 26, 2026. SOURCE ONLY / UNBUILT DAEMON / NOT RELEASE AUTHORIZATION.

## Proposed consensus behavior

- Mainnet may initialize the existing genesis block, but accepts no blocks beyond it. Both main-chain and alternative-chain processing reject subsequent mainnet blocks before database insertion. Opening a mainnet database already beyond genesis also fails.
- Native miner start, both core block-template overloads and miner-data requests refuse mainnet. Separate non-mainnet test identities retain their existing behavior; this patch does not authorize operating any test network.
- Independently of the temporary prelaunch lock, any mainnet spend ring referencing an output created at height zero is rejected before the output visitor/signature-input path. This proposes an explicit genesis-output exclusion, rather than claiming that an unknown key or a height-60 maturity lock proves a burn.
- Genesis bytes/hash, UUID, ports, prefixes, monetary constants and miner reward formula are unchanged. This is nevertheless a consensus-rule change requiring independent review and full native integration tests.

## Packaging safety

Manifest consensus_guard_stage=draft-unbuilt blocks both Windows Forms and Tauri packaging. Existing recorded native binary hashes predate these guards and cannot be treated as implementing them. No binaries were rebuilt or repinned. Remove the pending marker only after reviewed rebuilds, artifact audit and actual integration evidence.

## Validation completed

- Standalone C++14 policy compiled with warnings treated as errors; assertions pass for genesis, post-genesis heights, maturity height, LWMA boundary and maximum uint64, mainnet versus non-mainnet, and genesis-output exclusion.
- 17 mainnet/desktop Python checks pass, including source wiring for main/alternative routes, database refusal, native start and all three template/miner-data paths.
- 5 staging tests pass, including pending-consensus packaging rejection. Actual staging command exits BLOCKED before reading/copying sidecars.
- Native daemon/core translation units have NOT been compiled for this patch. Source-wiring tests do not substitute for block acceptance, full database/import/reorg tests or cross-platform consensus validation.

## Limits and launch decision still open

These guards affect only software built from this draft. They do not modify older distributed binaries, prevent public-source forks or prove that future launch binaries reject a premined chain. Do not simply remove the temporary lock and accept arbitrary existing block-1 descendants. A separately reviewed activation mechanism must bind the official chain to launch-time authorization, or the owner must explicitly choose a fresh final identity. No mechanism is activated here; no signer key created or accessed.

The genesis exclusion is a proposed consensus burn rule, not a historical proof that no private key exists. Review cached-input validation, fast-sync/checkpoint behavior and import paths before claiming complete enforcement in a release.

## Next acceptance work

1. Independent source/consensus review of guards and exclusion.
2. Full Windows/Linux/ARM64 native builds, followed by genesis-only checks in a separately authorized disposable environment.
3. Adversarial main/alternative/import/restart and genesis-output spend tests; no launch-chain mining.
4. Final launch authorization design and owner decision, then matching package rebuilds and release gates.

Oracle remains stopped and disabled per step-12 evidence. No daemon/miner or wallet process was launched, no private wallets/keys accessed, no server changed, and no main/feature branch merged.
