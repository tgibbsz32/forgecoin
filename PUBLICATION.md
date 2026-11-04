# ForgeCoin source publication and binary release controls

**Updated November 4, 2026. Native FRG mainnet is frozen and NOT authorized
for public mining, wallet spending, production pool payouts or public binary
distribution.** See [release readiness](docs/RELEASE_READINESS_2026-11-04.md),
[network identity](docs/CURRENT_MAINNET.md), and [project status](PROJECT_STATUS.md).

## Public GitHub source repository

Keep public source, docs, license files, dependency lockfiles, logos and
explicitly approved **nonsecret** test vectors in Git. This repository retains
existing history and the recovered Phase 3 source; see
[recovery provenance](docs/SOURCE_RECOVERY.md). Do not commit or upload:

- Wallet files, wallet .keys, mnemonic/seed phrases, view/spend keys, recovery
  backups, passwords, real user addresses linked to private records or CI
  secrets. Two inherited, explicitly known **public test-only fixtures** may
  remain solely as historical test fixtures; never infer a generic .keys
  exception for new content.
- Build caches, generated binaries, developer machine paths/credentials,
  anonymous telemetry containing private identity, or copied signed private
  packages. Sensitive security findings must follow [SECURITY.md](SECURITY.md).

Never publish experimental node/Stratum ports, fixed-difficulty test flags,
wallet RPC or unreviewed APKs as active FRG mainnet services.

## Exact release gates by asset type

| Asset | Current distribution | Mandatory approval before an official release |
| --- | --- | --- |
| Windows Forms EXE / installer | **Not authorized**; source-only compile and private candidate test bundles exist | Reviewed frozen native sidecars, proven funded wallet create/restore/send, accepted solo and pool mining, clean-machine install, signed reproducible artifact, license and SHA-256 |
| Tauri Windows installer | **Not authorized**; prior local debug installer only | Same native consensus sidecars, reviewed RPC/key custody, runtime/restore/mining acceptance, clean install/uninstall, signed distribution |
| Android APK | **Not authorized**; debug-only UI preview contains no native FRG wallet/miner | Real ARM64 native daemon/miner/wallet, Keystore-authenticated custody and restore, foreground/thermal/battery policy, physical-device acceptance, release signing and provenance |
| Native daemon / mining pool | **Not authorized for network activation** | Approved consensus/genesis-spend policy, independently operated peer verification, payout journal/signer idempotence and reorg safety, audited Oracle/network/firewall and monitoring |
| Pool dashboard/explorer/API | Static prelaunch pages only | Verified canonical-chain identity, HTTPS-only read endpoints, freshness and privacy guards, tested backend, accurately marked unavailable data |
| Solana mFRG / bridge / game utility | Planned, **no mint or sale authorization** | Separate governance, legal/custody/supply review and independently verified 1:1 native backing of any redeemable token |

## Before tagging a downloadable release

1. Freeze one independently reviewed source commit; resolve full signed native
   genesis-output rejection, peer consensus and wallet/pool payout tests.
2. Rebuild from that commit on a clean documented toolchain; independently
   verify target ABI, binary imports and licensed third-party dependencies.
   Hash-pinning historical candidate EXEs is **not** a source audit.
3. Validate clean Windows/Android installs, seed recovery on disposable test
   wallets, solo and pool work, wallet receipt, restart, UI errors, accessibility,
   and mining thermal/battery handling. Use physical Android ARM64 hardware.
4. Produce a signed installer/APK and separate downloadable SHA-256 manifest,
   builder provenance, changelog, source reference, licenses and known
   limitations. Require explicit owner authorization for each released asset.
5. Only then publish versioned GitHub Releases, update homepage/download links,
   launch services under separately approved operations, and test public
   download integrity. **No release asset should be published merely because
   a draft branch has green CI.**

Public miners' read-only stats may be looked up by their **public FRG payout
address without registration**, but the live API must remain disconnected until
independently verified. Knowing an address grants no ability to change payouts,
spend funds, or view nonpublic account records.

This publication document is not a launch approval or request to unlock any
network control.
