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

## November 4 native wallet GUI integration (private QA only)

The Windows Forms UI now includes **Restore 25 words** for disposable,
English-language, Monero-derived native FRG test wallets. It supplies the
restoration RPC with `restore_height=0` to rescan from genesis, checks a
plausible returned public address, enforces a distinct non-existing wallet
filename and 12-character minimum password, and does not print a mnemonic,
wallet password or RPC error payload. Recovery entry is never sent to
websites or cloud services; it reaches the local wallet-RPC process only.
The backend must be a separately reviewed native FRG wallet, **not an
old-chain or funded owner wallet**.

Send input now uses a separately testable exact **8-decimal atomic-unit**
parser: it refuses rounding, commas, scientific notation, overflow and
nonpositive values. It prepares a native `validate_address` RPC call
before any later transfer, requests no transaction secret key and treats
wallet-RPC timeouts as *ambiguous*: the UI must not automatically retry.
Native solo/pool mining and native spending are still **hard-locked in
the desktop code** until explicit launch acceptance. This is preparatory
GUI integration, not a wallet transfer or accepted mining demonstration.

### Repeatable offline Windows QA checks

Run in a fresh clean checkout on Windows with the .NET Framework 4.x
compiler:

```powershell
python -m unittest discover -s tests/desktop -p "test_*.py" -q
& "$env:WINDIR\Microsoft.NET\Framework64\v4.0.30319\csc.exe" /nologo /target:exe /reference:System.dll /out:"$env:TEMP\FrgWalletInputTests.exe" apps/desktop/FrgWalletInput.cs tests/desktop/windows/FrgWalletInputTests.cs
& "$env:TEMP\FrgWalletInputTests.exe"
.\apps\desktop\build.ps1 -SourceOnly -OutputRoot "$env:TEMP\FRG-Desktop-QA-New"
```

The connected Windows QA checkout passed **29 desktop Python tests**, **49
C# wallet input assertions**, and **Windows Forms source-only compilation**.
The same session also executed the native Windows wallet RPC
candidate `forge-wallet-rpc.exe` with SHA-256
`739eefe916f9a93017c870dde63b45c8db532d43226dc888395860122c3e851b`,
matched against the checked-in frozen prelaunch candidate hash pin. The
[isolated native test script](../../tools/smoke_windows_wallet_restore_offline.py)
created a disposable native wallet, retrieved its 25-word recovery phrase
**without displaying it**, successfully restored that phrase to another
ephemeral wallet with the exact same public address, rejected the wrong
password, and reopened it from disk and after a full RPC-process restart.
**Exit 0, four PASS checkpoints** on the connected Windows computer.
The daemon endpoint was deliberately nonexistent, RPC loopback-only,
`--no-dns --no-initial-sync`; no block was mined and Oracle was not used.

Run this native acceptance only on a trusted private Windows QA machine,
using the pinned candidate binary and no original wallet data:

```powershell
python tools/smoke_windows_wallet_restore_offline.py `
  --wallet-rpc "$env:USERPROFILE\Downloads\ForgeCoin-Mainnet-20261026-Prelaunch-Wallet-v0.4\bin\forge-wallet-rpc.exe" `
  --max-seconds 65
```

This verifies the **native candidate Windows wallet RPC** independently
from the GUI, not clicking the new Windows Forms restore dialog end-to-end
and not final independently reviewed mainnet binaries. It does not validate
funded transfers, solo/pool mining, seed portability to Android, public
peers, clean installation or release signing.

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
