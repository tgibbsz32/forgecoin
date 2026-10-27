# ForgeCoin pool preparation website

## Verified Oracle deployment update (October 27, 2026)

The live /pool/ path on Oracle preserves the existing 57-metric detailed pool and Pool Observer preview, not a replacement with this directory's redesigned index.html. The reviewed network-monitor.js was added to that existing page, backed by the persistent user-level forgecoin-monitor service over same-origin HTTPS GET /pool/api/monitor. When the 20261026 daemon is offline the monitor returns HTTP 503 and all unavailable values remain unavailable; pool/worker/payout fields have no live authoritative backend. Oracle public /pool/ and JS each returned HTTP 200 with TLS verified. The read-only monitor, shared frontend and genesis-only explorer passed the isolated QA described in docs/PHASE1_NATIVE_ORACLE_ANDROID_QA_2026-10-27.md. No public Stratum, miner login, fee payouts or user-account service has been enabled.

The account.html, statistics.html and redesigned dashboard assets in this source directory are staging previews; they are not a substitute for a working authenticated pool account backend.

Static HTML and CSS intended for the existing Oracle VM at `/pool/`. This is
a readiness page, not a pool server or live dashboard. It makes no API calls,
contains no analytics, and uses only local assets and system fonts.

Mining connections, block submission, and payouts are disabled. Publishing
this page must not launch the new mainnet or mine coins. The existing explorer
at `/` represents the old development network and is explicitly labelled.

The 1% operator fee is planned policy on eligible mining rewards, separate from
transaction fees. No fees are currently collected by this pool.

## Local preview

From this directory, run `python -m http.server 8080 --bind 127.0.0.1` and open
`http://127.0.0.1:8080/`. Stop the preview when finished. To verify the deployed
path locally, serve a parent directory with this folder mapped as `pool`.

Deploy `index.html`, `styles.css`, and `assets/forgecoin-logo.png` together beneath
`/pool/`. Preserve existing explorer routes and ACME challenges. Do not publish
this README as the homepage. No build, Node dependencies, scripts, wallet access,
miner, daemon, or backend are needed.

The logo is an exact copy of `docs/images/forgecoin-logo.png`; do not redraw it.


## Read-only pool dashboard preview — 2026-10-26

`dashboard.html`, `dashboard.css` and `dashboard.js` are an original
ForgeCoin-branded responsive interface for **pool/network aggregate statistics**.
The existing `index.html` is still the authoritative public readiness page and
now links to the dashboard preview. Both pages retain pre-launch disclosures,
and the website **does not** introduce a miner wallet lookup, pool endpoint,
account balances, payment information or functional mining configuration.

The dashboard makes same-origin `GET api/pool-stats` requests only. Use the
**separate, loopback-only** `services.pool_stats_bridge.app` local preview server
to serve the frontend and safely normalize the upstream jtgrassie
`GET /stats` JSON. If there is no valid backend, the UI displays **dashes**,
a disconnected status and an empty chart. It records up to 24 genuinely
observed pool hashrate samples *in the current browser session* after a
stats source connects; there is no fabricated demo curve or persistent tracking.

From the **repository root**:

```sh
python -m services.pool_stats_bridge.app --port 48775
```

Open `http://127.0.0.1:48775/dashboard.html` on the **same computer**.
For details and security warnings, read
`services/pool_stats_bridge/README.md`.
No Node installation or build pipeline is needed for the static website.
All assets are local and keep the existing ForgeCoin logo.

The local stats bridge is *not* designed for public hosting; no deployment is
made by these files. Before production, port the native jtgrassie backend to
ForgeCoin and arrange an audited private stats proxy with HTTPS, rate limits,
chain-identity verification and payout maturity tests. The existing explorer
and old network are unaffected.
