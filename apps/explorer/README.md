> **Current specification — 2026-10-26:** [Frozen mainnet parameters, tokenomics and release status](../../docs/CURRENT_MAINNET.md). Public launch is not authorized. Main-branch executables still implement legacy rules; these instructions are not proof of new-mainnet compatibility.

# ForgeCoin Explorer

Recovered read-only Flask API and standalone web interface intended for the Oracle-hosted ForgeCoin node. **Source exists; completion and current public availability are not verified.** The previously referenced `../HANDOFF.md` is absent from this checkout and cannot establish deployment status.

See the [implementation plan](../../docs/POOL_EXPLORER_IMPLEMENTATION_PLAN.md) for the remaining block/transaction UI and API verification, reorg/cache tests, RPC failure handling, security review, HTTPS, external reachability checks and staged operational rollout. `smoke.py` requires a running compatible daemon; its presence does not prove tests passed. The current nginx configuration serves HTTP only.

Continuation notes and the explorer workstream handoff are in [the current handoff](../../docs/HANDOFF_POOL_EXPLORER_2026-10-24.md).

Deploy source to /home/ubuntu/explorer, create its .venv and install requirements.lock.txt. Run smoke.py against the loopback daemon. deploy.sh installs /opt/forgecoin-explorer, isolated systemd services and nginx routing. It expects existing passwordless sudo and is intended for this server; inspect before reusing elsewhere.

Node RPC stays on127.0.0.1:39481. Explorer backend binds127.0.0.1:19800. nginx serves public port80. A separate Oracle cloud ingress rule must permit80. No account login, wallet keys or private transaction decoding are provided.
