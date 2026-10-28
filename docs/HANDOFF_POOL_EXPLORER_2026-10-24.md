> **Current mFRG policy (October 28, 2026): Historical archive only.** The previous October 27 50M mFRG notice below has been superseded by a **500M proposed fixed-supply target with nine allocations including 50M cryptocurrency fundraising and 30M (6%) founder-beneficial holdings** (15M immediate, 15M month-13-to-36 vesting). See [canonical policy](MFRG_LIFETIME_TOKENOMICS_500M.md). Do not follow older payment or mint instructions.

> **October 27, 2026 superseding notice:** This is historical research/evidence. The current direction has **no approved fixed ten-seat governance system** and **no planned wFRG bridge**. The separately proposed 50M mFRG SPL token has **5M initial sale**, **5M post-sale liquidity/staking treasury**, and **40M future issuance/development treasury**. Governance is to be selected before the sale concludes. The current active specifications are [ROADMAP.md](../ROADMAP.md) and [miniFORGE allocation](MINIFORGE_SPL_TREASURIES.md). Do not treat earlier planning decisions here as active authorization.

> **Historical archive — superseded for current configuration.** Original evidence and decisions below retain their original dates and network parameters. Do not use old ports, genesis, balances, token proposals or release claims as current instructions. See [current mainnet specification](CURRENT_MAINNET.md) and the current roadmap.

# Handoff: native pool, desktop, website, Observer and explorer

**Updated: 2026-10-24. Review only; do not merge or deploy.**

## Resume here

- Repository: `tgibbsz32/forgecoin`; existing [PR #17](https://github.com/tgibbsz32/forgecoin/pull/17).
- Review branch: `codex/docs-accuracy-review-20261024`; base: `main`. Fetch and inspect the current head and working tree before editing. Do not create a replacement PR or force-push.
- Implementation-plan and exact-logo update: commit `6393fb1` (pushed). This handoff is a follow-up documentation commit on the same branch. Use the current remote head rather than assuming `6393fb1` remains the tip.
- Start with [ROADMAP.md](../ROADMAP.md), [the implementation plan](POOL_EXPLORER_IMPLEMENTATION_PLAN.md), [PROJECT_STATUS.md](../PROJECT_STATUS.md) and [release evidence/limits](RELEASE_STATUS_2026-10-24.md).
- Current authorization covers roadmap/documentation/homepage/logo changes and pushing this review branch. It does not authorize merging, deploying services, opening public infrastructure or handling production funds. A future implementation task must establish its own scope.

## Completed in this update

- Added explicit construction and staged deployment of the official native FRG pool with a **1% operator fee** on eligible pooled rewards. Solo mining has no project-pool operator fee; payout transaction costs remain separate. The 100-worker goal is not verified capacity.
- Recorded Tauri official-pool integration alongside solo and custom pools, pool website/dashboard completion, a standalone Pool Observer and completion of the online blockchain explorer.
- Added component-specific tests, security requirements and offline → isolated integration → private hosted staging → reviewed beta → monitored public release gates. No gate is claimed passed by writing the plan.
- Updated the homepage roadmap and mining guide, root README/status, desktop/explorer READMEs and pool research cross-references. Existing trading/Solana research milestones remain deferred.
- Replaced `docs/images/forgecoin-logo.png` with the exact user-provided blue gear/flame/F image. SHA-256: `fd4aede81c6b50e78449722ba584e7cd3e0b94d4186e1ed7fc46fa938aca5a25`. Tracked website logo/favicon URLs use `?v=fd4aede8` to invalidate the old cached mark; no generated reinterpretation or image edit was used.

## Preserve the local drafts

`docs/pool.html` and `docs/pool-observer.html` were already **untracked drafts**. They were read for context, left byte-for-byte unchanged and excluded from commits. They refer to unfinished supporting assets and services; do not bulk-add them, link to them as shipped products, or delete them. Inspect and reconcile them deliberately in a separately scoped website implementation task. A fresh clone will not contain these local-only drafts.

## Workstream handoffs

| Workstream | Existing starting point | Next concrete deliverable and acceptance evidence |
| --- | --- | --- |
| Native pool | `services/pool_research/` offline model; `docs/ZERO_COST_MINING_POOL_RESEARCH.md` | Review/select FRG-compatible Stratum/RandomX implementation; specify fee basis, payout scheme, maturity and rounding; build durable ledger and payout recovery. Prove accepted blocks and reconciled mature payouts with two independent test miners, reorg/crash safety and tested connection limits. The model is not a network pool. |
| Tauri desktop | `apps/desktop-tauri/` Solo and user-configured XMRig controls | Implement opt-in verified official-pool profile only once an endpoint exists; preserve manual custom pools and solo mode. Test TLS errors, wrong network, full/offline pool, start/stop/restart and accepted-share/payout states; do not infer mining success from process state. |
| Pool website/dashboard | `docs/index.html`, `docs/mining.html`; two local untracked drafts | Complete overview/workers/shares/blocks/payouts/setup/FAQ with a separate secured API. Define privacy, authorization for any account/payout changes, freshness/error states and exact amounts; verify ledger agreement and desktop/mobile accessibility. GitHub Pages cannot run the backend or Stratum server. |
| Standalone Pool Observer | Delivery requirements in the implementation plan; local untracked draft | Build independent read-only observation and solo/pool probability tool. Validate formulas against reference values and edge cases; label sample inputs, stale data, fee assumptions and estimates. No wallet secrets or payout mutations. |
| Online explorer | `apps/explorer/app.py`, `static/`, `smoke.py`, nginx/systemd/deploy files | Complete fixture and isolated-node tests for lookups, pagination, confirmations, reorg/cache behavior, large values and RPC failures. Review dependencies, allowlisted RPC, rate limits and isolation; add HTTPS/certificate renewal and operational recovery. Verify external access and network identity before publishing links. Existing nginx config is HTTP-only; deployment script is server-specific. |

Full acceptance criteria and security requirements are in the [implementation plan](POOL_EXPLORER_IMPLEMENTATION_PLAN.md). Keep each component's implementation evidence distinct from its deployment evidence.

## Remaining decisions and dependencies

- Resolve final network identity, genesis and L1 release gates before production pool configuration; do not mix the current development chain with the fresh candidate or imply automatic balance migration.
- Publish the pool payout policy, minimum payout, confirmations, orphan/reorg behavior, precise 1% fee calculation and transaction-cost treatment before beta. PPLNS is not ratified merely because a draft mentions it.
- Decide whether a public official pool is required on mainnet launch day or follows solo launch. Explorer completion remains in phase 1 readiness; pool construction/private tests can proceed alongside L1 validation.
- Verify actual hosting quota/capacity and continued node health before any infrastructure change. Do not assume free-tier capacity or 100-worker throughput. Require independent security review and operational ownership before public rollout.
- Native FRG remains the launch scope: 50M primary-emission reference, no allocated premine, 100% native subsidy to PoW miners and perpetual 0.20 FRG/block tail, subject to source verification. Pool service fees are not a new consensus levy. Optional Solana interoperability and native trading remain research.

## Validation and release boundary

- Passed local documentation checks for 119 relative links/assets, HTML IDs/anchors, versioned logo references, exact supplied-logo bytes and unchanged draft hashes. Recheck links if this handoff or further documents change them.
- Reviewed the rendered homepage hero/logo and roadmap cards in a local browser preview. This is local preview evidence, not a GitHub Pages deployment or a complete responsive/accessibility audit.
- `git diff --cached --check` passed before the implementation-plan/logo commit. No native pool, desktop, explorer integration, load or production payout tests were run for these documentation/static-site changes.
- `.github/workflows/pages.yml` publishes on qualifying `main` pushes or manual dispatch. Pushing this review branch does not update the public website. Leave PR #17 open and unmerged; do not dispatch deployment as part of this handoff.
- Temporary localhost previews are disposable verification aids, not public services or durable handoff URLs. Recreate a local preview from `docs/` when needed.

## Website direction follow-up

The owner confirmed the project direction is settled and requested website copy reflecting the project and its future. The homepage now presents native monetary policy, mining choice, community governance and future interoperability together. Community copy reflects the ten-seat native FRG design target and labels legacy eligibility/voting tools as archived demonstrations. Downloads and mining pages distinguish the development chain from the future mainnet and describe planned services. This is confirmation of direction, not evidence of deployment, ratified seat allocations or passed release gates. Preserve the review-only branch workflow and local untracked drafts.
