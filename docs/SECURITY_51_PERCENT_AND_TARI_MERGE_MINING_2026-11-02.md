# ForgeCoin 51% resistance and Tari merge-mining feasibility (research, 2026-11-02)

> **Status: prelaunch research and operational safety plan, not a consensus or public-mining activation.** The frozen 20261026 identity, genesis hash, RandomX PoW, 120-second target, difficulty schedule, and 39480/39481/39482 service ports are unchanged. The selected mainnet remains unlaunched; draft PR #185 has not been merged.

## Executive decision

**Phase 1:** keep independent FRG RandomX mining, recruit independent miners/nodes and diversify pools, audit network difficulty/seed rules, monitor deep reorganizations and conflicting node tips, and apply conservative wallet/exchange settlement policies. Existing pool payout/reorg holds are an important component, not a substitute for independent PoW security.

**Phase 2 (sandbox feasibility only):** test whether a *Monero-format FRG parent block* can produce an accepted Tari RandomXM auxiliary proof, using current patched Tari code and disposable isolated FRG/Tari environments. Do not market FRG+Tari as supported or add a public toggle until an end-to-end valid block, coinbase/mempool/template reconstruction, stale-job treatment and upstream compatibility are proven.

**Phase 3 (separate consensus proposal):** evaluate FRG as an auxiliary chain merge-mined by existing Monero miners. This could recruit external RandomX proof-of-work, but requires an audited FRG AuxPoW consensus path (including XMR RandomX key/seed validation), upgraded pool/proxy/miner plumbing, replay and cross-chain binding rules, chain-selection modeling, a hard-fork strategy and independently reproduced tests. **It cannot be made safe by a pool configuration switch.**

## Why direction matters

| Proposal | Parent chain | Auxiliary chain | FRG security result |
| --- | --- | --- | --- |
| Mine FRG and Tari together | FRG (if interoperable) | Tari | FRG miners may earn Tari rewards and FRG participation *might* increase. It does not import Tari/Monero hashrate into FRG. |
| Merge-mine FRG with Monero | Monero | FRG | Monero miners *could* provide work to FRG, proportional to genuine adoption; not automatic and concentration still matters. |
| Independent FRG RandomX | FRG | None | Security scales with actual decentralized honest FRG hashrate; operational controls reduce exposure but do not eliminate 51% risk. |

Tari's actual architecture uses **four independent PoW lanes**: Monero merge-mined RandomXM, native RandomXT, SHA3x, and Cuckaroo29 (C29). Each lane targets 25% of rewards; this is Tari's *own* consensus, not a ready-made FRG protection.

Tari's current Monero merge-mining proxy intercepts Monero-compatible daemon `get_block_template` and `submit_block`, adds Tari commitment material into the parent coinbase extra field, and reconstructs the parent hashing blob/Merkle root. A Tari node verifies the proof without contacting the Monero blockchain. The fact that FRG derives from Monero makes a **lab compatibility test reasonable**, not proven. FRG's separate genesis, network consensus/RandomX seed, daemon RPC responses, reward construction and Tari's strict proof encoder may all affect interoperability. Verify current code behavior and patches, not older RFC prose alone.

**Security warning:** Tari published critical advisory GHSA-jm73-2949-8jcc on 2026-09-22 for attacker-controlled Keccak proof-state forgery in RandomXM. It reports affected versions <=5.7.0-pre.9 and patch 5.7.0-pre.10. No integration may copy or rely on that vulnerable representation; require exact patched-version review and proof-binding negative tests.

## What is cheap and worth doing now (non-consensus)

1. **Miner distribution and pool diversity — high priority.** Make both true solo mining and official pool mining work; facilitate *independent* pools and wallet-controlled mining. Publish verified pool share, miner concentration and network hashrate metrics, without pretending anonymous wallet counts prove unique operators. Alert when one pool/operator appears dominant; mining decentralization is the main protection against majority control.
2. **Independent observers and alerts — high priority.** Monitor at least two independently hosted full nodes over authenticated/private RPC (39481), compare chain tips and blocks at common heights, track suspicious reorg depths, divergent peer views, block delays, timestamp anomalies and difficulty changes. Persist incident evidence and require human review; monitoring cannot prevent a majority attack.
3. **Settlement-risk controls — high priority.** Keep the official pool's existing persistent LMDB reorg quarantine, ensure old credited blocks are periodically reaudited beyond the ten-header window, and do not enable payouts until a complete real 61+ block/reorg/fault-injection test passes. Gate bridge mint/release, exchange credits and merchant settlement on independently verified confirmations and configurable risk-based policies; avoid hard-coded promises that 60 confirmations stop a 51% adversary.
4. **P2P/eclipsing resilience — high priority.** Operate bootstrap peers on independent hosts/ASNs, retain outbound peer diversity and independently sourced block views; keep daemon, wallet and ZMQ RPC unexposed to the public Internet. Verify peer-handshake and seed identity on frozen mainnet. Do not add hard-coded untrusted peers or launch the old Oracle chain.
5. **Difficulty/timestamp tests — consensus verification, not a magic 51% fix.** Test frozen initial 500,000, 400,000 minimum, progressive LWMA90 from height 16, missing history, timestamps, abrupt hash changes, competing branches, native x86_64 and ARM64. **Do not use the legacy `main` constants as the chosen final schedule.** Difficulty floors can slow trivial low-difficulty attacks but do not defeat a majority of actual hashpower; over-aggressive floors can stall an honest low-hash network.
6. **Checkpoints — only with explicit governance and hard-fork review.** Unilateral or automatically generated signed checkpoints can suppress deep reorgs but centralize history selection, hinder recovery and be abused. No automatic checkpoint-on-alert rule and no silent consensus-finality change in the frozen launch.

### Security mathematics / reporting caveats

At target 120 seconds, estimated equilibrium hashrate is difficulty / 120 H/s. The specified 400,000 floor corresponds to ~3,333 H/s and the 500,000 initial target to ~4,167 H/s **as a mathematical equivalence, not measured live hashrate**. Neither number is an anti-51% threshold. Attacker risk depends on the *actual independently controlled honest and adversarial hashpower*, their sustained work and economic incentives. Avoid publishing a synthetic `security percentage` from pool API samples.

## Implemented read-only observer (source-only prototype; not deployed)

- [`tools/forgecoin_chain_risk.py`](../tools/forgecoin_chain_risk.py) compares two or more **trusted** node header ranges from *distinct* local RPC endpoints. Independent remote nodes must be accessed by separate reviewed SSH tunnels to localhost. It checks the selected frozen genesis hash on each poll and detects conflicting same-height hashes, observed local history changes, height rollback, stale tips, gaps and incomplete RPC responses. No RPC writes, private keys, network consensus modification, automatic pause or checkpoint.
- [`tools/test_forgecoin_chain_risk.py`](../tools/test_forgecoin_chain_risk.py) contains offline regression tests. Ten local deterministic tests passed before source finalization; this is **not** an integration test against frozen candidate daemons.
- Example after approved test nodes and tunnels are available (ports are *local tunnel endpoints*, not a change in selected mainnet port contract):

```sh
python tools/forgecoin_chain_risk.py \
  --node http://127.0.0.1:39481/json_rpc \
  --node http://127.0.0.1:39581/json_rpc \
  --state ./local-chain-risk-state.json
python -m unittest discover -s tools -p 'test_forgecoin_chain_risk.py'
```

- Exit 0 = observations returned with no alarms (NOT chain finality or evidence of safety); exit 1 = alert(s); exit 2 = unverified/error. First execution establishes an observation baseline. State file is deliberately local and contains no secrets. Observing only a bounded header window cannot prove there were no prior deep reorganizations.
- The watcher is **not scheduled, deployed, integrated with pool payouts or wired to alert delivery**. Until live release gates are satisfied, use only disposable/authorized test nodes. Independently authenticated observations and response playbooks are still outstanding.

## Experiment matrix before accepting FRG/Tari integration

- **FRG parent chain validity:** produce real isolated FRG block templates with coinbase extra commitment, prove both unmodified and modified parent blocks accepted under frozen selected FRG rules, and test rejection of malformed extra fields.
- **RandomX identity:** verify parent key/seed, block hashing blob, target thresholds, share/difficulty checks and valid Tari RandomXM proof from the *same* miner work. Check the stale-seed/seed-reuse policy; do not assume Monero mainnet seed and FRG seed are interchangeable.
- **Tari proof binding:** use patched Tari proof format, correct coinbase prefix reconstruction and Merkle inclusion, auxiliary chain depth and domain binding; negative tests must reject changed Tari header, changed coinbase, spoofed keccak state, swapped seed, old template, duplicate and malformed merkle branch.
- **Job routing:** test `get_block_template` and `submit_block` both with and without solved FRG difficulty; valid Tari-only shares must not be incorrectly submitted to FRG. Confirm fee wallet, reward attribution, stale-work handling and pool share accounting remain correct.
- **Safety:** disposable lab only; no changes to frozen consensus, no public Stratum, no released miner toggle, no mining against live mainnet and no pool payout signing.

## Release gates (P0 / P1 / R&D)

- **P0 before launch:** genesis permanent-unspendability verification; frozen PR #185 native integration/reorg tests; pool 61+ block canonical/credited-block reorg tests; independent node/peer review; documented incident runbook; trusted full-node monitoring; Windows/Android release validation and peer/port parity.
- **P1 before custody or exchange integrations:** multiple independent observers, settlement/confirmation policies, documented emergency pause and resume with independent manual authorization, notification runbook, public mining distribution metrics.
- **R&D, not a launch blocker:** patched Tari interoperability lab; FRG-as-Monero-auxiliary fork specification, hashpower-adoption analysis and outside cryptographic review.

## Source references (verified November 2, 2026)

- Tari implemented merge mining protocol: https://rfc.tari.com/RFC-0132_Merge_Mining_Monero
- Tari mining strategy / independent lanes: https://rfc.tari.com/RFC-0131_Mining and https://tari.com/tokenomics
- Current Tari native code: https://github.com/tari-project/tari/blob/development/base_layer/core/src/proof_of_work/monero_rx/helpers.rs
- Tari RandomXM security advisory: https://github.com/tari-project/tari/security/advisories/GHSA-jm73-2949-8jcc
- P2Pool Tari integration: https://github.com/SChernykh/p2pool#merge-mining
- Frozen FRG selected mainnet: [CURRENT_MAINNET.md](CURRENT_MAINNET.md)
- FRG port/exposure contract: [NETWORK_PORTS.md](NETWORK_PORTS.md)
- Existing pool persistent reorg hold: [POOL-PERSISTENT-REORG-QUARANTINE-2026-11-02.md](handoffs/POOL-PERSISTENT-REORG-QUARANTINE-2026-11-02.md)
- Native consensus draft: https://github.com/tgibbsz32/forgecoin/pull/185

No production code or consensus parameters were changed as part of this decision.
