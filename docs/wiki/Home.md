> **Current specification — 2026-10-26:** [Frozen mainnet parameters, tokenomics and release status](../CURRENT_MAINNET.md). Public launch is not authorized. Main-branch executables still implement legacy rules; these instructions are not proof of new-mainnet compatibility.

# ForgeCoin documentation hub

**Project:** ForgeCoin (FRG) — experimental, Monero-derived, privacy-oriented, RandomX proof-of-work cryptocurrency.

**Last evidence review:** 2026-10-25. **Release state:** development / prelaunch validation. An older ForgeCoin development chain and explorer exist; **the frozen October 26 mainnet has not launched**. Do not mistake the legacy chain's `mainnet` network-type label for authorization or validation of the new chain.

> **Safety:** No new-mainnet genesis, real mining, block submission, public share crediting or payouts are authorized by this documentation. The hosted `/pool/` page is a readiness page, **not a working public mining pool**.

## Start here

| Page | Purpose |
| --- | --- |
| [Current status](Current-Status.md) | What has been implemented, what was demonstrated, what is live, and what is blocked |
| [Roadmap and release gates](Roadmap.md) | Prioritized milestones, dependencies and explicit acceptance criteria |
| [System architecture](Architecture.md) | Consensus, daemon, desktop, wallet, explorer, pool-research and hosted components |
| [Software and operator guide](Software-Guide.md) | Components, prerequisites, development commands and safety expectations |
| [Testing and release verification](Testing-and-Release.md) | Reproducible test commands, artifact evidence and release holds |
| [FAQ](FAQ.md) | Answers to common miner, wallet, privacy, fee and launch questions |
| [Maintaining this documentation](Maintaining-the-Wiki.md) | Source-of-truth rules, status evidence, ownership and change procedure |

## Essential source documents

- [Project overview](../../README.md) · [Original detailed roadmap](../../ROADMAP.md) · [Existing project status](../../PROJECT_STATUS.md)
- [Native source build guide](../../BUILDING.md) · [Tauri desktop README](../../apps/desktop-tauri/README.md)
- [Pool research README](../../services/pool_research/README.md) · [Pool/explorer implementation plan](../POOL_EXPLORER_IMPLEMENTATION_PLAN.md)
- [Owner policy decisions](../OWNER_POLICY_DECISIONS_2026-10-24.md) · [Whitepaper](../WHITEPAPER.md)
- [Fresh-mainnet release evidence](../FRESH_MAINNET_RELEASE_EVIDENCE.md) · [Oracle pool preparation handoff](../HANDOFF_ORACLE_POOL_2026-10-25.md)
- [Security policy](../../SECURITY.md) · [Contributing](../../CONTRIBUTING.md) · [Open issues](https://github.com/tgibbsz32/forgecoin/issues)

## Status language used throughout

- **Implemented in source:** code or UI exists, but may still fail in real deployments.
- **Tested (isolated):** a specific reproducible test passed; not a production claim.
- **Deployed (limited):** a reachable service exists for the **old** development network or static documentation.
- **Planned / blocked:** no validated user-facing capability yet.
- **Released:** only when approved binaries, independent verification, security review and published release evidence satisfy documented gates.

This hub is version-controlled in `docs/wiki/` so changes can be reviewed alongside code. It is **not yet published into the separate GitHub Wiki tab**; that wiki repository must be initialized/enabled separately before mirroring these pages. The Markdown page names and links are designed for migration.
