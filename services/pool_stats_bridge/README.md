> [Current mainnet specification, tokenomics and release status](../../docs/CURRENT_MAINNET.md) — October 26, 2026; prelaunch.

# ForgeCoin read-only pool statistics bridge

**Scope:** preview UI and an isolated *read-only* aggregate statistics adapter for the
official native FRG mining pool. **Not a mining pool implementation**, not a
wallet, not a Stratum listener, and not approved for public production use.

## Why this adapter exists

The upstream candidate [jtgrassie/monero-pool](https://github.com/jtgrassie/monero-pool)
(C, libevent, LMDB, PPLNS) exposes a JSON `/stats` endpoint in
`src/webui.c:send_json_stats`. The upstream README recommends that a separate
webserver/UI consume this endpoint rather than compiling a custom dashboard
into the pool binary.

Pinned, independently audited upstream source snapshot:
`db16e73fcc587a873050a946214f63b6e1bed22a` on upstream `master`.
License in upstream `LICENSE`: BSD three-clause notice. **No upstream source code
has been copied into this repository by this branch.** Preserve notices and
attribution if a backend fork is later added.

The upstream `/stats` response uses numeric keys `pool_hashrate`,
`network_hashrate`, `network_difficulty`, `network_height`,
`connected_miners`, `pool_blocks_found`, `round_hashes`,
`last_block_found`, `last_template_fetched`, and `pool_fee`. The last is
**a fraction** (0.01 means 1%). The bridge normalizes those fields for the
ForgeCoin dashboard, never substitutes simulated values, and refuses malformed,
negative or missing required statistics. It strips all account/miner-specific
keys and never processes cookies, wallet addresses, payment requests or mining
credentials.

## Local preview (no backend, no FRG mining)

From repository root:

```sh
python -m services.pool_stats_bridge.app --port 48775
```

Open `http://127.0.0.1:48775/`. All statistics remain **—** / disconnected.
The existing site `apps/pool-site/index.html` remains the public preparation
page and links to `dashboard.html` as a preview. Opening the static dashboard
on a file server will also show no real statistics without a proxy/adapter.

To test ONLY with an explicitly trusted, local **disposable** upstream that
implements the exact audited `/stats` contract:

```sh
FRG_POOL_STATS_UPSTREAM=http://127.0.0.1:4243/stats python -m services.pool_stats_bridge.app --port 48775
```

On PowerShell, set `$env:FRG_POOL_STATS_UPSTREAM` to the URL before starting
Python. Both the bridge preview and upstream **must** remain on numeric loopback
interfaces. The bridge refuses public/DNS/HTTPS endpoints, credentials, path
variation, redirects and proxies. It has a 2-second upstream timeout and
64-KiB response maximum.

The normalized API is `GET /api/pool-stats` on the preview origin. When no
upstream is configured or the source is invalid, it responds **503** with
`state: not_connected` or `unavailable` and **no figures**. With a valid
source it responds `backend_observed_unverified` and `launchApproved: false`.
It does **not** establish that the ForgeCoin mainnet is live or the statistics
represent a canonical chain. The dashboard polls every 20 seconds and drops
figures when the source fails.

Tests (no network except fixture HTTP bound to localhost; no wallet or daemon):

```sh
python -m unittest discover -s services/pool_stats_bridge/tests -t . -v
node --check apps/pool-site/dashboard.js
```

## Backend porting and production gates

**Do not point this at public Monero pools and relabel their statistics as
ForgeCoin.** Upstream jtgrassie source is not FRG-compatible out of the box.
It expects a compiled Monero source tree and Monero daemon/wallet RPCs. Before
an authorized official deployment, fork/port the C backend to the exact
ForgeCoin consensus and wallet RPC, verify RandomX seed & templates, address
validation, transaction serialization and fee/royalty rules, block maturity
and reorg recovery, PPLNS, durable balances and native FRG payouts.

**CRITICAL atomic-unit mismatch:** jtgrassie's `src/webui.c` divides the
account balance by `1000000000000.0` (Monero's 12-decimal convention).
ForgeCoin currently uses **8 decimals**. The bridge **deliberately strips
`miner_balance` and does not offer miner-account lookups** to prevent falsely
reported balances. Do not enable personal earnings, payout thresholds or worker
lookup until the backend is patched, a native wallet is used, and end-to-end
8-decimal reconciliation is proven.

For any public rollout, serve static UI through HTTPS/Nginx using audited
read-only API caching and rate limits; bind pool backend statistics privately;
configure actual chain identity and canonical source independently; validate
frontend accessibility and error states; obtain explicit mainnet/payout
authorization. This local Python preview is **not a production web server**.
