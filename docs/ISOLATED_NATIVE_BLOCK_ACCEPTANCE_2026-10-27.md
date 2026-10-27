# ForgeCoin: isolated native wallet, template, and block acceptance

**Date:** 2026-10-27. This is a disposable offline-chain acceptance exercise,
**not** an official pool, public-network launch, mined-share reward or payout.

## Source-matched binaries

- Disposable source checkout: `0f3a9a2820a6285838fb45227a34c65957615e38`.
- Windows MinGW `forged.exe` SHA-256:
  `600a76d02fbf9f46825ca989daf1c74187aa3bf524d651c35cfe6fbbc1fd2836`.
- Windows MinGW `forge-wallet-cli.exe` SHA-256:
  `0844AEAC38DA0C2BFDB6F85FA8F2C9C0931499678337D00BE873BAB769DE5A79`.
- These are source-matched disposable build artifacts, not release signatures.

## Disposable test wallet and recovery

An independent wallet was created with the source-matched wallet CLI in
`--offline` mode, using new random credentials, and then reopened offline.
The wallet file, `.keys` file, generated wallet password and full 25-word
recovery phrase were encrypted into a Windows **DPAPI CurrentUser** archive
outside the source repository. A separate verification decrypted the actual
archive and confirmed both file contents and 25-word phrase. The wallet was
named and isolated as a `legacy-prefix90` disposable test wallet.

No mnemonic/password/wallet keys or backup archive is committed, logged in
this document, or reported through ChatGPT. DPAPI alone is **not** a portable
backup: before real funds are used, the owner must independently record a
secure offline recovery phrase/password backup.

**Network-identity release blocker:** The compiled wallet's help still says
`monero-wallet-cli`. The source's current mainnet address prefix is **90**,
while a separate provisional future mainnet proposal referenced **190**.
The test wallet belongs to the source checkout's currently implemented
configuration; it is NOT an approved final mainnet FRG receiving wallet.

## Real, disposable daemon template

`tools/capture_isolated_native_template.ps1` checked the daemon binary hash,
refused occupied test ports and used an empty independent chain data directory.
It launched `forged.exe` with `--offline`, localhost-only RPC/P2P/ZMQ
bindings and `--no-igd`. The wallet's **public test address** was read from
a local private file. No wallet spending or private keys were supplied to RPC.

At isolated chain height 1, the native daemon returned
`get_block_template` with network difficulty **1**, and a hashing blob of
**76 bytes**. The complete template was stored in a private LocalAppData
capture directory, not in Git. An earlier real capture passed the offline
native RandomX/template-bound check at height 1, with nonce offset **39** and
`POW_THRESHOLD_MET_UNCREDITED`. No share was credited.

## Native block acceptance (separate test)

A fresh isolated daemon generated a block template at height 1/difficulty 1.
With the explicit `-SubmitUnmodifiedBlock` test flag, the unchanged daemon
block candidate was submitted through the private `submit_block` RPC.
The daemon returned `status=OK`, the chain height advanced to 2, and
`get_block_header_by_height(1)` returned canonical block hash:

```text
088652005ec0c3d476c1ada8b78ff43579fea05562a22934f719358f554d646b
```

The PowerShell wrapper terminated the isolated daemon and reported no
ongoing service. The candidate was **not** discovered by XMRig or through
a production Stratum pool; at test difficulty 1, an unchanged template can
meet the target. This does not validate coinbase-reserve modifications,
native share-to-block reconstruction, PPLNS, block maturity, payouts, or
production consensus configuration.

## Other repeatable evidence

- Pinned XMRig v6.26.0 synthetic Stratum test passed with two actual
  RandomX submissions independently verified by the native worker,
  `records=2`, `credited=0`, in a loopback-only unprivileged namespace.
- Broad offline pool research test collection passed **93 tests** with
  **4 skipped** after fixing package-aware test imports.
- DPAPI wallet backup/restore dummy test passed encryption, decryption,
  file equality and overwrite rejection.
- The user-owned disposable test directories and encrypted archives remain
  outside Git. No production miner, pool service, wallet RPC or payouts ran.

## Header-nonce-modified native block acceptance

A separate isolated run used the new `services/pool_research/nonce_candidate.py`
reconstruction and `tools/build_isolated_nonce_candidate.py` helper to replace
only the four-byte header nonce with `01020304`, consistently in the full
`blocktemplate_blob` and its `blockhashing_blob`. The original captured blobs
were preserved in the same private test directory. The candidate builder
requires matching native block headers, a changed nonce, an isolated
height-1/difficulty-1 template, and exclusive private output-file creation.

The fresh offline daemon was started with separate localhost test ports
**49680/49681/49682** and a new empty disposable data directory, leaving an
existing independent test daemon on its own ports untouched. The modified
complete block was submitted to the local `submit_block` RPC. The daemon
returned `status=OK`, the chain reached height 2, and its canonical height-1
block hash was:

```text
89e44649462164ceaa28284407adf0302d108a1dd3b29bb72e505dd923c7a6ca
```

The script confirmed termination of its test daemon. Five header-reconstruction
regression tests passed, and the broader offline research suite passed **98 tests**
with **4 skipped**. Independently, the offline native RandomX worker
verified the modified hashing blob at nonce offset **39**, difficulty **1**,
and reported `credited=0`. The check is reproducible with
`tools/verify_isolated_nonce_candidate.py` against the original and modified
private captures. No source or wallet secrets were uploaded.

**Scope limitation:** This establishes acceptance of a *nonce-modified*
native candidate, **not** coinbase reserved-byte modification, miner-supplied
Stratum block reconstruction, network-difficulty mining under production
conditions, or pool reward accounting. The test deliberately uses difficulty 1
and does not demonstrate useful mining work or financial settlement.

## Outstanding gates

The **critical next feature** is mapping a miner-specific Stratum nonce
and reserved coinbase bytes into a complete reconstructed native block
with consensus-correct CryptoNote transaction-tree root. Only after
independent RandomX validation and the isolated daemon's acceptance of
that miner-derived block can the real pool block lifecycle be called tested.
Reward maturity, orphan handling, PPLNS and wallet payout reconciliation
remain separately blocked. Do not interpret this experiment as mainnet
authorization.
