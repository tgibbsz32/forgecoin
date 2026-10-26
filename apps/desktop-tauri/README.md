# ForgeCoin Tauri desktop — prelaunch

[Current mainnet specification](../../docs/CURRENT_MAINNET.md) · [Project status](../../PROJECT_STATUS.md) · [Roadmap](../../ROADMAP.md)

The selected October 26 chain is frozen and unlaunched: nonce 20261026, P2P/RPC/ZMQ 39480/39481/39482, prefixes190/191/192. Main still contains the retired runtime; the retargeted desktop remains in draft #111 and the audited packaging update in draft #114. Do not package main and label it a matching new-mainnet release. No public bootstrap peer or pool is approved; do not use the retired Oracle peer.

## Build and evidence

Install frontend dependencies with `npm ci`, then `npm run build` for TypeScript/Vite checks. Native Tauri packaging requires matching manifest-pinned sidecars and reviewed dependency imports; never substitute old binaries to satisfy a build.

The isolated feature-branch review passed 14 mainnet/desktop source checks, 20 pool guards, matching binary SHA-256/import audit, Rust library compilation and exact-amount test, frontend build, and local debug NSIS construction. The debug installer was not installed, launched, signed or published. These results are not a clean-machine runtime or public-release pass.

## Release gates

Complete Tauri wallet create/restore and failure UX using separately authorized disposable tests, funded send/receive, genuine Solo and compatible Pool acceptance/maturity/payouts, clean-machine install/uninstall, security review, reproducible release builds and ARM64 agreement. Keep solo/pool mining locked until authorization. Historical mock Stratum acknowledgments do not prove valid native PoW or payouts. Never run wallet/mining integration tests against owner wallets or the frozen launch chain.

Windows Forms create/restore evidence is separate from Tauri acceptance. No recovery seed, private wallet, password or executable belongs in Git. [Current limitations](../../docs/CURRENT_MAINNET.md) include the unresolved genesis output permanent-unspendability gate.
