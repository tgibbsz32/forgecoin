> **Current specification — 2026-10-26:** [Frozen mainnet parameters, tokenomics and release status](../CURRENT_MAINNET.md). Public launch is not authorized. Main-branch executables still implement legacy rules; these instructions are not proof of new-mainnet compatibility.

# Software guide — developers, node operators and miners

**Applies to current source only.** A source directory, UI button or successful compile is not evidence of a vetted, publicly released product. See [status](Current-Status.md) before attempting a deployment.

## Which software is which?

| Software | Path | Technology | Current use |
| --- | --- | --- | --- |
| Full node / consensus daemon | `src/` → `forged` | C++ / Monero-derived / RandomX | Legacy development chain and isolated consensus candidates |
| Wallet RPC | `src/` → `forge-wallet-rpc` | C++ | Local wallet handling; protect wallet files/passwords and loopback |
| Current Windows app | `apps/desktop-tauri/` | Tauri 2 / Rust / React / TypeScript | Wallet/node/Solo/custom pool controls, **release validation incomplete** |
| Earlier Windows app | `apps/desktop/` | C# Windows Forms | Historical implementation; not the current primary app |
| Web explorer | `apps/explorer/` | Separate explorer service | Hosted legacy development-chain lookup; do not confuse with fresh-mainnet explorer |
| Official-pool preparation page | `apps/pool-site/` | Static HTML/CSS | Public status/readiness only; **no mining endpoint** |
| Pool verification experiments | `services/pool_research/` | Python, C++, SQLite | Synthetic-only PoW tests, not account balances or a payout processor |
| Governance experiment | `services/governance_api/` | API research | Not binding native consensus governance |

## Clone and inspect (non-destructive)

```powershell
git clone https://github.com/tgibbsz32/forgecoin.git
cd forgecoin
git rev-parse HEAD
git status --short
```

Use a **new disposable checkout** for validation. Never overwrite an existing customized consensus tree, wallet directory, seed material or working chain data.

## Windows core build — development reference

Read [BUILDING.md](../../BUILDING.md) and [desktop preflight evidence](../DESKTOP_MINING_PREFLIGHT_2026-10-25.md) first. The following is a recorded **development** command sequence for MSYS2 MinGW64, not a complete portable or release build:

```powershell
$env:PATH = 'C:\msys64\mingw64\bin;' + $env:PATH
cmake -S . -B build-disposable -G "MinGW Makefiles" -DMANUAL_SUBMODULES=1 -DCMAKE_BUILD_TYPE=Release -DARCH_ID=x86_64
cmake --build build-disposable --target daemon wallet_rpc_server --parallel 2
```

A previous native build needed explicit `ARCH_ID=x86_64` so RandomX JIT sources were included. **Do not automatically treat resulting executables as a release.** Confirm source commit, build recipe, architecture, runtime imports and artifact digests; run isolated tests. Store generated executables outside Git.

Tauri expects host-specific sidecar filenames. Existing `tools/stage_windows_sidecars.py` uses an explicit digest allowlist for a reviewed MinGW-built pair; the `-msvc` filename suffix is a Tauri host naming convention, **not** a claim the C++ binary was built with MSVC. Never rename arbitrary binaries to bypass integrity checks.

## Desktop development

From `apps/desktop-tauri/`, after native sidecars are safely staged and dependencies installed:

```powershell
npm ci
npm run test:rust
# Do not run the UI against real wallets/peers during isolation testing.
# npm run tauri:dev
# npm run tauri:build
```

Do **not** blindly run either commented command until you have checked saved application state, sidecar provenance and external network isolation. The current app may default to a **public legacy-chain peer** and persistent local data. Desktop mining's source controls are not proof of successful Solo or Pool payouts. Refer to [desktop README](../../apps/desktop-tauri/README.md) for UI features; follow [release verification](Testing-and-Release.md) for evidence requirements.

## Node and privacy precautions

- The frozen mainnet P2P port is **39480**. Daemon RPC is **39481**; wallet RPC must remain protected and local.
- A wallet **recovery phrase, private/spend key and password are secrets**. Do not post them to issues, logs, websites, screenshots or test summaries. Wallet address is public but should still be excluded from private fixture publications.
- For offline candidate tests, use fresh test-only data directories, loopback RPC/P2P/ZMQ and disposable wallets; never start an existing public service or chain accidentally.
- Restoring wallet scans, synchronizing to a public peer and selecting miner/pool settings can have network side effects. Obtain explicit approval for actual mining/transactions.
- Run XMRig only from an approved binary. The current downloaded v6.26.0 ZIP **fails publisher checksum equivalence** ([issue #95](https://github.com/tgibbsz32/forgecoin/issues/95)); do not execute it to “see if it works.”

## Read-only verification before any release

```powershell
py -m unittest tools.test_preflight_desktop_mining -v
py tools/validate_desktop_mining_evidence.py --self-test
```

The PE preflight detects malformed binaries but does **not** verify signatures or benign behavior. `FOUND` is not approval. Consult [Testing and Release](Testing-and-Release.md) for the full acceptance matrix.

## Public pool and explorer

There is **no active official pool payout endpoint**. The [pool preparation page](https://150.136.209.227/pool/) is informational only. Do not submit wallet secrets to pool-site pages or infer hashrate/payout from placeholders. The existing explorer is for the **old** chain; confirm network identity and freshness for any block data shown.
