# Solana desktop wallet creation — keygen process safety handoff (2026-10-29)

## Change
The Windows Solana wallet creation path now kills a timed-out `solana-keygen` subprocess before cleaning the temporary keypair file and only saves the encrypted vault once plaintext keypair file deletion and temporary-directory removal have both succeeded. This reduces the chance that the app displays a successfully created wallet while a known plaintext key file remains after an ordinary cleanup failure.

## Still blocked for production
The current local official Solana CLI emits a mnemonic and writes a **temporary plaintext JSON private key**. Deleting it is not forensic erasure, cannot prevent malware/backup scanners/filesystem snapshots, and does not guarantee cleanup after a crash or power loss. This patch also starts stdout and stderr reads concurrently before waiting, so pipe buffering cannot indefinitely block the child while the timeout is enforced. A reviewed in-memory key generator and keypair/public-key derivation verification are required before considering this fit for mainnet custody. Existing vault cryptography uses AES-CBC/HMAC and PBKDF2; audit and recovery testing are mandatory.

## Wallet recovery model
Native ForgeCoin FRG wallets use a **25-word** seed, Solana normally uses its own BIP39 12/24-word seed and derivation procedure. They are separate wallets in one desktop application. No seed phrase, private key, or wallet password should be committed, uploaded, or transmitted.

## Test/release gate
Source changes alone do not establish compiled Windows build/test success. Run Windows compilation and both success/CLI-timeout/cleanup-failure desktop QA on an isolated disposable test wallet; verify encrypted backup/restore and address consistency. Keep Solana mainnet mint/sale and Oracle public mining disabled until separately approved after full launch acceptance tests.
