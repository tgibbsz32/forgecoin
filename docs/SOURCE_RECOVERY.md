> **Historical archive — superseded for current configuration.** Original evidence and decisions below retain their original dates and network parameters. Do not use old ports, genesis, balances, token proposals or release claims as current instructions. See [current mainnet specification](CURRENT_MAINNET.md) and the current roadmap.

# Source recovery â€” October 20, 2026

This publication restores the complete source tree to the existing GitHub history
and includes the previously developed October desktop, explorer and consensus work.
It does not reset a chain, deploy services, publish binaries, or introduce new
activation heights.

## Provenance

- Base: local publication snapshot `2b6139b`, derived from Monero v0.18.5.1.
  Its vendored dependencies, licenses, tests and ForgeCoin seed/checkpoint cleanup
  are retained.
- Native October source: working tree based on `0fd67570c`, including changes to
  monetary formatting, wallet fork handling, blockchain difficulty/timestamps,
  the hard-fork schedule, `forgecoin_difficulty.h`, and `tests/forgecoin`.
- Current desktop: Tauri 2 / Rust / React source version 0.1.6, under
  `apps/desktop-tauri`, including both dependency lockfiles.
- Historical desktop: Phase 3 Windows Forms source under `apps/desktop`.
- Explorer: October read-only Flask frontend/backend and deployment templates under
  `apps/explorer`. The deployment script is environment-specific; it was not run.

The publication snapshot intentionally removes inherited Monero DNS/IP seeds and
embedded checkpoint data. Those cleanups are retained instead of copying the
corresponding older files from the native development checkout.

The base includes dependency source directly, with no Git submodules.
Use `-DMANUAL_SUBMODULES=1` as described in `BUILDING.md`.
Earlier upstream and local development Git histories are not imported; copyright
notices and license files remain in the source.

## Existing mainnet upgrade schedule

| Height | Version | Existing rule |
| --- | --- | --- |
| 1 | 16 | Initial ForgeCoin consensus |
| 500 | 17 | Difficulty floor 500,000 |
| 600 | 18 | Difficulty floor 1,000,000 |
| 700 | 19 | 90-interval LWMA variant; 11-block median timestamp and 540-second future limit |

The genesis, network identity, 120-second target, eight-decimal precision,
50-million primary emission reference and eventual 0.20-per-block tail reward
are preserved. The September whitepaper predates these difficulty upgrades.

## Build and validation boundary

This is source recovery, not a freshly validated release. Prior validation reports
are retained in `docs/history`; their runtime observations describe earlier tests.
A clean native build, desktop package and end-to-end network validation from this
combined snapshot remain necessary before distributing new binaries.

Desktop sidecar executables, installers, wallet data, blockchain databases, private
credentials, caches and build outputs are deliberately excluded. Build both native
sidecars from this checkout before packaging the Tauri desktop.

## Checks performed during recovery

The standalone C++ difficulty test was freshly compiled against the recovered
source on Windows x64 and passed all 1,231 generated consensus vectors. Explorer
Python/JavaScript syntax and desktop version consistency were checked. These
checks do not replace a full build or integration run.
