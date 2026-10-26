> **Historical archive — superseded for current configuration.** Original evidence and decisions below retain their original dates and network parameters. Do not use old ports, genesis, balances, token proposals or release claims as current instructions. See [current mainnet specification](../CURRENT_MAINNET.md) and the current roadmap.

# STEP-001 — 2026-10-25 — original ForgeCoin pool reconciliation

## Scope and inspected baseline

Owner corrected this chat to the regular https://github.com/tgibbsz32/forgecoin
project. FCMP/CARROT belongs to the separate project/folder and is excluded here.
A fresh isolated checkout starts at restored main
66d54dba6e25bfe078f6cc227e946185c0858620. Remote branches and open PRs were inspected;
only open PR #97 is a conflicting draft documentation hub, left unchanged.
Existing Work folders and drafts were read without modification. No AGENTS.md
was found in this source tree. Development branch:
codex/native-pool-launch-blocker-20261025.

The native source, Tauri wallet/mining controls, explorer, synthetic RandomX
listener, persistent worker and offline reward ledger exist. Existing handoffs
record native ARM64 synthetic validation and isolated XMRig compatibility, not
production share credits or payouts. Current source still requires trusted native
template-to-job evidence, full share accounting, mature payouts, installers,
independent release review and staging. Genesis/network/economics release gates
remain unresolved. No component is declared launch-complete by this step.

## Completed implementation

Commit: 2836035cf322eb33bf12a5e3705372e2c84f534a

Changed files:
- services/pool_research/ledger.py: replace ambiguous hash-set reconciliation
  with explicit height-indexed coverage plus a tip observation. Reject incomplete,
  malformed or duplicate-height/hash evidence. Match candidates at their recorded
  heights; handle shorter tips and maturity rollback. Lock before coverage reads
  and apply all state changes atomically; orphan revival remains rejected.
- services/pool_research/test_ledger.py: eleven tests, seven new regressions.
- services/pool_research/test_model.py: fix package import preventing full suite.
- services/pool_research/__init__.py: enable ordinary unittest discovery.
- services/pool_research/README.md: replacement API, evidence and limitations.
- .github/workflows/pool-offline-tests.yml: Windows/Linux offline fixture CI;
  sparse service checkout avoids inherited Windows long-path fixture failures.

Old callers passing a hash list/set must migrate to dict[height, hash]. No SQLite
schema or consensus changes. Repository search found only test callers. Partial
views can no longer silently reverse rewards. A caller must still independently
verify chain identity and coherent canonical ancestry; this is not an RPC verifier
or a payout authorization boundary.

## Tests and results

Windows x64, Python 3.13:
- Initial full module-based run: 105 discovered, one import error, four skips.
- Tests added before repair: eleven ledger tests ran, eight errors on old API.
- python -W error::ResourceWarning -m unittest services.pool_research.test_ledger services.pool_research.test_model -v:
  15 passed, no skips.
- python -W error::ResourceWarning -m unittest discover -s services/pool_research -t . -v:
  115 discovered, 111 passed, four skipped, 13.819 seconds.
- Skips: three private-capture checks require Unix; one executable-help check
  requires FORGECOIN_DAEMON_BIN. Socket digest fixtures use fake callbacks unless
  native helper variables are explicitly provided; no native hashing result is
  claimed for this run.
- git diff --check passed. Remote CI pending at handoff creation.

Initial fresh clone hit Windows long-path errors; enabled core.longpaths locally,
restored this new checkout's tree/index from HEAD and confirmed clean baseline.
Other checkouts were untouched. No node, miner, wallet or deployment launched.

## Blockers and next action

Highest pool integration blocker: source-matched native daemon block templates
must map to unique miner jobs, native RandomX verification and canonical block
acceptance before durable financial crediting can be integrated. Obtain coherent
read-only chain snapshots with identity/ancestry verification for this ledger;
never treat mock snapshots as chain evidence. Payout policy, funding isolation,
reorg maturity and crash-safe signing/submission remain unfinished.

Next development step: implement/test the native-template job pipeline against
the regular fork and preserved isolated template evidence, keeping production
chain submission and payouts disabled. Continue numbered dated committed
handoffs. Do not import FCMP/CARROT or Solana work into this project. Do not merge
consensus changes or launch production without separate release authorization
and independent review.

This handoff is committed after the implementation so it can record its exact SHA;
its own SHA is available through Git history.
