# Building the ForgeCoin Desktop Application

## Requirements

- Windows with .NET Framework 4.x
- Rust toolchain (cargo) for the isolated Solana devnet wallet helper; use Cargo.lock and --locked
- See SOLANA-WALLET-DEVNET.md for the new devnet wallet's limitations and recovery safeguards
- A completed, hash-verified ForgeCoin prelaunch Windows build containing `forged.exe`, `forge-wallet-rpc.exe` and `forge-wallet-cli.exe`
- The MinGW runtime DLLs used by that build
- Optional XMRig 6.26.0 Windows x64 files for the Pool Mining tab

The desktop source is a Windows Forms application in `Program.cs` and `SolanaWalletTab.cs`, plus a Rust Solana devnet wallet helper. The build script compiles both C# files and the Rust helper, verifies and packages all three approved ForgeCoin native executables, and copies the required MinGW runtime libraries. XMRig remains optional; prelaunch mining remains disabled.

From PowerShell:

```powershell
.\build.ps1 -ForgeBin C:\path\to\forgecoin\build\release\bin
```

To include pool mining support, pass the extracted XMRig release directory:

```powershell
.\build.ps1 `
  -ForgeBin C:\path\to\forgecoin\build\release\bin `
  -XmrigRoot C:\path\to\xmrig
```

Do not restore the earlier binary-patching build process. This repository fixes the inherited checkpoint data and eight-decimal wallet formatting in source. Build the native binaries from this source tree before packaging the desktop application.

Place release binaries under an untracked `release` directory and publish them as tagged GitHub Release assets with SHA-256 checksums. If XMRig is included, also include its GPLv3 license and matching source archive.
