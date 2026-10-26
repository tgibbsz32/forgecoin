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

- An unfunded throwaway wallet was created through the new wallet RPC, its
  public address and zero balance verified and the wallet closed. GUI
  Create and Restore still need interactive owner-side testing.
- The throwaway wallet reported zero balance against genesis-only RPC;
  live balance scanning, sending/receiving and recovery remain untested.
- RandomX mining and pool Stratum were tested on separate disposable
  historical research networks, **not on this fresh mainnet**.
- Independent consensus review, preallocation unspendability, fully
  compatible native ARM64 binaries, public peer bootstrap and explorer,
  validated reorg-safe pool accounting/payout, and explicit public
  launch authorization remain pending.
- Until the genesis coinbase output can be proved permanently unspendable
  (or consensus explicitly disallows its spending), a categorical
  'zero-premine' public claim is not justified.
- No funds, wallet keys, actual fee treasury or official fee transfers were
  generated or entrusted to the assistant.

**Treasury-wallet owner instructions:** `TREASURY-WALLET.md`.
