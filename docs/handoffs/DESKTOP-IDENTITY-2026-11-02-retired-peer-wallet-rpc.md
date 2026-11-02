# Desktop network identity and wallet-RPC port isolation — November 2, 2026

**Status:** Independent desktop safety integration against current GitHub `main`; not a public-ready binary or authorized mainnet release.

## Incident addressed

A full-tree audit identified launch-facing stale endpoints:
- The Tauri Windows desktop defaulted to local daemon `127.0.0.1:19481`, the old Oracle peer `150.136.209.227:19480`, and spawned P2P port `19480`, daemon RPC port `19481`. Those ports belong to the retired network. A Tauri startup fallback even reintroduced the old peer when the saved peer was blank.
- Windows Forms correctly uses selected native P2P/RPC `39480/39481`, but 15 wallet-RPC call/bind sites still used retired port `19482`.
- Windows Forms launch documentation erroneously said its wallet RPC uses `39483`. The same GUI already assigns `39483` to XMRig's local statistics endpoint, so reusing that for wallet RPC would create a local port collision.

## Changes

- Windows Forms wallet RPC uses `127.0.0.1:39484` consistently for bind, create/open/close/recovery/address/balance/transfer requests. Local XMRig statistics API **retains 127.0.0.1:39483**. Native P2P remains `39480`, native daemon HTTP RPC remains `39481`, native ZMQ RPC remains `39482`. Wallet RPC is a **separate** process/port and must never bind externally.
- Windows Forms P2P listener defaults to `127.0.0.1:39480` for a private desktop node rather than `0.0.0.0`. Public node operations should use explicitly administered Oracle infrastructure, not an implicitly exposed desktop listener.
- Tauri defaults now use `http://127.0.0.1:39481` with an **empty peer**. The application refuses to start the node until the user provides an explicitly trusted peer; **no production/bootstrap P2P peer has been authorized yet**.
- Tauri node launch uses P2P loopback `39480` and local daemon RPC `39481`. `validate_settings` rejects old peer port `19480` and daemon RPC port `19481`.
- Previously saved Tauri settings migrate away from any peer ending in `:19480` (clearing it), and from a retired loopback daemon URL `http://127.0.0.1:19481` (updating to `39481`). Migrated settings are saved; users must explicitly choose a trusted 39480 peer. Other saved wallet settings are preserved.
- User-facing desktop text and Windows Forms installation documents now reflect the selected ports and no approved prelaunch peer.

## Verification

- Four dedicated source regression checks in `tests/desktop/test_endpoints.py` passed locally, confirming no port overlap, explicit Tauri peer selection, saved-settings migration, and docs.
- Windows Forms native .NET Framework C# compiler compiled the adjusted source successfully into a **temporary** executable that was deleted; no release package was published.
- Tauri TypeScript/Vite frontend production build completed successfully with `npm ci` and `npm run build`.
- Tauri Rust backend `cargo check --locked --offline` reached its intentional build.rs review gate and **stopped** because the vetted `forged-x86_64-pc-windows-msvc.exe` sidecar is missing. This is an expected prelaunch release blocker; **do not bypass it or silently substitute the retired binary**. A complete Rust packaging build is NOT yet verified.
- An independent workflow `.github/workflows/desktop-frozen-mainnet-endpoints.yml` runs source/TypeScript CI and Windows Forms compilation on GitHub. CI results must be observed separately.

## Required before public Windows release

Reconcile the desktop integration with draft packaging PR #114 and selected mainnet consensus PR #185. Build/sign/fingerprint freshly reviewed native sidecars using the frozen genesis and consensus, then complete Rust backend compile, wallet restoration, solo and pool acceptance, safe local RPC binding, proper shutdown, and installer/upgrade acceptance. Do not label older testing binaries as an approved October 26 public-mainnet release.

This desktop branch does **not** deploy Oracle, open public mining/Stratum, or authorize payouts. User's first solo-mined public block remains reserved for the eventual verified launch.
