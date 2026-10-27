# ForgeCoin desktop: Solana wallet development preview

**Status (October 27, 2026):** implementation in an isolated feature branch; NOT a public release, NOT audited, and NOT approved for handling funds.

This is a separate Solana DEVNET wallet in the Windows Forms ForgeCoin desktop application. It does not use the native FRG recovery phrase, native daemon, mainnet wallet files or mining infrastructure. The existing genesis-frozen native FRG test build remains unchanged.

## Features implemented in source

- Create new 12-word English BIP39 Solana mnemonic using the operating system's cryptographic RNG.
- Restore 12/15/18/21/24-word English BIP39 phrase with checksum validation.
- SLIP-0010 Ed25519 derivation, **m/44'/501'/0'/0'** (zero-based account 0).
- Separate vault files stored in %LOCALAPPDATA%\ForgeCoin\solana-devnet-v1\<name>.wallet.json, refusing to overwrite an existing name.
- Vault encryption with Argon2id (64 MiB, t=3, p=1) and AES-256-GCM, independently randomized salts/nonces, with the public address authenticated as additional data.
- Unlock checks password, tag, mnemonic and derived public address without returning the phrase to the GUI.
- Reveal recovery words only after password re-entry; the modal clears after at most 60 seconds. No clipboard export button.
- Export and import encrypted wallet-backup JSON. The password must also be preserved.
- Read public SOL balances and optional SPL balances for separately entered **devnet** mFRG and **devnet** USDC mint addresses.
- All network requests are public-address reads against https://api.devnet.solana.com.

**Not implemented:** sending SOL or SPL transfers, token mint deployment, USDC liquidity/sale execution, mainnet, hardware wallet support, NFTs, bridging or wallet integration with native FRG. These functions MUST NOT be represented as complete. There is no known official mFRG or USDC devnet mint prefilled in this preview.

## Build

The development build is Windows Forms (Program.cs and SolanaWalletTab.cs) with a local Rust helper (solana-wallet-helper/) that receives requests through process stdin. Passwords and recovery phrases are never passed via command-line arguments or HTTP.

Prerequisites: .NET Framework 4.x C# compiler; Rust cargo for building the helper; the *exact* approved frozen-mainnet FRG binaries to produce a full bundle. Run:

1. cargo test --manifest-path solana-wallet-helper/Cargo.toml
2. cargo build --locked --release --manifest-path solana-wallet-helper/Cargo.toml
3. Compile Program.cs **and** SolanaWalletTab.cs with existing C# framework references.
4. Run build.ps1 only with approved frozen-mainnet native executables; it checks pinned hashes and refuses stale/native mismatches.

The build script copies solana-wallet-helper.exe into its bin directory. A compiled GUI by itself is not a complete distributable wallet.

## Recovery and backup

1. Choose a new wallet name and a unique strong password of at least 12 characters; select Create.
2. Write the displayed 12 recovery words by hand on offline material, in order. Do not photograph, screenshot, email or message them.
3. Save a second encrypted copy with **Backup encrypted wallet**. Keep the password independently; the backup alone cannot unlock.
4. Use **Restore words** with a NEW wallet name and password to recreate the same public address, or **Import encrypted backup** followed by its original password.
5. Verify the resulting public address is exactly the same as the address recorded when the wallet was first created. If recovery does not reproduce the original address, **do not send assets**.

A BIP39 phrase created under a different account/derivation path or with a nonempty BIP39 passphrase can produce a different Solana address. This preview only supports the documented derivation path and empty BIP39 passphrase; it does not guarantee compatibility with every Solana wallet.

## Safety and scope

- Do not fund devnet wallets with real-value assets or treat devnet tokens as production assets.
- Rust packages have a Cargo.lock; third-party dependencies need a security audit and vulnerability review before a public wallet release.
- The helper is not code-signed; process, memory, file/ACL and GUI threat-model reviews are outstanding.
- The native FRG network remains release-locked and mining-disabled, regardless of this Solana development tab.
- The provisional mFRG allocation is **50 million** tokens total: **5 million reserved for potential USDC sale/trading** and **45 million reserved for later distribution**. Nothing has been minted. This independent token is not yet a backed wrapper or bridge instrument.
