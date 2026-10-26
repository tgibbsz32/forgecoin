# ForgeCoin Desktop

> Source publication: generated native sidecars are not included. Build the node
> and wallet RPC from the repository root and stage them as described in
> [BUILDING.md](../../BUILDING.md). References below to included/tested binaries
> describe the earlier local development package, not this source checkout.

Minimal Windows wallet and CPU miner built with Tauri 2, Rust, React and TypeScript.

## Features

- Wallet: create/open, exact 8-decimal balance, receive/copy address, review fee then send, recover from a 25-word phrase, reveal/hide backup phrase.
- Miner: Solo through the local ForgeCoin daemon; Pool through a user-installed XMRig and user-entered third-party ForgeCoin pool. No pool is hosted, bundled, advertised or selected automatically.
- Transactions: account 0 incoming, outgoing, pending and failed transfers. Incoming mempool transactions appear after confirmation; cached history remains available when the node is offline.
- Settings: node URL, explicit ForgeCoin P2P peer, XMRig path, pool host:port, TLS and CPU threads.
- No embedded explorer, remote web pages or arbitrary shell access from the frontend.

## Run and build

Requires Windows x64, Node.js, Rust MSVC toolchain, Microsoft C++ Build Tools and WebView2.

```powershell
npm ci
npm run tauri:dev
npm run test:rust
npm run tauri:build
```

The NSIS installer is generated in `src-tauri/target/release/bundle/nsis`. Both `forged` and `forge-wallet-rpc` sidecars are bundled. XMRig is supplied by the user, not distributed by this project. For a portable folder, place the desktop executable alongside `forged.exe` and `forge-wallet-rpc.exe`.

## First use

1. Configure a trusted ForgeCoin node URL. For the bundled local node, the actual public peer `150.136.209.227:39480` is prefilled; start the node. The peer is exclusive so inherited Monero bootstrap nodes are not contacted. DNS checkpoints and automatic daemon update checks are disabled.
2. Create a wallet and write down its recovery phrase, or recover an existing wallet. A wallet password is required. Use restore height 0 if unknown.
3. Wait for node synchronization and wallet scanning. The balance screen shows wallet height and offline status; Settings shows node height and sync status. Wallet auto-scanning is enabled only while the node responds, so offline balance and recovery controls remain usable.
4. Solo mining uses the local daemon. Pool mining requires a ForgeCoin-compatible pool and a standard non-elevated XMRig executable. Pool login uses the primary wallet address and password `x`; pools requiring custom login formats are outside this minimal version.
5. Choose the correct TLS port advertised by the pool. CPU threads default to one. XMRig's normal donation policy applies. Read the miner log to confirm accepted shares; a running process alone does not establish a successful connection.

The public peer was recovered from the prior hosting conversation and its P2P port verified reachable on 2026-10-17. Its RPC port 39481 timed out, so the wallet defaults to local RPC `http://127.0.0.1:39481` while the bundled node syncs from the prefilled public peer. An empty saved peer is filled automatically; a nonempty custom peer is preserved. No pool is preconfigured. Existing wallet files and chain directories are not migrated. To import wallet files, close their existing wallet program and copy both the wallet cache and `.keys` file into the folder shown in Settings, using a simple alphanumeric/hyphen/underscore wallet name. Keep the original backup. Recovery is the other supported import path.

## Keys and processes

Wallet files live under `%LOCALAPPDATA%/com.forgecoin.desktop/wallets` and retain the wallet implementation's password encryption. The frontend does not store keys, passwords or phrases in browser storage. Recovery phrases exist transiently in UI memory and hide after 30 seconds, on navigation or window blur; this is not a guarantee against compromised software on the same machine.

Rust owns the child processes and exposes an allow-listed set of operations. Wallet RPC binds only to a random loopback port, requires Digest authentication, and uses the wallet binary's owner-restricted, delete-on-close credential file. The unauthenticated challenge contains no wallet secrets. Prepared transaction metadata remains in Rust until explicit confirmation and cannot be sent twice through the same review. Amounts cross IPC as decimal strings and are converted to atomic integers without floating point.

The app locks its data folder against concurrent instances, closes/stores the wallet on normal exit and stops its child processes. Force-killing the desktop may leave child processes running; close the application normally. Mining disables MSR modifications and CUDA/OpenCL. Pool monitoring uses XMRig’s read-only HTTP API on a random loopback port with a random authentication token; it is not exposed on the network. An explicit XMRig config prevents inheriting another installation's pools. Settings and miner configuration contain public addresses/endpoints, not wallet secrets.

## ForgeCoin prerequisite repaired

The local core source set `CRYPTONOTE_DISPLAY_DECIMAL_POINT` to 8, but its inherited decimal validation rejected 8 when reopening a wallet. `docs/forgecoin-8-decimal.patch` adds 8 to that validation and names the unit `forgecoin`. Apply it to a matching core checkout before rebuilding wallet sidecars. The repaired node and wallet RPC binaries are included here. No consensus rule was changed.

```bash
cmake --build build/MINGW64_NT-10.0-26300/forgecoin-dev/release --target wallet_rpc_server daemon -j 4
```

## Validation

Unit tests cover atomic precision above JavaScript's safe-integer range, malformed amounts and endpoint/path validation. Opt-in integration tests use new disposable wallets and an isolated offline chain, never existing wallets or public peers:

```powershell
$env:FORGE_TEST_XMRIG='C:\path\to\standard\xmrig.exe'
cargo test --manifest-path src-tauri/Cargo.toml --lib -- --include-ignored
```

The mining test verifies a v16 template and seed hash, Solo start/stop, an XMRig-accepted offline block, and a submitted/accepted Stratum share through the actual Pool-mode launcher using a loopback test fixture. The fixture is test-only and is not part of the shipped app's behavior. If `FORGE_TEST_XMRIG` is omitted, the XMRig portion is skipped.

Live public-pool TLS, production payouts and real-funds payment broadcast require a configured live environment and have not been tested. Account management, hardware wallets, multisig, integrated payment IDs, custom pool credentials and QR codes are not included in this minimal version.

References: [XMRig algorithms](https://xmrig.com/docs/algorithms), [XMRig pool configuration](https://xmrig.com/docs/miner/config/pool), [wallet RPC](https://www.getmonero.org/resources/developer-guides/wallet-rpc.html). The local ForgeCoin source and runtime tests are authoritative for this fork's precision and compatibility.





Version 0.1.3 adds independently saved CPU thread counts, Solo/pool log selection with a live toggle, live mining state and hashrate, and a saved-wallet dropdown. Thread changes apply at the next mining start. Wallet and mining integration tests cover reward scanning, live telemetry authentication, thread changes, wallet discovery, and log selection.

## Planned official-pool integration

The existing Solo mode and user-configured XMRig Pool mode are the starting point for the [pool delivery plan](../../docs/POOL_EXPLORER_IMPLEMENTATION_PLAN.md). Add a verified official native FRG pool profile only after deployment; retain independent-pool configuration and solo mining. Disclose the **1% operator fee** on eligible pooled rewards separately from network payout fees and XMRig donation policy. Solo mining has no project-pool operator fee.

Official-pool accepted-share/payout status, TLS/offline/full-pool handling and end-to-end two-miner mature-payout tests remain pending. The 100-worker target is not tested capacity. Pool website/dashboard, standalone Pool Observer and online explorer are separate planned services, not embedded or deployed features of this desktop. Security review and staged rollout are required before public integration.

See the [workstream handoff](../../docs/HANDOFF_POOL_EXPLORER_2026-10-24.md) for branch context, completed documentation work and the next desktop integration deliverable.

## Network cutover: 20261026

The application defaults to the new isolated mainnet P2P/RPC ports 39480/39481 and fresh local chain/wallet storage. Existing saved settings using 19480/19481 fail closed with instructions to change the connection explicitly. Old LMDB files and wallets are not migrated. The fresh mainnet is not yet live; never mine or transfer value until an approved genesis hash and binaries have been released.
