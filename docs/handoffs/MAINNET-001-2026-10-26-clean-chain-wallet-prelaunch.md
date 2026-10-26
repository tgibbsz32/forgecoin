# MAINNET-001 — 2026-10-26 — fresh ForgeCoin mainnet identity and owner wallet prelaunch kit

## Scope / permanent nonmining rule

Original `tgibbsz32/forgecoin` only. Dedicated isolated branch:
`feat/fresh-mainnet-identity-and-integration-gates-20261026`.
The owner's separate original development checkout with uncommitted consensus work,
unfinished mining listener research, and separate FCMP++/CARROT project are untouched.

**THE NEW MAINNET IS NOT LIVE. DO NOT MINE BLOCK 1 UNTIL EXPLICIT LAUNCH APPROVAL.**
The local genesis-only daemon tests ran offline with no miner or peers; all services
and payout/signing APIs remain disabled by default. No treasury secrets were created.

## Old Oracle chains retired and preserved

- Development network (genesis nonce 10000, P2P 19480, RPC 19481) had **RPC
  height 519** at retirement. It remains an old development chain only.
- Isolated candidate with genesis nonce 20261020 had an offline saved RPC height 3
  (genesis plus two mined blocks). It was not used as launch mainnet.
- On the Oracle Ubuntu ARM64 host, `forgecoin.service` and
  `forgecoin-mainnet-staging.service` were stopped and disabled; status
  verified inactive. Both chain LMDB data dirs moved off active paths into
  `/home/ubuntu/forgecoin-chain-archives-20261026`. No old chain file deleted.
- Tar archives were integrity checked and hashed:
  - dev `878fbdc36aa5553af5df583e8ffdc5c72df0efcf9f6021554e6b45b9b2826df6`
  - candidate `9778a453e6506ed6ea04aa9c1d8dfe1e036771634b50e304f9dccd66a191998d`.
- The old public explorer is still a web service, but the old daemon is offline.
  **The public explorer has NOT yet been redeployed for the new chain**;
  no public P2P or Stratum endpoint has been activated.

## Actual new mainnet consensus implementation

The historical Oracle `20261020` candidate's cryptonote config, hardfork
schedule, difficulty algorithm, and blockchain consensus source were preserved
and integrated into the original repository on a clean branch. Its **chain
identity only** changed:

- Fresh genesis nonce **20261026** (NOT 20261020).
- Unique network UUID `bd936359-09e4-4fdb-8ec0-12fa9d6ef090`.
- Address prefixes standard/integrated/subaddress `190/191/192`.
- P2P/RPC/ZMQ `39480/39481/39482`.
- Difficulty start 500,000 (mineable heights 1–15), minimum 400,000,
  two-minute target, LWMA N90 starting at height 16.
- 50,000,000 FRG supply constant, eight decimal places, candidate's
  original emission/coinbase genesis TX bytes.

The new mainnet's **genesis hash was independently returned by the newly
compiled Windows daemon** on isolated loopback RPC:
`4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c`.
This was RPC height **1** (genesis at height 0), nonce 20261026, zero
peers, one genesis coinbase output **1,192,092,895 atomic units =
11.92092895 FRG**, unlock height 60. **No blocks were mined.** Daemon
stopped after validation.

Genesis hash, nonce, UUID, ports, economics and binary SHA-256s are recorded
in `config/mainnet.identity.json` with `stage=genesis-frozen` and
`release_authorized=false`. `tools/verify_mainnet.py` was run against
the REAL binary on localhost 39481; it passed the strict nonce/hash/height
check and confirmed no launch authorization. Explorer source rejects
a chain with a mismatched nonce or full genesis hash.

## Native Windows matching wallet and GUI binaries verified

In a separate scratch CMake/Ninja release build (not copied from the old
candidate), the actual **Windows x64** `forged.exe`,
`forge-wallet-rpc.exe`, `forge-wallet-cli.exe` compiled and linked.
CMake's uppercase AMD64 detection had dropped required CryptoNightR
assembly and RandomX x86 JIT objects, causing undefined symbols.
Architecture normalization was implemented in
`src/crypto/CMakeLists.txt` and `external/randomx/CMakeLists.txt`,
after which all three **linked with exit code 0**.

Binary SHA256s, recorded in the manifest:
- forged.exe: `3efaf014c7fdfcea167630f1884abee2defd40f28f1e725b6c0a8fcede5b5c37`
- forge-wallet-rpc.exe: `739eefe916f9a93017c870dde63b45c8db532d43226dc888395860122c3e851b`
- forge-wallet-cli.exe: `e5e7a807b3a1b2c7702df9cad48dfde8871f4aab1ef662032e1b5bc5becbe991`.

Windows Forms GUI compiled via native .NET Framework csc and started without
error in a noninteractive process smoke. Native daemon, wallet CLI, and
wallet RPC EXEs passed portable `--help` invocation **with MSYS2 excluded
from Windows PATH** and embedded executable SHA-256 verification.

With only the **packaged binaries** and an isolated offline genesis-only
daemon, the wallet RPC successfully executed **create_wallet** using a
clearly disposable test password, **get_address** (97-character public
address), **get_balance** (zero), and **close_wallet**. Chain remained
height 1. Synthetic test wallet file/keys were deleted afterward; no
user wallet or key was accessed. Interactive GUI Create/Restore and
live on-chain wallet scanning still need owner-visible validation.

`apps/desktop/build.ps1` now fails closed unless **all three** exact
native binary SHA-256 values match `config/mainnet.identity.json`.
Desktop stores LMDB, wallets, and ringdb in uniquely suffixed
`*-mainnet-20261026` directories rather than reusing dev data.
Prelaunch solo and pool mining actions intentionally fail closed.
Tauri source was retargeted but **its production installer/build was
not executed** in this step.

## Private distribution (not an official GitHub release)

A complete private portable Windows GUI wallet/prelaunch archive was placed
on the user's own Windows PC under Downloads:
`ForgeCoin-Mainnet-20261026-Prelaunch-Wallet-v0.1.zip`
SHA-256 `48f9deb7328655a89ae84c82867534297c215c6904bc70c12222d9df5c42e403`.
Contains desktop GUI, new native EXEs, MinGW runtime DLLs, frozen
identity manifest, license, and `TREASURY-WALLET.md` instructions.
The wallet installer **does not bundle XMRig**, because mining is
prelaunch-disabled and correct GPL/source distribution was not verified.
Package was NOT uploaded to GitHub, deployed to Oracle, or shared with
third parties. An updated local ZIP may supersede the v0.1 package as
documentation and code are finalized.

The owner alone creates and backs up the final **operator fee treasury**
wallet on a trusted local Windows machine. **Only its public mainnet
receiving address** should be provided to configure `pool-fee-wallet`.
No secret phrase, wallet password, spend key or wallet file should be
copied to ChatGPT, the C pool, a public server, or the web dashboard.

## Automated tests and scope

- Fresh-mainnet/desktop security tests: **12 passed** on Windows Python.
- jtgrassie/FRG pool source/build guard tests: **19 passed**.
- Exact FRG 8-decimal monetary/1% fee native C tests: **40 passed**.
- Strict live localhost-only RPC genesis verifier: **passed** against
  compiled daemon at height 1; daemon stopped.
- Actual Windows desktop GUI noninteractive startup: **passed**.
- Native Windows daemon/wallet CMake targets: **all 3 linked**.
- Native portable `--help` tests: **all 3 passed**.
- Disposable wallet RPC create/address/balance/close: **passed**.
- No live mining, block submission, network announcements, pool payouts
  or user custody happened.

## Outstanding mandatory launch blockers

**11.92092895 FRG genesis output permanent unspendability remains
unproven**; its unlock height 60 does not prove nobody controls a spend
key. Do not claim categorically zero spendable premine. Need independent
security proof or explicit consensus prevention.

New-release native ARM64 build and exact-genesis agreement, authorized
public node bootstrapping, Windows GUI interactive backup/restore, genuine
Stratum/XMRig mainnet-equivalent accepted-block testing on a separate
disposable chain, payout/reorg/PPLNS accounting and security controls,
new public explorer/dashboard deployment, and owner approval remain
incomplete. This step **does not constitute mainnet launch**.
