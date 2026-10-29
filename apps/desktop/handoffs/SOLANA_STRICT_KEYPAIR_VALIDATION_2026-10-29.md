# Solana Desktop Wallet — Canonical JSON Keypair Validation Handoff (2026-10-29)

## This phase
The existing Solana vault previously used `Convert.ToInt32` to parse 64 keypair JSON byte entries. That allowed potentially coercible values (including JSON strings or booleans) to be interpreted as key bytes. The parser now accepts only JSON integral runtime values and rejects other types before vault encryption or address display.

A standalone C# smoke test includes six negative fixtures (string, boolean, fractional, negative, out-of-range, wrong length). On the connected Windows machine, the .NET Framework compiler built the smoke test; **6/6 checks passed**. The complete desktop GUI source also **compiled** using the repo's .NET Framework C# compiler target. This is not an integration or security audit.

## Remaining critical security issue
The 64-byte Solana CLI private keypair contains 32 bytes of seed material and 32 bytes of public key. The current `AddressFromKeypair` verifies only that the provided trailing 32 bytes are byte-shaped, *not that they are the actual Ed25519 public key derived from the first 32 bytes*. Therefore, a syntactically valid but inconsistent keypair can still pass. Require independent Ed25519 public key derivation and comparison using a vetted library or carefully reviewed implementation, with positive and negative vectors, before any real funds or authority accounts use the app.

Replace the Solana CLI temporary plaintext keypair creation flow with in-memory generation and audited mnemonic derivation; do not invent 25-word Solana mnemonic compatibility. Validate seed recovery, backup restoration on a clean machine, crash cleanup, storage encryption and rotation with disposable wallets.

## Owner and launch gates
Owner intends to create native FRG and Solana wallets inside the desktop GUI, using locally encrypted software custody. Proposed wallet roles: native FRG wallet; Solana treasury; Solana mint authority; optional separate operations/fee payer. Freeze authority policy and fixed-supply mint authority revocation remain undecided. Neither mFRG issuance nor Oracle public mining is authorized. Never paste or upload private keys, seed phrases, passwords, or vault files to GitHub or ChatGPT.

## Next phase
Integrate vetted Ed25519 public derivation and offline 12/24-word BIP39 mnemonic generation/recovery into desktop application with reproducible test vectors, before wallet deployment and production release.
