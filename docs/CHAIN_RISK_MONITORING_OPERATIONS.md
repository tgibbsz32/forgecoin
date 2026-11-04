# ForgeCoin 51% risk operations — independent-node chain observer (prelaunch)

> **Not deployed and not permission to activate native FRG mining.** This document and the referenced source provide monitoring, not chain finality, guaranteed 51% prevention, automatic financial settlement, or trusted checkpoints. The frozen native chain identity remains unchanged; draft consensus PR #185 and genesis-output proof are separate launch blockers.

## Scope and trust requirements

Monitor **at least two independently operated full nodes**, ideally on separate hosts/providers and autonomous systems, *after* both report the selected 20261026 genesis. Connect using separate, authenticated private tunnels to their loopback daemon RPC listeners. Do not expose native RPC 39481 or ZMQ 39482 to the public Internet. Distinct local ports alone **do not prove** independent infrastructure or prevent an eclipse of both nodes. Keep a third out-of-band node/operator view for incident resolution.

The source:
- `tools/forgecoin_chain_risk.py` — one read-only poll; JSON on stdout, exit statuses
- `tools/forgecoin_chain_history.py` — persisted *observational* anchors, **not** cryptographic checkpoints or protocol changes
- `tools/test_forgecoin_chain_*.py` — deterministic offline tests
- `.github/workflows/chain-risk-observer.yml` — offline test automation

## Example on an approved isolated lab network

With a separately approved **test** daemon already bound at `127.0.0.1:39481`, and a separately administered second node accessible over SSH:

```sh
# On the monitoring host only. Use pre-approved SSH host keys and credentials.
ssh -N -L 127.0.0.1:39581:127.0.0.1:39481 observer@SECOND_INDEPENDENT_NODE
# In another terminal or systemd-managed one-shot invocation:
python3 tools/forgecoin_chain_risk.py \
  --node http://127.0.0.1:39481/json_rpc \
  --node http://127.0.0.1:39581/json_rpc \
  --state /var/lib/forgecoin-risk/chain-observations.json
```

This assumes the default selected FRG daemon RPC is loopback-only and that approved SSH connectivity exists; it does **not** create either node or authorize public mainnet deployment. Use dedicated non-root OS accounts and restrict state file/directory permissions. The observer refuses non-local RPC URLs.

- Exit **0** / `OBSERVED_ONLY`: recent observation verified with **no alarm**, not an assertion that the network cannot be attacked.
- Exit **1** / `ALERT`: anomaly observed; treat as an incident, independently verify.
- Exit **2** / `UNVERIFIED`: missing/malformed data, historical RPC failure, lost node or corrupted state. **Never treat as safe** or as permission for payout/bridge release.
- Invoke periodically using a reviewed supervisor that records stdout/stderr and the exit code. Continuous deployment and notifications are separate operational tasks; this repository does not silently schedule them.

### What the observer checks

1. Frozen genesis identity, contiguous recent headers, tip consistency, positive difficulty and valid header encodings.
2. Diverging blocks at shared heights, local replacement of previously seen hashes, tip rollback, abnormal block delay and unverified time jumps.
3. Reported synchronization state and fewer than two outbound peers; peer count alone **does not establish** diverse ASNs/independent nodes.
4. Operational difficulty jumps at or beyond 4x (warning only; never substitute for consensus difficulty validation).
5. Every 60 blocks, after at least 60 further blocks, it can retain a canonical *observed* block-hash anchor; each poll rechecks the two most recent and a rotating sample of older ones. If a hash conflicts, preserve the previous anchor and report a critical historical reorg suspicion. Sampling does not audit all heights or guarantee immediate detection.

On the first run, the observer creates a history baseline only from the most recent fetched headers; it **cannot validate unobserved historical periods**. If it encounters a conflict, do not auto-overwrite the state. Preserve the evidence and require a separately reviewed resolution. If the history exceeds its bounded capacity, it fails closed and requires manual archival/review. The state file contains block hashes and RPC endpoint references, **not private wallet material**.

### Manual incident response

1. Record observer JSON, old state, timestamps, independently verified block hashes and each node's trusted host identity. Check for split-tip / eclipse / out-of-sync conditions.
2. Suspend *new* exchange, bridge and merchant credit decisions under their own independently reviewed policies. The watcher itself **does not** stop blockchain consensus, disable pools or change balances. Current native pool wallet transfers are already disabled pending end-to-end tests.
3. Check canonical total accumulated work and actual FRG node history with at least one additional trusted, independently administered full node. Do not choose the longer *height* automatically and never rewrite consensus checkpoints from alerts.
4. For any matured-block conflict, preserve the native pool's existing durable LMDB accounting-quarantine marker; never clear it automatically. Complete a full credited-block ledger reconciliation and independent review before manually authorizing payouts in a future production build.
5. Publish an incident record and remediation plan. Genuine majority work may still reorder blocks/censor transactions; monitoring reduces detection latency and settlement exposure, not PoW takeover capability.

## November 3, 2026: RPC difficulty parser correction

[Merged PR #198](https://github.com/tgibbsz32/forgecoin/pull/198) corrects the read-only observer's `wide_difficulty` parsing. The ForgeCoin/Monero JSON-RPC convention represents this as **hexadecimal even without `0x`**, as explicitly checked by `tests/functional_tests/blockchain.py`. The watcher now parses bounded hex text and cross-checks supplied low/high 64-bit values, failing closed on malformed or contradictory fields. New offline regression cases passed in [GitHub Actions](https://github.com/tgibbsz32/forgecoin/actions/runs/41658675417). This is not a runtime deployment or a new consensus rule.

## Required next native-pool release gates## November 3/4 — genuine native two-node observer fork acceptance

[GitHub x86_64 native CI 41771760913](https://github.com/tgibbsz32/forgecoin/actions/runs/41771760913) **PASSED** on [PR #202](https://github.com/tgibbsz32/forgecoin/pull/202), merged only into the **isolated test-only validation branch**. The actual compiled daemon produced separate 66- and 70-block FAKECHAIN histories in two disposable localhost-only LMDBs. The **unmodified production read-only `forgecoin_chain_risk` snapshot/assessment code** fetched both native daemon RPC histories and reported `node_divergence` plus `node_height_gap` (four blocks) before synchronization. After a genuine P2P reorganization replaced the entire 66-block shorter fork, a second live RPC observation reported a critical `observed_reorg` of at least 66 blocks on the losing node, with no remaining divergence/height-gap event. No fabricated header data, public node listener, mining on MAINNET, wallet keys or payouts were involved.

**Scope:** This validates the observer's real daemon RPC integration and alarm classification. Both nodes ran on the same disposable GitHub CI host; this does **not** satisfy the required two *independently operated/hosted* production nodes, authenticated separate tunnels, eclipse-resistant cross-checking, or settlement authorization. The observer remains an alert, not a payout gate, checkpoint or consensus safeguard.



- Continuously examine **all credited canonical heights** beyond the existing limited ten-header maturity window, with bounded batches and restart-safe coverage tracking. Verify each credited block's hash, parent, reward and orphan status against independently authenticated canonical headers.
- Treat unavailable, truncated, malformed or conflicting historical RPC as unverified; preserve current ledger balances; on a canonical mismatch, persist first-conflict quarantine to LMDB before any future transfer.
- Prove at least 61-block native mining, mature credit, orphan/deep-fork reconciliation, ledger rollback, restart persistence, fee wallet allocation and wallet-transfer gating on disposable local networks, plus x86_64/ARM64 source agreement.
- Alert on hash concentration and node/peer health only from measured sources; avoid inferring unique miners from wallet count or treating a difficulty floor as a 51% threshold.
- Do not enable a public Stratum port, real payouts, FRG/mFRG issuance, production RPC, mining or hard-coded finality from this monitoring source.

Related: [full feasibility and security research](SECURITY_51_PERCENT_AND_TARI_MERGE_MINING_2026-11-02.md), [selected network ports](NETWORK_PORTS.md), [persistent quarantine handoff](handoffs/POOL-PERSISTENT-REORG-QUARANTINE-2026-11-02.md), [implementation issue #194](https://github.com/tgibbsz32/forgecoin/issues/194).
