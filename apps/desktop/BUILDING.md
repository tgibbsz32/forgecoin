> [Current mainnet specification, tokenomics and release status](../../docs/CURRENT_MAINNET.md) — prelaunch; public distribution NOT approved.

# Building ForgeCoin Windows Forms Desktop — November 4, 2026

The current `main` branch Windows Forms source can be compiled, but native
ForgeCoin consensus **remains in draft integration PR #185**. A successful
source compilation or presence of `forged.exe` is not acceptance of wallet
recovery, private-key protection, funded transfers, solo/pool mining, compatible
network identity or a clean Windows installer.

## 1. Safe source-only compilation (no wallets or mining)

Use Windows PowerShell and the .NET Framework 4.x C# compiler:

```powershell
Set-Location apps/desktop
.\build.ps1 -SourceOnly
```

This checks the frozen documentation identity and creates only
`qa-build/ForgeCoin-Desktop-SourceOnly/ForgeCoin Desktop.exe`.
**No daemon, wallet RPC, XMRig binary or public release bundle is included.**
The GUI is a source compilation artifact, not a functional wallet installer.
Choose a fresh `-OutputRoot` for repeat compilations.

## 2. Private prelaunch packaging only

For a controlled, offline test of **exact existing prelaunch sidecars**:

```powershell
.\build.ps1 `
  -PrivatePrelaunch `
  -ForgeBin C:\path\to\reviewed\native\bin `
  -OutputRoot C:\path\to\unique-private-qa-output
```

The script verifies selected genesis nonce/hash, network UUID, ports
39480/39481/39482, address prefixes 190/191/192, and release/payout locks
against `docs/mainnet.identity.json`. It requires the native `forged.exe`
and `forge-wallet-rpc.exe` SHA-256 files to exactly match the repository's
**existing 20261026 private prelaunch candidate pins**. Unrecognized, legacy
or modified executables are rejected before output creation. It never
modifies existing private wallet data or repairs binaries in place. The
output is marked `PRIVATE-PRELAUNCH-NOT-FOR-DISTRIBUTION.txt`.

**These pinned hashes are NOT an independent proof** of clean source,
reproducibility, final consensus, or a trustworthy signer. Public packaging
without `-PrivatePrelaunch` is refused. Bundling XMRig is also blocked until
a reviewed binary/source and GPL license/disclosure package is approved.
Users can install an independent miner separately in future release testing.

## Release gates (separate from build success)

- Merge only independently reviewed frozen consensus and permanently reject
  genesis-output spends, including a full signed native input-validation test.
- Test native Windows wallet creation/recovery, wrong seed/password errors,
  independent recipient confirmation, spend, rescan and restart behavior on
  **disposable** wallets, never existing user wallets.
- Validate real solo and Stratum pool mining, mature 99/1 pool accounting,
  native wallet payout signing, and reorg-safe payout idempotency.
- Verify signed native binary provenance, DLL dependencies, clean Windows
  install/uninstall, security audit, and release manifest/checksums.
- Audit public peer/bootstrap, Oracle listeners and retired ports, TLS,
  explorer endpoints and pool website before user-facing distribution.
- Only after explicit launch authorization may an audited public release
  installer and tagged GitHub Release be published.

Tauri has a separate [prelaunch README](../desktop-tauri/README.md) and
requires manifest-pinned matching native sidecars, not old Windows Forms
binaries substituted to satisfy a packaging build.
