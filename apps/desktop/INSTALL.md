# ForgeCoin Windows wallet — prelaunch installation and recovery

**Current status:** private wallet testing only, NOT an authorized public mainnet/miner release. No miner or pool payouts are enabled in this package. Native genesis nonce `20261026`; expected genesis hash `4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c`.

## Installation

1. Extract the entire **verified owner test ZIP** into a new folder. Keep `ForgeCoin Desktop.exe` next to the `bin` directory. Do not use older v0.1 or v0.2 test packages for custody.
2. Confirm `mainnet.identity.json` specifies the expected genesis nonce/hash and `release_authorized=false`. Verify the release ZIP hash against the owner-verified SHA-256, not an untrusted message.
3. Open the desktop application. If Windows security flags the unsigned executable, investigate its provenance and hash; **do not automatically bypass security prompts**.
4. The Node tab can inspect an offline, genesis-only chain; offline mode must not mine or connect a public P2P port. The daemon RPC is loopback-only at `127.0.0.1:39481`; wallet RPC at `127.0.0.1:39483` requires randomly generated HTTP Digest credentials.
5. Existing development-chain blockchain databases, wallets and transaction balances are **not imported or merged**. Back them up separately.

## Create and protect a wallet

1. Open the **Wallet** tab, select a new wallet name and enter a unique encryption password of at least 12 characters.
2. Click **Create**. The native wallet RPC creates the files in `%LOCALAPPDATA%\ForgeCoin\wallets-mainnet-20261026`.
3. The GUI displays a **25-word recovery phrase**. Write the phrase in correct order on offline media and store it securely. Do not photograph, copy to clipboard, upload or transmit it.
4. Record the public address on the Wallet tab. Use **Copy address** to copy ONLY that public address. Verify its beginning and ending characters against the wallet display.
5. Click **Close wallet**, then use **Open** with the same name and password to confirm that the encrypted wallet files load normally.

## Independently verify recovery BEFORE funding

1. Record your public address and close the current wallet.
2. Choose a **new filename** (for example `treasury-recovery-test`), set a new encryption password, then click **Restore**.
3. Enter your 25 offline recovery words in order. Entry is masked and sent only to the locally authenticated wallet service. The words are cleared from the input after the restore attempt.
4. Verify that the new wallet displays **exactly the same public address** as the original. Your original wallet files remain untouched. Keep the encrypted original and recovery backups separately.
5. Reopen the original wallet when finished. Do not send the recovery phrase to the team, the pool server, an assistant, or anyone else.

An automated interactive Windows Forms test successfully created a disposable wallet, displayed its recovery dialog, closed and restored it into a second wallet file, verified the public address match, and deleted only the disposable test files. This is **not** an independent security audit or a test involving real funds.

## Treasury and pool

The owner-controlled **1% pool operator fee treasury** is separate from the pool reward/payout hot wallet and any proposed future governance treasury. The pool may require only the PUBLIC receiving address to account for operator fees. It must never receive the treasury mnemonic/password/private keys. Payout distribution remains disabled pending production safety review and a distinct pool reward wallet.

## Mining and networking

- Native RandomX SOLO and XMRig-compatible POOL source controls are present but intentionally **locked** in this genesis-frozen prelaunch package.
- No publicly authorized mining, Stratum endpoint, fee collection, block template submission or transfer is permitted at this phase. A GUI button or local test is not evidence of a live network.
- The official mining package must eventually include a verified, legally distributable pool-miner implementation and successfully pass accepted-share/payout and solo block-maturity tests on a **separate disposable network**, not on the frozen public launch genesis.
- Node P2P `39480`, daemon RPC `39481`, wallet RPC `39483`. Never expose wallet RPC or unrestricted daemon RPC to the internet.

## Backups and removal

Preserve `%LOCALAPPDATA%\ForgeCoin\wallets-mainnet-20261026`, your offline seed phrase, and (where relevant) your private wallet password. Never delete `%LOCALAPPDATA%\ForgeCoin` during a simple application uninstall because it may contain valuable encrypted wallets or historical backups.

Read [technical validation](VALIDATION.md), [treasury setup](TREASURY-WALLET.md), and the [new-mainnet cutover gates](../../docs/MAINNET_CUTOVER_RELEASE_GATES_2026-10-26.md).
