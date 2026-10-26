# ForgeCoin Desktop — fresh mainnet 20261026 prelaunch validation

**Scope: NEW CHAIN ONLY, genesis nonce 20261026. NOT LAUNCH-APPROVED.**
The historical Phase 3 tests in this repository applied to the now-retired
development chain (genesis nonce 10000 and ports 19480/19481). They are not
proof that the new mainnet, its wallets or mining pool are production-ready.

## Actually verified on 2026-10-26

- New mainnet config uses network UUID
  `bd936359-09e4-4fdb-8ec0-12fa9d6ef090`, native address prefix 190
  (191 integrated, 192 subaddress), P2P 39480, daemon RPC 39481, two-minute
  target, starting difficulty 500,000, difficulty floor 400,000 and LWMA
  adjustment beginning at height 16 using N=90.
- The matching `forged.exe`, `forge-wallet-rpc.exe` and
  `forge-wallet-cli.exe` **compiled and linked** from the same new-mainnet
  source in a fresh isolated Windows MinGW/CMake/Ninja build.
- Windows Forms `Program.cs` compiled with the installed .NET Framework
  C# compiler. The app uses fresh, separate blockchain/wallet/ring
  directories and local RPC `127.0.0.1:39481`.
- Read-only genesis smoke: matching daemon launched `--offline`, with
  localhost P2P/RPC, into a new disposable chain data directory; reported
  RPC `height == 1`, nonce `20261026`, **0 peers**, and genesis hash
  `4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c`.
  It has **one** 11.92092895 FRG genesis output with unlock height 60.
  **No block was mined, and the daemon was stopped** after verification.
- Six new static mainnet identity tests and 19 pool source/build-guard tests
  passed against the fresh candidate before freezing the genesis hash.
- The desktop's Start Solo and Start Pool handlers are intentionally
  **prelaunch-disabled**. A successful compiler build is not a claim that
  they passed live new-mainnet mining or official pool share tests.
- The desktop package build verified all three native hashes against
  `config/mainnet.identity.json`, produced an owner's Downloads ZIP,
  and portable CLI/RPC/daemon executables passed help with no MSYS2 PATH.
  The GUI also passed a noninteractive startup smoke.

## Outstanding validations — MUST NOT claim they passed

- **The actual Windows Forms GUI wallet create/restore lifecycle has now been exercised.** On an offline genesis-only matching node, the native wallet RPC created an unfunded disposable wallet; the GUI displayed the seed dialog and public address; the test closed it, restored it from its mnemonic into a separate disposable name, and compared addresses. The restored public address matched, both wallet files were then deleted and the owner treasury was not touched.
- The throwaway wallet reported zero balance against genesis-only RPC;
  actual on-chain transfers and chain rescans remain untested. Unfunded recovery was verified through the Windows GUI.
- RandomX mining and pool Stratum were tested on separate disposable
  historical research networks, **not on this fresh mainnet**.
- Independent consensus review, preallocation unspendability, fully
  compatible native ARM64 binaries, public peer bootstrap and explorer,
  validated reorg-safe pool accounting/payout, and explicit public
  launch authorization remain pending.
- Until the genesis coinbase output can be proved permanently unspendable
  (or consensus explicitly disallows its spending), a categorical
  'zero-premine' public claim is not justified.
- No real user wallet recovery phrase, wallet password, spend key, pool fee payout or actual fee transfer was handled by the test. A separate owner-controlled public pool-fee address has been recorded in a subsequent pool configuration branch. The owner retains the wallet secrets.

**Treasury-wallet owner instructions:** `TREASURY-WALLET.md`.

## Wallet-RPC authentication gate (v0.2 private prelaunch)

The previous v0.1 GUI started `forge-wallet-rpc.exe` with
`--disable-rpc-login`, so it was unsuitable for funded treasury custody.
The v0.2 GUI generates an ephemeral 256-bit random password, starts the
wallet RPC with `--rpc-login` bound to 127.0.0.1, and uses .NET HTTP
Digest credentials on requests to that wallet service.

Actually exercised against the same packaged native wallet RPC on an
isolated, genesis-only, offline daemon (height 1): unauthenticated RPC
request returned **401 Unauthorized**; a .NET `HttpWebRequest` with Digest
credentials successfully received `get_version`; both processes were
stopped afterward; no blocks were mined, no funded wallets accessed, and
no phrase was output. A separate Windows C# build of the updated GUI
passed; **13 mainnet tests + 19 C pool source tests passed**.

The later **interactive GUI automation** did successfully exercise the Create, seed-backup dialog, Close, Restore, address equality and Close workflow on disposable files with zero mined blocks. This is not an independent security audit and the owner should still independently restore their actual wallet offline before funding it. The RPC credential in the child process command line is potentially visible to privileged local processes.

## Actual interactive GUI wallet lifecycle (private prelaunch v0.4)

A reproducible Windows Forms integration test is available under
`apps/desktop/tests/GuiCreateRestoreSmoke.cs` and
`apps/desktop/tests/run-gui-create-restore-smoke.ps1`. It uses the **native
new-mainnet** `forged.exe` and `forge-wallet-rpc.exe`, a private offline
genesis-only chain directory, and its own disposable GUI wallet names.
The test neither touches the operator's existing treasury files nor
prints or saves a private mnemonic in the results.

Verified through the **actual desktop GUI event handlers** on Windows:

1. Authenticated native wallet-RPC startup from the packaged `bin` directory.
2. Click/create a synthetic encrypted wallet; display its 25-word recovery dialog.
3. Display the expected-length native public receiving address in Wallet.
4. Close wallet, then restore from its synthetic 25 words into a **different**
   wallet filename using a masked seed-entry dialog.
5. Confirm exactly matching recovered public address and close the wallet.
6. Stop the isolated daemon; confirm it remained at **RPC height 1**, with
   no submitted/mined blocks. Delete only four disposable synthetic wallet
   files, leaving the owner's treasury untouched.

The test output contained no seed or private key. Source-level tests now
also check for per-session Digest authentication, address-copy-only UI,
no mnemonic clipboard button, minimum password length, and wallet
filename collision protection.

**Scope limits:** even with tested offline wallet creation and recovery, this
does not establish live receive/send maturity, audited private-key custody,
real pool Stratum accepted shares/payouts or correct activation of SOLO
mining. Those must pass independent launch gates before public release.
