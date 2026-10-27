# Oracle native ForgeCoin release unit — staged, disabled

**Staged October 27, 2026. This is NOT authorization to start mainnet or mine.**

The older `forgecoin-mainnet-staging.service` still points at a stale October 20 build. It is inactive but must **never** be used for the fresh FRG mainnet. This separate unit uses the verified October 26 ARM64 source-matched daemon.

## Installation (completed on Oracle)

- `/etc/systemd/system/forgecoin-mainnet-20261026.service`: installed via `sudo install`, systemd-analyze verify passed. **Disabled and inactive**.
- `/opt/forgecoin-ops/verify_launch_gate.py`: **earlier pinned-hash/genesis/consensus/fee validator installed** (SHA256 `bf6e36d33391b9bb166842ae9ee9130ca90286cbcca1784b255abcc4e9c616ef`). The latest source version adds stricter native currency-term assertions (SHA256 on staged Oracle home copy `967cd59939b20ffad20d7e25f9a3099bcaaa3e100065609800d0fa815b87bdae`); its privileged installation was **blocked**, so the latest script is staged at `/home/ubuntu/verify_forgecoin_launch_gate_20261026.py` but is NOT yet installed under `/opt`. The operator must install and re-verify the reviewed latest version before public release.
- Uses the binary `/home/ubuntu/forgecoin-mainnet-20261026/build-release/bin/forged`, SHA256 `3dd3d0c10f41ef2f887314221e0b9adec9571b98a83c9783a78a6290156506bd`.
- New database path `/home/ubuntu/forgecoin-mainnet-20261026/production-blockchain-20261026`. Never mix with archived devnet, 20261020 candidate, or QA databases.
- P2P binds `0.0.0.0:39480` only **if** the service is launched; daemon RPC `127.0.0.1:39481`, ZMQ `127.0.0.1:39482`. No public wallet RPC, mining autostart, remote RPC, or pool activation in this unit.
- `ConditionPathExists=/etc/forgecoin/approved-mainnet-launch.json`. The file **does not exist**. Independent `ExecStartPre` also requires `release_authorized=true` and `stage=released` in the selected manifest plus an operator-approval marker tied to SHA256 of the exact manifest, genesis, and pinned daemon binary.
- The currently installed preflight passed the exact genesis, ports, consensus policy, 1% operator-fee destination and executable checksum (native 8-decimal currency assertions are present only in the latest staged revision). Its `--require-authorized` mode **correctly rejected** the frozen, unapproved manifest. Both validator versions fail closed while the marker and authorization are missing.
- Systemd warnings about the preexisting OCI monitoring-agent unit file permissions were unrelated to this service.

## Accepted native identity

20261026 genesis nonce, hash `4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c`; address prefixes 190/191/192; 500,000 initial RandomX block difficulty, 400,000 floor and 120-second target; LWMA height-16 activation; eight decimal places; 1% optional pool operator allocation to the designated, separately controlled fee wallet. Solo miners pay no pool fee.

Genesis caveat: inherited height-0 11.92092895 FRG coinbase is described as a fork byproduct intended unspendable. Permanent unspendability is not cryptographically proven, and the user has accepted disclosing that residual issuance uncertainty. No one should advertise a formally demonstrated zero-premine genesis.

## Remaining release evidence

1. Operator's intended first **public** solo-mined block and independent second-node consensus/synchronization verification; no public block has yet been mined. Offline QA did not submit a block.
2. Pooled mining: real XMRig RandomX share acceptance **passed**; full winning block submission and canonical propagation **not tested**.
3. Pooled 60-block maturity, canonical reward reconciliation, PPLNS orphan/reorg/crash behavior and **idempotent, chain-confirmed payout settlement** remain unverified. Pool wallet transfer code is still compile-time gated and payout-disabled.
4. Production pool reward wallet and proof that the operator controls the separate fee wallet; enforce authenticated wallet RPC and safe key backup. Do not place either key in Git or website files.
5. Windows native mining/wallet public release, independent second-node build verification, Android real RandomX/FRG wallet native support, signed release checksums, public installation documentation.
6. Explicit final operator launch approval and matched manifest digest. The existence of the service file alone is never sufficient authorization.

## Operational guardrails

Never run the older staging unit. Never enable or manually start this unit while the release marker is absent. Do not change its SHA256 pin or create approval marker to bypass a failed test.

The release marker must only be created as part of a verified production cutover after the actual binary/manifest hashes and security requirements are signed off. A positive **read-only preflight is not a launch approval**.

Pool monitoring and block explorer are already live read-only; both correctly return unavailable when no daemon exists. Windows Android QA APK is **not** a wallet/miner release.
