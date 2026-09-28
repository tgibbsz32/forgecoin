# Building the ForgeCoin Desktop Application

## Requirements

- Windows with .NET Framework 4.x
- A completed ForgeCoin Windows build containing `forged.exe` and `forge-wallet-rpc.exe`
- The MinGW runtime DLLs used by that build
- Optional XMRig 6.26.0 Windows x64 files for the Pool Mining tab

The desktop source is a single Windows Forms application in `Program.cs`. The included build script compiles it with the .NET Framework C# compiler, copies the two ForgeCoin executables and required MinGW runtime libraries, and optionally packages XMRig.

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
