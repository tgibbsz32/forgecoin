# ForgeCoin Windows mining release activation — prelaunch design

**As of October 27, 2026, the actual Windows application is intentionally MINING-LOCKED.** The QA zip is not the mainnet public release. This file documents implementation and remaining release controls.

## Gates implemented in source

Both Windows mining entrypoints now call the actual mining functions only if all package checks pass:

1. A **reviewed, recompiled** release must explicitly change the source-level `BuildPermitsPublicMining` flag to true. It is **false** in current QA source and binary. Editing JSON alone cannot unlock the QA mining buttons.
2. Bundled `mainnet.identity.json` must say `release_authorized: true`, `stage: released`, `chain: forgecoin-mainnet`, nonce `20261026` and exact genesis hash `4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c`.
3. Mining consensus must retain RandomX, 120-second blocks, difficulty 500,000 initial and 400,000 floor, precision eight decimals, pool fee `0.01`, and native ports.
4. Release manifest must contain an explicit `windows_release_binaries_sha256` map for all three executable names (`forged.exe`, `forge-wallet-rpc.exe`, `forge-wallet-cli.exe`) and those files must match SHA-256 exactly. The current frozen manifest has only separate PRELAUNCH hashes, so it cannot accidentally pass this gate.
5. Solo start rechecks the running local daemon's live `get_info` network type and `get_block_header_by_height(0)`: exact genesis nonce, hash and height are mandatory before it calls `start_mining`.
6. Pool start remains separately gated and requires a verified packaged XMRig executable. Production release must also verify the XMRig source/archive SHA256 and included GPLv3 notices, official pool endpoint and no donation misconfiguration.

The application is NOT cryptographically signed solely by this scheme. A reviewed release pipeline must independently sign the distributed EXE/ZIP and hash manifest, document Windows publisher identity, and verify download provenance. The in-app gate is a defense-in-depth prelaunch safeguard, not a substitute for audited distribution.

## Tests executed

- Current source `BuildPermitsPublicMining=false` compiled successfully to Windows WinForms.
- GUI reflection smoke: `startMiningButton.Enabled=False` and `startPoolButton.Enabled=False`. Eight Solana buttons and five fields also disabled.
- `apps/desktop/tests/test_release_gate.ps1` creates temporary text-only **FAKE .exe fixtures** (never executed) and temporary test-build variants: the unmodified QA source stays locked even with release JSON; a temporary source-modified test variant unlocks only with exact manifest/hash; tampering with binary hash or genesis locks it again. The test cleans its own fixtures and NEVER mines.
- Full v0.6 QA package rebuilt successfully using frozen SHA-pinned Windows native prelaunch executables, and stored privately on the owner's PC:
  `C:\Users\tgibb\Downloads\ForgeCoin-Windows-Prelaunch-QA-v0.6-20261027.zip`.

## Still required before actual GitHub release

- Independently verified Windows native wallet backup/restore, full-node sync with Oracle, first user-controlled solo block and recovered FRG outputs.
- Valid public Stratum pool work and independently reviewed mature, reorg-safe, idempotent payout and operator-fee settlement.
- Actual reviewed mainnet production authorization and source-level release flag change, plus a NEW pinned release manifest and release build pipeline rather than reusing the locked prelaunch build script.
- Real XMRig Windows miner packaging with pinned upstream source/license, detailed get-started instructions and verified signed GitHub Releases assets.
- Android QA remains a read-only signed *debug* preview without native mining/wallet functions. The Android public APK requires a separate complete build and security review.

Do NOT upload current prelaunch QA binary as a functional mining wallet or instruct users to rely on it for real funds.
