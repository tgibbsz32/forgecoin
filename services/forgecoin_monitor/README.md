# ForgeCoin Oracle status monitor — installed 2026-10-27

Read-only standard-library Python 3 service; no wallet keys, mining jobs, accepted shares, payouts or login actions. Requires the 20261026 frozen native genesis hash/nonce before displaying network statistics.

## Verified Oracle deployment

- Source services/forgecoin_monitor/monitor.py; service as **ubuntu user-level systemd** unit at ~/.config/systemd/user/forgecoin-monitor.service (versioned template: forgecoin-monitor.user.service). loginctl enable-linger ubuntu is active and user service is enabled/running.
- Process binds **127.0.0.1:19810** only. Health endpoint GET /healthz returns HTTP 200 to mean **monitor process up**, not blockchain online.
- GET /api/monitor returns HTTP 200 only for exact known genesis and mainnet network type; else HTTP 503 and null fields. Status always includes launchApproved=false, payoutsEnabled=false, miningAuthorized=false. It reports only aggregate node/public pool stats, never wallet/spend keys, payment accounts or private worker identifiers.
- nginx has a same-origin HTTPS GET-only /pool/api/monitor reverse proxy with public rate limiting. Installer script install_nginx_monitor_route.py checks the current nginx config and restores a backup on invalid syntax.
- Oracle /pool/ existing 57-field public static statistics page now loads network-monitor.js as an additive integration. The script displays identity-verified node metrics and leaves all other unverified pool/payout fields Unavailable. Installer install_pool_network_readonly.py makes a dated backup of the existing 57-metric index page.
- Runtime checks: HTTP 200 from Oracle monitor with an isolated offline new-genesis daemon and height1/difficulty500000; HTTP 503 after daemon stop. External HTTPS certificate validated (TLS verify=0) with pool page and script HTTP 200.
- Public pool Stratum port, wallet RPC, actual payout and miner accounts are NOT enabled. This service intentionally does not expose write handlers or enable them via API response flags.

## Routes

- GET 127.0.0.1:19810/healthz: running process
- GET 127.0.0.1:19810/api/monitor: fresh verified canonical chain summary when available, otherwise 503
- GET 127.0.0.1:19810/api/pool-stats and /api/solo-stats: currently 503 launch-disabled
- Browser public GET https://150.136.209.227/pool/api/monitor through reviewed Nginx
- POST/PUT/DELETE on monitor: method not allowed

## Verification

Run tests: python3 -m unittest discover -s services/forgecoin_monitor/tests -v (8 passed). Combined daemon/wallet/explorer/C-pool/XMRig QA: tools/run_offline_pool_qa.py --with-miner, restricted to the **Oracle disposable local-only QA system**, never a public chain.

The forgecoin-monitor.service template in this folder is a separate root-level systemd reference; Oracle currently uses the **user-level** template.

These status endpoints do NOT authorize production release or public mining.
