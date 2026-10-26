> [Current mainnet specification, tokenomics and release status](docs/CURRENT_MAINNET.md) — October 26, 2026; prelaunch.

# ForgeCoin source build status

## October desktop and explorer

The current Windows application is under `apps/desktop-tauri` and requires Node.js,
Rust/MSVC, C++ build tools and WebView2. Follow its README for dependencies.
First build `forged.exe` and `forge-wallet-rpc.exe` from this checkout, then provide
them as `src-tauri/binaries/forged-x86_64-pc-windows-msvc.exe` and
`src-tauri/binaries/forge-wallet-rpc-x86_64-pc-windows-msvc.exe` within that app.
Include any runtime DLLs required by your native toolchain in the final package.
These generated files are excluded from Git. A fresh package has not been validated
from this combined source snapshot.

The independent explorer is under `apps/explorer`; install its locked Python
dependencies and read its deployment notes. The deployment script is specific to
an existing host and must be reviewed before reuse.

## Native source

The source includes vendored dependency directories rather than Git submodules.
Pass `-DMANUAL_SUBMODULES=1` to CMake to skip the inherited submodule-history check.
A starting configuration, after installing the required compiler and dependencies:

```sh
cmake -S . -B build -DMANUAL_SUBMODULES=1 -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel 2
```

These are configuration/build entry points, not a claim of a verified clean build.
The complete native build from this publication snapshot remains to be validated.
Dependencies and compiler choices differ by platform; the inherited `docs` and
`contrib/depends` material supplies reference information and may still say Monero.
For Windows, use the matching MSYS2/MinGW environment for the native build.

To avoid embedding local account names, build in a neutral directory and configure
supported GCC/Clang prefix-map flags for source/debug paths. Scan final executable
strings and symbols as well as package documents before public distribution.

The desktop wrapper has separate instructions in
[apps/desktop/BUILDING.md](apps/desktop/BUILDING.md). Build the daemon and wallet
from this tree before packaging. Do not substitute older patched release binaries
and describe them as builds of this commit.
