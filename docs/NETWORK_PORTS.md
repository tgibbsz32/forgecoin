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
| Pool Stratum and pool web/stats | **Not assigned in this chain port contract** | Configured per pool/service and approved separately. **Do not infer** Stratum is 39480–39484. No public Stratum or payouts authorized. |
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
(Windows desktop endpoint corrections). Both remain draft; neither is an
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

A read-only SSH check of the previously documented Oracle host was **not
authorized by the available SSH key** (`Permission denied (publickey)`).
Therefore, the actual remote service process command lines, firewall bindings,
legacy daemon listeners, pool Stratum listener and reverse proxy remain
**unverified**. No server configuration or network rule was changed. When
authorized access is restored, inspect `ss -ltn`, relevant service units, native
daemon configuration, pool config, explorer RPC URL and firewall rules
**before** applying reviewed changes. Do not expose daemon RPC, ZMQ or wallet
RPC to the public internet and do not start mining merely to confirm connectivity.

The active app/service source cross-check is in the dedicated
`tests/desktop/test_network_port_contract.py` regression attached to desktop
draft PR #186, with independent GitHub CI. The compiled frozen-native source
and its runtime identity checks remain in draft PR #185. The old installed binaries
have **not** been replaced or certified.
