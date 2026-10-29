# Solana BIP39 English Mnemonic Generation — 2026-10-29

## Completed
Added the standard 2,048-word English BIP39 word list from bitcoin/bips, entropy-to-mnemonic encoding, 12-word OS-CSPRNG generation, and checksum verification for valid 12/15/18/21/24-word lengths. Existing BIP39 mnemonic-to-seed helper from PR #162 remains separate.

On the connected Windows machine, the C# component compiled and passed a standard 128-bit-zero entropy reference phrase (`abandon` x11, `about`), rejected a changed checksum, and generated a phrase passing its checksum verification. All tests were performed using disposable test phrases.

## Important limitations
This component is NOT yet connected to the desktop app's Create Wallet or Restore Wallet controls and has not undergone independent security auditing. A BIP39 phrase is not a Solana keypair by itself: the supported derivation path and hardened Ed25519 derivation must be specified and verified against independent Solana reference vectors, including recovery to the exact same address. The current GUI Create Wallet still uses the Solana CLI temporary file implementation. The BIP39 wordlist's provenance, normalization cases and negative tests require expanded audit before production custody.

The owner intends encrypted desktop-created software wallets, no hardware wallet, with ForgeCoin 25-word seeds entirely separate from Solana BIP39 recovery phrases. Never place real seeds in issue trackers, source files, chat or logs.

## Next milestone
Implement deterministic mnemonic-to-Solana-keypair/address using an independently checked standard derivation path, test 12- and 24-word round trips, then integrate verified in-memory generator into GUI only after backup/recovery QA. No mint, Oracle mining or token sale activation.
