> **Current specification — 2026-10-26:** [Frozen mainnet parameters, tokenomics and release status](../CURRENT_MAINNET.md). Public launch is not authorized. Main-branch executables still implement legacy rules; these instructions are not proof of new-mainnet compatibility.

# Testing, build evidence and release gates

## Safety levels

| Level | Allowed evidence | What it does **not** prove |
| --- | --- | --- |
| Static source review | API/code inspection and documented invariants | Runnable binary, correct fork behavior or secure deployment |
| Synthetic unit test | Deterministic fixtures and mocked adapters | Real candidate block or pool share |
| Native offline test | Actual C++/RandomX arithmetic with controlled input | Native mainnet candidate equivalence, miner integration, payouts |
| Isolated integration | Disposable network, actual daemon/wallet/miner and bounded test workers | Secure/public production operation without independent audit |
| Controlled beta and release | Independently reviewed binaries, network, load, reorg, payout and incident response | Absolute security or guaranteed coin value |

**Do not skip levels**, and never count a mocked “OK” Stratum response as proof that a RandomX hash or pool payout was accepted.

## Safe, non-mining test commands

Run from a disposable checkout's root with Python 3 and no real wallet/process:

```powershell
py -m unittest tools.test_preflight_desktop_mining -v
py tools/validate_desktop_mining_evidence.py --self-test
py -m unittest services.pool_research.test_randomx_validation services.pool_research.test_stratum_protocol services.pool_research.test_ledger -v
py -m unittest services.pool_research.test_synthetic_journal services.pool_research.test_share_preflight services.pool_research.test_share_preflight_concurrency -v
py -m unittest services.pool_research.test_private_capture -v
```

All commands above target offline/synthetic behavior unless their own explicit options or environment select a native helper. Some Windows/platform-specific tests are skipped, as intended. The recorded 2026-10-25 selected Windows runs passed 21 basic and 53 additional research cases (3 skips), with another 23 passing on the [PR #27](https://github.com/tgibbsz32/forgecoin/pull/27) overlay. These are **overlapping** suites.

**Do not run ignored/integration tests blindly.** Some process-launching desktop tests normally skip and may invoke a real daemon, wallet, XMRig or external peer unless separately sandboxed. The source file name `test_*.py` is not, by itself, a guarantee of no network activity. Review the test first.

## Candidate and mining acceptance required before launch

- **Consensus:** independently verify genesis unspendability, emission math, coinbase maturity, mainnet identity, LWMA/fork transition and reorg recovery on exact candidate binaries across the target architectures.
- **Daemon:** guard loopback-only RPC, isolated/disposable data, correct service cleanup, digest/provenance and deterministic native template fields. See [#28](https://github.com/tgibbsz32/forgecoin/issues/28).
- **Job construction:** compare actual candidate full block template/hash blob, seed schedule, offsets, byte order, target and session identity to canonical native behavior. See [#29](https://github.com/tgibbsz32/forgecoin/issues/29).
- **Share verification:** compare native RandomX digest and difficulty against real candidate jobs; reject malformed, duplicate, stale, cross-worker, over-target and adversarial submissions. Measure CPU/memory and stress concurrency. See [#30](https://github.com/tgibbsz32/forgecoin/issues/30).
- **Desktop Solo:** demonstrate real isolated block submission and canonical acceptance, 60-block reward maturity, safe exit/restart and wallet scanning.
- **Desktop Pool:** demonstrate trusted client and real compatible isolated pool, accepted/rejected shares, reconnect and telemetry, share allocation and authorized mature payout.
- **Public infrastructure:** external verification, independent security audit, TLS, monitoring, backups, crash/reorg handling, access control and rollback. No unreviewed public RPC or payouts.

## Trusted XMRig archive gate (read-only)

The repository includes `tools/verify_xmrig_upstream_archive.py`, which checks only the **named upstream v6.26.0 Windows x64 ZIP** against the recorded publisher-archive digest. It does **not** unzip or execute anything:

```powershell
py tools/verify_xmrig_upstream_archive.py --archive "C:\\path\\xmrig-6.26.0-windows-x64.zip"
py -m unittest tools.test_verify_xmrig_upstream_archive -v
```

**Expected for the locally downloaded archive recorded in issue #95: `BLOCKED` / exit code 1.** A matching checksum is only integrity evidence against a known recorded digest: independently authenticate the publisher/checksum list, and review source changes, compiler, donation behavior and dependencies for any custom XMRig build. A custom source-built artifact must not be passed off as the publisher's unmodified ZIP.

## Evidence required for a pass

Every supported release gate should record:
1. UTC timestamp, code commit/branch, compiler/dependencies, exact binary SHA-256 and relevant platform;
2. isolated network identity, disposable-wallet provenance (no private keys, seeds, raw private blobs), configuration and complete command syntax;
3. deterministic inputs/expected outputs, passed/rejected cases, complete exit codes and **actual** accepted chain/pool results;
4. security limits and skips, independent review, reproducibility, rollback and operator authorization.

Stored hashes are **identifiers, not authentication**. If upstream/publisher-provided artifacts mismatch (see [#95](https://github.com/tgibbsz32/forgecoin/issues/95)), stop use until provenance is resolved.

Use [desktop mining evidence](../DESKTOP_MINING_PREFLIGHT_2026-10-25.md), [fresh-mainnet evidence](../FRESH_MAINNET_RELEASE_EVIDENCE.md), [release checklist](../RELEASE_CHECKLIST.md) and [Oracle preparation evidence](../HANDOFF_ORACLE_POOL_2026-10-25.md) as detailed sources.

## Release decision

**Block** the initial Windows V1 download and independent fresh-mainnet launch until all required gates are supported by real evidence and explicitly authorized. The official *public* pool is optional later, but verified Solo and compatible Pool mining are required for desktop V1 under the current roadmap.
