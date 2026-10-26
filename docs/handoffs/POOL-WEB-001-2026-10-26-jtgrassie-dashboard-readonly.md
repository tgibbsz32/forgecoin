> **Historical archive — superseded for current configuration.** Original evidence and decisions below retain their original dates and network parameters. Do not use old ports, genesis, balances, token proposals or release claims as current instructions. See [current mainnet specification](../CURRENT_MAINNET.md) and the current roadmap.

# POOL-WEB-001 — 2026-10-26 — jtgrassie research-backed ForgeCoin dashboard

## Scope and provenance

- **Active project:** original `tgibbsz32/forgecoin`. The separate
  `Forgecoin---Monero-FCMP-CARROT-Upgrade` repository was not modified.
- Base: `main` at `7140606fdc26c7c4ca745d4fbb520a51631bacd0`.
- Isolated checkout/branch:
  `feat/official-pool-website-jtgrassie-readonly-20261026`, kept separate
  from the user's in-progress Step 007 job-refresh changes.
- **Implementation commit:**
  `238692f2db37058ec67ff7d94419b6025c75da2b`.
- Pool backend **candidate**:
  `jtgrassie/monero-pool` pinned upstream `db16e73fcc587a873050a946214f63b6e1bed22a`.
  Inspected `src/webui.c`, `src/webui-embed.html`, `README.md` and
  `LICENSE`. Upstream is BSD three-clause. No upstream C source was copied
  or compiled in this step.

## Actual files implemented

- `apps/pool-site/dashboard.html`, `dashboard.css`, `dashboard.js`:
  polished, responsive original ForgeCoin blue/navy-branded pool console with
  accessible navigation, aggregate metrics, a genuinely observed hashrate
  chart (up to 24 locally recorded observations), network details,
  informational miner setup and engineering release gates. No fabricated
  network data, withdrawal control, miner wallet account lookup, or live
  mining endpoint. The existing `apps/pool-site/index.html` preparation
  page was preserved and simply gained a clearly labeled dashboard-preview
  link. Original ForgeCoin logo reused.
- `services/pool_stats_bridge/app.py`: zero-dependency Python read-only
  **localhost-only** preview and adapter. The only upstream supported is
  an explicit numeric-localhost `http://127.0.0.1:PORT/stats` source.
  Proxies, remote URLs, redirects, credentials, query parameters and
  non-`/stats` upstream routes are refused. Response size <=64KiB, upstream
  timeout 2 seconds, strict schema/value checks, no arbitrary methods.
  Normalizes upstream aggregate pool hashrate, network hashrate/difficulty,
  block height, connected account count, found blocks, round hashes, timestamps,
  and `pool_fee` fractional percent. Deliberately excludes `miner_balance`,
  individual miner fields, payout thresholds, wallets, cookies and upstream
  listen-port configuration. Responses are `503/not_connected` with NO
  stats when backend missing; `200/backend_observed_unverified` and
  `launchApproved=false` only when valid aggregate data is observed.
  The same-origin preview server serves a fixed allowlist of dashboard
  assets, with no-store, CSP, no-sniff and frame-denial headers.
- `services/pool_stats_bridge/tests/test_app.py`: 10 Python cases covering
  schema, bad numbers/fees/paths/credentials, private-field removal,
  API unavailable/live distinction, localhost fixture HTTP upstream, missing
  assets, blocked wallet paths, and browser-target asset serving.
- `.github/workflows/pool-dashboard-readonly-tests.yml`: Ubuntu and
  Windows CI for Python 3.13 read-only fixture tests and Node 22
  JavaScript syntax checks. No chain, mining, payout, or network backend.
- Documentation in both `services/pool_stats_bridge/README.md` and
  `apps/pool-site/README.md` explaining how to preview safely and why
  production deployment is prohibited.

## Tests and executed evidence

- Windows Python 3.13:
  `python -W error::ResourceWarning -m unittest discover -s services/pool_stats_bridge/tests -t . -q`:
  **10 passed, 0 skipped, 0 failures**.
- `node --check apps/pool-site/dashboard.js`: **passed**, Node v24.19.0.
- Headless Google Chrome on Windows: served the dashboard on a random
  `127.0.0.1` port with no backend, rendered at 1440x1100 and
  created a valid **269,858-byte PNG screenshot**. The smoke script
  deleted the temporary browser profile/screenshot afterward.
  No source data, wallet, or public network touched.
- Local real HTTP fixture at `127.0.0.1` supplied representative upstream
  `/stats` JSON and showed that a normalized 1% reported fee appears in
  the adapter, with account-specific fields excluded.
- `git diff --cached --check` passed before source commit.
- No production service, public pool, live node, payout wallet, reserve
  address or mining process started in this step.

## Important backend audit findings

1. **Upstream C pool requires a compiled Monero source tree** via
   `MONERO_ROOT`. Native ForgeCoin must be used instead, with header and
   ABI validation, current daemon `get_block_template`/RandomX tests and
   wallet RPC integration. This step is a separate **frontend/adapter**, not
   a working fork of that C backend.
2. Upstream `src/webui.c` divides `account_balance` by
   **1,000,000,000,000 (12 decimals)**. Current native FRG uses
   **100,000,000 atomic units per FRG (8 decimals)**. Individual balances
   and worker lookup are **disabled** until both backend accounting and
   settlement are corrected and tested against real FRG outputs.
3. Upstream `connected_miners` derives from `connected_accounts`.
   The console accordingly labels the field **connected accounts** rather
   than asserting a distinct worker count.
4. Pool `/stats` is **not an independent chain identity check**, and an
   observed upstream never grants launch authorization. No canonical
   accepted blocks, native address validation, verified mature payouts,
   PPLNS reconciliation, TLS edge, or public deployment are evidenced.
5. The earlier experimental Python research listener is still separate;
   its uncommitted Step 007 job-renewal changes in the owner's scratch
   checkout were **not modified**.

## Next implementation priority

Fork/pin jtgrassie's C pool without losing license notices, build in an
isolated Linux environment against the selected ForgeCoin daemon/wallet
commit, and test exact daemon template, miner address validation, native
RandomX seed/nonce semantics, 8-decimal accounting and wallet payout
transactions. Then integrate audited read-only statistics with the
dashboard, deploy separately under HTTPS only after security and FRG
mainnet release authorization.

**Do not merge/deploy as a production mining pool or advertise live
mining/payouts on the strength of these frontend preview tests.**
