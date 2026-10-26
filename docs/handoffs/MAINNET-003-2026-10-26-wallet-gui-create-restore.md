# MAINNET-003 — Windows desktop wallet GUI lifecycle and reproducible prelaunch package

**2026-10-26 | Source: draft PR #111 | Classification: PRELAUNCH / no public mining.**

## Wallet GUI completion

The private Windows Forms frontend has completed its previously unfinished
**Restore** handler. It invokes the matching protected localhost
`forge-wallet-rpc` native `restore_deterministic_wallet` endpoint,
with a masked 25-word input, zero restore-height for the unlaunched mainnet,
a separate wallet filename and collision protection. It clears the recovery
input after use and does not print the recovery phrase in logs.

**Create** enforces at least a 12-character encryption password and refuses
existing files. The app opens the new wallet, displays its primary receiving
address, and exposes **Copy address** for the public value only. The earlier
mnemonic clipboard copy button was removed; the seed is displayed only for
offline backup. The UI has explicit mainnet PRELAUNCH labels; transaction
sending, solo mining and pool mining remain disabled. When operating offline,
the bundled daemon binds P2P on loopback, not a public interface.

New mainnet wallet, ring data and chain data remain isolated under
`%LOCALAPPDATA%\ForgeCoin\*-mainnet-20261026`; no old development wallets
were moved, modified, read or deleted.

## Real interactive Windows GUI test (pass)

A reproducible QA harness and PowerShell runner are checked in under
`apps/desktop/tests/GuiCreateRestoreSmoke.cs` and
`apps/desktop/tests/run-gui-create-restore-smoke.ps1`.

Test source first checks unused localhost RPC ports and a **genesis-only
offline** source data directory. It verifies the freshly built new-mainnet
daemon's exact genesis hash
`4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c`,
nonce `20261026`, mode `mainnet` and RPC height `1`.

Using actual **Windows Forms Create/Restore button handlers** and native
authenticated wallet RPC, the test:

1. Creates an encrypted, disposable synthetic wallet and sees the mnemonic
   backup dialog. Checks the 25-word seed in RAM only, never in output.
2. Reads the synthetic public receiving address from the GUI.
3. Closes the wallet and restores the same mnemonic into a *new* synthetic
   wallet filename via the GUI's masked recovery field.
4. Compares the two public receiving addresses byte-for-byte and confirms
   they match.
5. Closes both, stops the offline daemon, confirms chain height remained
   `1`, and deletes only four synthetic QA wallet files.
6. Never reads or modifies the user's separate real fee treasury wallet.

**Actual integration run passed twice** (first v0.3; second v0.4 with the
final UI and docs). All fourteen Python mainnet/desktop tests and twenty
C pool source guards passed; Windows desktop compiled after the changes.

The synthetic seed and real user's seed were never printed or disclosed.
A true owner-side interactive restore is still recommended before taking
custody of valuable FRG, and public transfer/mining tests have not passed.

## Private owner package — v0.4

`%USERPROFILE%\Downloads\ForgeCoin-Mainnet-20261026-Prelaunch-Wallet-v0.4.zip`

- SHA-256: `4029E26A571FCA84C4BAFABEE0396F8E392BE21433426CD5AC95237A5CBB6E12`
- Size: 46,197,707 bytes.
- GUI binary SHA-256:
  `E542F8C1EE9F9CFE4346D9BB4F3311AE758233500AAEE42CA14AF569B4A1014B`.
- Includes the three manifest-hash-pinned fresh mainnet native EXEs,
  required MinGW DLLs, network identity manifest, owner treasury guidance,
  accurate installation/readme and validation notes.
- Explicitly **does not bundle XMRig**, open a Stratum listener, issue a
  new Solana token, or mine block 1. It was saved to the owner's Windows
  Downloads folder, **not uploaded as a public release**.
- v0.1–v0.3 private wallet bundles are superseded for further testing.

## Required release gates not completed by this work

- Demonstrate **real accepted solo blocks and maturity** and **native
  accepted/rejected shares, accounting and payouts through compatible pool
  software** on a genuinely distinct disposable mining chain.
- Supply a reviewed, legally distributable pool-miner backend (including
  proper upstream licensing and source) and a full signed/verified installer.
- Independently prove that the 11.92092895 FRG genesis output is permanently
  unspendable, or apply and audit a consensus-level rule.
- Build and compare matching ARM64/Windows native genesis and height-16+
  consensus vectors, run cross-platform wallet synchronization.
- Bring up an authorized public node/explorer/pool with real peer discovery,
  safe hot-wallet custody, deterministic recovery/reorg/payout audits,
  monitored deployment and operator launch approval.

No production mining, real payouts, user wallet seeds or public network
activation were performed.
