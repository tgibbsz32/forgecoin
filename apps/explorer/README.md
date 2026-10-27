# ForgeCoin new-mainnet block explorer

**Status (October 27, 2026):** The public HTTPS explorer frontend and read-only API are deployed on Oracle at `https://150.136.209.227/`, but **native FRG mainnet is frozen and not launched**. The native daemon is deliberately inactive and no public blocks, transactions, miners, or balances should be represented as live. The explorer frontend is therefore a prelaunch readiness interface, **not a completed live-chain synchronization test**.

## Immutable network identifier

| Property | Required value |
| --- | --- |
| Network | Frozen ForgeCoin mainnet candidate, not retired development chain |
| Genesis nonce | `20261026` |
| Genesis hash | `4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c` |
| Native daemon HTTP RPC | Loopback `127.0.0.1:39481`, **never public** |
| Explorer app | Gunicorn/Flask loopback `127.0.0.1:19800` |
| Public entrance | nginx HTTPS 443; separate static preview at `/pool/` |
| Launch authorization | **False**; no native FRG block mining or public peer activation |

Code in `app.py` pins the candidate genesis and verifies `mainnet` nettype plus the height-0 block header. A global request gate checks identity before serving *all* public ledger API routes, including transaction/hash direct lookups, so a legacy node cannot be mistaken for the selected new chain. The explorer does not expose a general RPC proxy or wallet/seed access. The public `/api/status` endpoint advertises the frozen identity, reports whether a matching local node is reachable, and never authorizes mining; it responds even when the daemon is stopped. Every ledger endpoint fails closed with HTTP 503 if the matching node is offline or incorrect.

The static landing page contains a visible not-launched notice. It does not invent new blocks or a synthetic hashrate while the daemon is stopped. Wallet addresses, amounts and balances cannot be decoded from a privacy-preserving chain explorer; only publicly available metadata are displayed.

## Verified work / reproducibility

- The updated Flask backend, pagination, read-only methods, chain mismatch refusals, status route, offline and input validation passed **14 of 14 tests** via `test_newmainnet_routes.py` in the existing Oracle Flask environment, using synthetic RPC fixture responses, with no mining or real wallet operations.
- The Oracle service update was applied with an exact-hash source gate, byte-for-byte backups of the previous `app.py`, `static/index.html` and `static/style.css`, followed by a controlled **explorer-only** systemd restart and live HTTP/HTTPS verification. Recorded **9 successful deployment gates**; pool HTML still reports 57 unavailable-until-verified metrics and 22 observer placeholders. This was not a mainnet daemon restart.
- The existing Oracle record is under `/home/ubuntu/pool-preparation/explorer-release-gate-20261027.json`. The reversible prior files are at `/home/ubuntu/pool-preparation/explorer-backup-20261027`. Local handoff/evidence is in `outputs/42-oracle-explorer-deploy-result.txt` in the connected desktop project (not committed).
- The deployed code, static notice, and CSS are exactly the three files in this proposed change. Do not claim that all production block and transaction interactions have been exercised; their fixture tests passed, but a native verified chain has not started.

Run tests in an isolated environment with Flask installed, with `FORGE_EXPLORER_SOURCE` pointing to this `app.py`. Example on the Oracle VM without modifying the explorer service:

```sh
FORGE_EXPLORER_SOURCE=/home/ubuntu/pool-preparation/explorer-review-20261027/apps/explorer/app.py \
/opt/forgecoin-explorer/.venv/bin/python /home/ubuntu/pool-preparation/explorer-review-20261027/apps/explorer/test_newmainnet_routes.py
```

The older `smoke.py` requires a **live, authorized native chain** and must not be run as a substitute for these offline checks. It is not a prelaunch gate. Existing `nginx.conf` is a legacy HTTP-only example; Oracle's actual HTTPS and `/pool/` routing are defined in its installed nginx configuration. The old `deploy.sh` installer is intentionally disabled to prevent clobbering that working configuration.

## Remaining release gates

1. Publish a final independently reviewed FRG native consensus build with permanent genesis-output policy, deterministic Block 1 activation and independently validated cross-platform consensus. The source's mainnet identity manifest still states `release_authorized=false`, `consensus_guard_stage=draft-unbuilt`, `mined_blocks_permitted_before_launch=0`, and `genesis_spendability=unverified`.
2. Bring the approved Oracle daemon online only after authorization and verify its runtime genesis, UUID/address prefixes, chain height, RPC/P2P confinement and peer/sync behavior.
3. Perform full live explorer acceptance: canonical block list and pagination; block hashes, heights, orphan status, mined rewards and maturity; native transaction metadata/mempool and confirmation lookup; reorg invalidation of cached tips; forced daemon downtime and restored sync; stale/wrong-chain fallback; load and rate-limit resilience; browser accessibility/mobile review.
4. Keep public read-only explorer and worker-account/payout signer isolated; no public wallet RPC/seed or private pool balances should be exposed.
5. Remove the frozen banner and change `/api/status` authorization fields only through a **separate reviewed, explicitly approved public-network cutover**, never because a node happens to answer RPC.

The explorer backend is therefore **prelaunch-ready**, not proof that mining, the pool or the native mainnet are live.
