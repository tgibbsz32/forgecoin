# ForgeCoin Desktop — Solana BIP39 seed derivation test handoff

Introduces a **separate, non-GUI** C# PBKDF2-HMAC-SHA512 2048-iteration 64-byte seed derivation helper using UTF-8 NFKD normalization, with a reference BIP39 test vector. The first official test vector is the mnemonic `abandon` repeated eleven times then `about`, passphrase `TREZOR`, expected seed beginning `c55257`; the full expected seed appears in the source test. Source: https://github.com/trezor/python-mnemonic/blob/master/vectors.json and BIP39: https://github.com/bitcoin/bips/blob/master/bip-0039.mediawiki.

No mnemonic is generated or validated against the 2048-word list and checksum. A BIP39 seed is **not yet** a Solana keypair: the wallet path and hardened Ed25519 derivation need separately verified implementation and vectors. Neither the main GUI Create Wallet action nor the existing encrypted vault format is modified by this phase. Do not present this as recoverable owner wallet functionality.

## Release gates
Run the supplied test on Windows with the .NET Framework C# compiler; check official test vector match, invalid input, normalization, passphrase distinctions and independent Solana address derivation. The Windows remote device was not reachable during initial preparation, so a merge must wait for confirmed compilation/test evidence. Next: vetted BIP39 wordlist generation/checksum and Solana-compatible derivation, recover original public address from mnemonic, test fresh-device recovery and encrypted-vault backup.
