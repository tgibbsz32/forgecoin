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

## November 4 — Native Windows wallet RPC is authenticated

The native Windows GUI **no longer starts the FRG wallet with
`--disable-rpc-login`**. Every wallet RPC call now requires a randomly
generated, per-process HTTP Digest credential. The credential is initially
written to a **new, owner-only Windows ACL-protected temporary config file**
so it cannot appear on the command line. The app authenticates a harmless
`get_version` request before removing that startup file; native wallet
requests (including wallet creation, 25-word restoration and balance
queries) never silently fall back to an unauthenticated request.

The native Monero-derived HTTP server advertises two RFC 2617 Digest
schemes, **MD5** and **MD5-sess**, and binds its nonce to the persistent
TCP session. A short-lived, explicitly authenticated loopback HTTP client
now reads only a harmless version challenge, drains the 401 response so
the connection can be reused, and sends sensitive wallet RPC data only
with a correctly computed Digest proof on the authenticated connection.
It disallows proxies/redirects, serializes wallet requests, bounds
responses, redacts native wallet stdout from the GUI, treats ambiguous
transfers as unverified, and disposes the secret session on exit. All
private wallet calls remain restricted to `127.0.0.1:39484`.

### Actual native Windows tests (connected PC)

Both tests require a trusted Windows QA machine and the **SHA-256 pinned
private candidate** executable in a local Downloads folder. They create
only temporary disposable native wallets and **never open the user's
existing wallet, connect to peers or Oracle, mine, or send funds**.

```powershell
.\tests\desktop\windows\Invoke-WalletDigestQA.ps1
.\tests\desktop\windows\Invoke-WalletSessionAcceptance.ps1
```

**Verified PASS on the connected Windows machine:**

- HTTP 401 with no authentication, HTTP 401 with incorrect credentials,
  HTTP 200 with correct native Digest authentication.
- The actual production `WalletRpcSession` created a disposable native
  wallet over authenticated RPC; its private auth config was deleted
  after successful handshake.
- A native **25-word recovery phrase** from that disposable wallet
  restored the exact same public FRG address via the actual wallet RPC.
- Incorrect wallet password was rejected; native wallet files reopened
  correctly, including after killing and restarting the wallet-RPC
  process with newly generated credentials.
- All test wallet data was temporary and removed after testing. **No
  password, mnemonic, wallet private key, address or RPC payload was
  printed to the terminal.** There was no standalone native daemon,
  PoW work, wallet transfer, Oracle or public P2P connection.

The Windows Forms source build and desktop source/security tests passed at
this checkpoint. The GUI's native Create/Backup/Restore/Close interactions
were **subsequently tested end-to-end on disposable native wallets** (see
the following updated acceptance section). No funded transaction or final
independently reviewed mainnet binary has been tested. The
pinned historical candidate is not a final independently verified
mainnet release. Native solo/pool mining and sends stay hard-locked.

## November 4 — Actual Windows Forms layout and offline-node acceptance

The **real WinForms GUI** was instantiated on the authorized Windows QA PC
with production-form source compiled under the **test-only**
`FRG_PRIVATE_UI_QA` symbol. That symbol is **not defined in normal desktop
builds or packages**. It redirects wallet/application storage to an empty
temporary sandbox, and the harness includes **no daemon, wallet-RPC or miner
executables**.

The test opened all seven tabs, exercised wallet controls at
**900×680** and **1040×760**, verified that Restore/Create/Send buttons
remain scroll-reachable, and confirmed that native Send, Solo Mining
and Pool Mining controls are disabled with short, readable captions.
Node startup is **disabled by default** before launch, and the local
offline test node option must be explicitly selected to enable it.
The public peer input is disabled in prelaunch. Unchecking offline mode
immediately disables node startup again. The test did not invoke node,
wallet or mining actions, and it verified there were no native processes
launched and no wallet files created.

**Connected Windows test result:** **46 real Windows Forms layout and
release-lock assertions passed** with zero failures, plus **38 Python
desktop source/security tests passed**.
The regression is compiled and run in GitHub Windows CI as
`tests/desktop/windows/WinFormsGuiLayoutQa.cs`, including its strict
temporary-directory isolation.

In addition to layout checks, the real native GUI now has **end-to-end
disposable wallet acceptance** (see below), but no physical clean-install
or funded transaction acceptance. Neither check authorizes mainnet.

### Native Create / Backup / Close / Restore — verified through real WinForms

Using the pinned historical prelaunch candidate
`forge-wallet-rpc.exe`, a second isolated GUI harness
`tests/desktop/windows/WinFormsNativeWalletQa.cs` drove the **actual**
Create Wallet, recovery backup confirmation, Close Wallet and Restore
25 Words buttons on the Windows PC. Its isolated QA build copied only
the native wallet-RPC executable and required runtime DLLs into a new
temporary folder. **No native daemon binary was present, and both
daemon port 39481 and wallet-RPC port 39484 were checked to be free
before launch.** The GUI launched and authenticated its own wallet
service using the per-session Digest and owner-only config flow.

**Result: PASS — 49 native GUI integration checks**, including a newly
created **25-word disposable native wallet**, GUI backup dialog, closing,
restoring to another new wallet file, and comparing the exact same
public address via authenticated RPC. The GUI closed the restored wallet
and disposed the temporary service. The test did not print seed words,
passwords, addresses, private keys or raw native RPC payloads. The
temporary wallet files were deleted.

This deeper test uncovered a real **timer-refresh regression**:
`RefreshMining()` previously enabled Solo Mining when no daemon was
running, overriding the prelaunch lock. This has been fixed and covered
by both Python source checks and actual WinForms UI regression
assertions, including during the native wallet test.

Native wallet Create/Open/Seed retrieval RPC now have distinct
cold-start timeouts rather than a two-second monitoring timeout.
The wallet RPC remains loopback-only and authenticated, with no
real network node, public peer, funds, transfer, solo miner, pool
connection or Oracle launch involved. This is **not a complete mainnet
release or a signed, clean-install Windows application**.

## November 4 — native Windows GUI RandomX SOLO mining acceptance

[PR #225](https://github.com/tgibbsz32/forgecoin/pull/225) fixes the
previous **three-second blocking native `start_mining` call**: the
desktop GUI now initializes native RandomX in a background worker, with
a bounded 60-second RPC timeout and visible start/stop/error state.
The ordinary Windows desktop **still cannot start mainnet mining**.

The separate **compile-time-only** private GUI QA entrypoint
`tests/desktop/windows/WinFormsSoloMiningQa.cs` requires **both**
`FRG_PRIVATE_UI_QA` and `FRG_PRIVATE_MINING_QA` defines. Compiling with
the mining flag alone explicitly **fails**. Neither define is present in
the normal `build.ps1` path. The harness creates a new temporary
wallet-free data tree; runs only the hash-pinned historical
`forged.exe` candidate on P2P/RPC **127.0.0.1**, `--offline`,
`--out-peers 0 --in-peers 0`; and checks the frozen genesis hash before
making any mining RPC call. No public or private peer may join.

**Verified on connected Windows:** the actual Node → Mining tab →
**Start Mining** → positive `mining_status.speed` →
**Stop Mining** GUI flow passed **134 live native integration checks**;
the native status reported **active**, then **inactive**, with
zero network peers. The desktop security source tests passed
**41/41**. Test process and chain files were cleaned up; FRG port
listeners were absent afterwards. This is a real native RandomX
operation, not a simulated GUI indicator. An independent local
full-block propagation test existed previously, so this acceptance
focuses on wiring **the GUI controls** to native RandomX, not
repeating genesis mining.

**Still missing:** GUI-to-native **pool/Stratum integration acceptance**,
production consensus provenance/final review, clean install, and
physical Android ARM64 wallet/miner functionality. The public wallet
spend, public Stratum, native pool payout and Oracle launch gates remain
off. **Do not package another public or private ZIP as a completion
milestone until remaining application work has passed.**

## Release gates (separate from build success)

- Merge only independently reviewed frozen consensus and permanently reject
  genesis-output spends, including a full signed native input-validation test.
- Test native Windows wallet creation/recovery, wrong seed/password errors,
  independent recipient confirmation, spend, rescan and restart behavior on
  **disposable** wallets, never existing user wallets.
- Native Windows GUI solo RandomX start/hashrate/stop **passed isolated
  offline integration QA**, but production consensus review remains.
  Finish Stratum pool mining through the desktop GUI, then verify native
  wallet payout signing and reorg-safe pool payout idempotency.
- Verify signed native binary provenance, DLL dependencies, clean Windows
  install/uninstall, security audit, and release manifest/checksums.
- Audit public peer/bootstrap, Oracle listeners and retired ports, TLS,
  explorer endpoints and pool website before user-facing distribution.
- Only after explicit launch authorization may an audited public release
  installer and tagged GitHub Release be published.

Tauri has a separate [prelaunch README](../desktop-tauri/README.md) and
requires manifest-pinned matching native sidecars, not old Windows Forms
binaries substituted to satisfy a packaging build.
