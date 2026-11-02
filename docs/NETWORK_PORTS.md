# ForgeCoin selected network port contract

**Frozen native identity: October 26, 2026. Public FRG mainnet is not yet launched.**
This is a selected-network configuration contract, **not evidence that an Oracle node,
pool listener, firewall, wallet, or public peer is live**. Retired network endpoints
must never be silently reused by new desktop or Android clients.

| Service | Selected port | Exposure / usage |
| --- | ---: | --- |
| Native P2P | **39480/TCP** | Node-to-node only. A public node may explicitly expose this port **after launch authorization**; desktop defaults bind localhost. |
| Native daemon HTTP RPC | **39481/TCP** | **Loopback or authenticated private access only.** Pool, explorer, and wallet connect to a trusted daemon at this port. Do not expose unrestricted RPC publicly. |
| Native ZMQ RPC | **39482/TCP** | **Loopback/private only** for approved native event consumers. Not the wallet RPC and not the pool miner port. |
| Windows Forms XMRig local statistics HTTP | **39483/TCP** | **Localhost-only** miner telemetry; not the native daemon RPC and not the wallet RPC. |
| Windows Forms `forge-wallet-rpc` | **39484/TCP** | **Localhost-only** wallet control. The Tauri wallet RPC chooses a separate dynamic local port; never substitute 39482 or 39483. |
| Pool Stratum (staging only) | **127.0.0.1:4242/TCP** | Default in `services/official_pool/jtgrassie/pool.conf`; **localhost-only, not public Stratum approval**. A public listener requires independent security and release review. |
| Official pool web UI (staging only) | **127.0.0.1:4243/TCP** | Local/backend-only; expose statistics through a reviewed read-only proxy, not through this listener. |
| Explorer Gunicorn backend | **127.0.0.1:19800/TCP** | Reverse-proxy upstream; never publish the Python backend listener directly. |
| Website HTTPS | **443/TCP** when deployed | Reverse proxy service, separate from native daemon RPC. |
| Local preview | **8080/TCP** where documented | Developer-only example, not an official production listener. |

The **native address prefixes** are 190 (standard), 191 (integrated) and 192
(subaddress). The frozen genesis nonce is 20261026. These must agree with
the compiled daemon, wallets, explorer, official native pool, and any Android miner.

## Retired network settings

The old development chain used P2P **19480**, daemon RPC **19481**, and
ZMQ **19482**, with retired address prefixes. Those values may remain in
historical records and under `prior_chains` with `classification: archive_only`,
but **must not appear as live defaults** in selected-mainnet applications.
The October 20 candidate is also retired. Previously installed clients should
not automatically connect to the older Oracle peer when migrated.

The active staging work is tracked in
[PR #185](https://github.com/tgibbsz32/forgecoin/pull/185)
(native consensus and prelaunch protection) and
[PR #186](https://github.com/tgibbsz32/forgecoin/pull/186)
(Windows desktop endpoint corrections, now **merged into source `main`**).
PR #185 remains draft; PR #186 is merged. Neither change is an
authorized network or installer release.

## Verification and deployment gates

- Verify the **compiled binaries** report frozen genesis, prefixes, ports and chain
  identity. Updating source or docs does not update existing installed binaries.
- Verify the Oracle service unit, daemon flags, pool config, explorer `FORGE_RPC_URL`,
  reverse proxy/firewall, Windows and Android defaults against this contract
  **before** an authorized production cutover.
- Keep RPC/ZMQ/wallet control local or behind separately reviewed authenticated
  private access. Only an approved P2P port should become externally reachable.
- Run native consensus/block/ring-spend tests and real pool payout maturity
  tests before public Stratum or wallet release. Never unlock public mining
  merely to prove a port is listening.

This document is normative for *selected* ports only. Historic handoffs and
tests retain their original recorded ports as evidence, not current instructions.

## Verification performed November 2, 2026

The canonical `docs/current-mainnet.html` public website was fetched over HTTPS
from the project workstation; HTTP 200 was returned, and the published page
showed native ports **39480/39481/39482**, Windows wallet RPC **39484**,
and XMRig telemetry **39483**.

An authorized read-only Oracle SSH inspection **succeeded later on November 2** using
the Dell's pre-existing Oracle identity. The earlier key-rejected attempt is
superseded. The installed `forgecoin-mainnet-20261026.service` points at
**P2P 39480, loopback daemon RPC 39481, loopback ZMQ 39482**, and has
`ConditionPathExists=/etc/forgecoin/approved-mainnet-launch.json`; it was
**disabled and inactive**. A separate older `forgecoin.service` was also
**disabled and inactive**, but still contains **19480/19481** in its unit
and difficulty-upgrade drop-in and targets a **legacy binary/database**.
**Do not retarget or start that legacy service** as a shortcut to mainnet.

The live Oracle INPUT firewall still contains an **ACCEPT for retired
19480/TCP** and **no ACCEPT for selected 39480/TCP**. This is a real
configuration inconsistency, not a running public node: no FRG P2P/RPC/
ZMQ port was listening. nginx was listening on 80/443; the explorer's
Gunicorn was listening on **127.0.0.1:19800**. The explorer service
was active, while the selected native chain service remained inactive.
An exact-rule firewall cleanup attempt was **blocked by remote-command
permissions before execution**, so **no live firewall change was made**.
The old allow rule remains present; public 39480 must stay closed until
an independently approved mainnet cutover. Verification also does not
establish OCI cloud-side security lists or live payout readiness.

The new **read-only** `tools/audit_oracle_prelaunch_config.py` detects
legacy service settings, unsafe active/enabled launch services, missing
selected-port or launch guards, and insecure IPv4 INPUT allows. It
does not change the firewall, daemon, systemd configuration or wallet.
An authorized operator must separately review and apply any firewall
cleanup; the historical service remains archived/disabled.

The active app/service source cross-check is in the dedicated
`tests/desktop/test_network_port_contract.py` regression attached to desktop
draft PR #186, with independent GitHub CI. The compiled frozen-native source
and its runtime identity checks remain in draft PR #185. The old installed binaries
have **not** been replaced or certified.

## Read-only host listener audit

When an authorized operator has shell access **on the Oracle host itself**, from
a working copy of this repository run:

```bash
python3 tools/audit_host_ports.py --json
```

The script reads `ss -H -ltn` locally; it makes **no network connections**,
does not start/stop services, and never edits firewalls. It reports any
listeners using the retired 19480/19481/19482 ports as errors and flags
non-loopback bindings on daemon RPC 39481, ZMQ 39482, XMRig statistics
39483 or Windows wallet RPC 39484 as errors. External P2P listening on 39480
is a warning requiring separate launch authorization, not an automatic change.

To examine previously captured `ss -H -ltn` output without SSH access:

```bash
python3 tools/audit_host_ports.py --ss-file /path/to/saved-ss.txt --json
```

Exit status **0** means the observed listeners produced no error alerts,
**2** means unsafe/deprecated listeners were detected, and **3** indicates
the local socket query failed. **A clean report does not establish that
services are correctly configured, firewall rules are safe, or the network
is launch-ready.** Also inspect service units, RPC authentication, reverse
proxy, firewall and external reachability before approval.

The parser and severity rules have standalone offline tests under
`tests/desktop/test_host_ports.py` in the main CI workflow.
