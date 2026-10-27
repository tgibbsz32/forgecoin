# ForgeCoin Oracle native backend monitor (prelaunch)

Read-only localhost-only Python 3 service. No dependencies outside Python standard library. Does not start the daemon/pool, mine blocks, submit templates, sign payouts or read wallet keys.

- GET /healthz: monitor process operational; this does not mean the FRG blockchain is live.
- GET /api/monitor: returns verified genesis/height/peer snapshots if new-mainnet daemon responds, otherwise HTTP 503 and unavailable fields. Exact nonce + genesis hash + network type are mandatory.
- GET /api/pool-stats and /api/solo-stats: HTTP 503, explicitly launch-disabled. Activation must follow audited launch authorization.
- HTTP listener fixed to 127.0.0.1, never public. No dashboard connectivity until interface and chain identity are validated.
- Polls daemon 127.0.0.1:39481, optional pool stats 127.0.0.1:4243/stats. Redacts wallet/account/private data; never reads retired 19481 chain.
- Only approved read-only RPC methods. No start_mining, submit_block, wallet RPC, login or payment handlers.

Run tests: python3 -m unittest discover -s services/forgecoin_monitor/tests -v.
Deploy only after source review to /opt/forgecoin-monitor with forgecoin-monitor.service.

Monitor responses do not authorize launch even if a daemon becomes reachable.
