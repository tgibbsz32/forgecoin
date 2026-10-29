# Solana mnemonic-to-address derivation handoff — 2026-10-29

Added standalone C# SLIP-0010 hardened Ed25519 key derivation from BIP39 seeds for the explicit path m/44'/501'/0'/0'. The 12-word BIP39 example 'abandon' x11 + 'about' (empty BIP39 passphrase) derives to Ed25519 public key hex `f036276246a75b9de3349ed42b15e232f6518fc20f5fcd4f1d64e81f9bd258f7`. This result was cross-checked independently using Python hashlib/HMAC plus the cryptography Ed25519 implementation, and pinned as a C# regression vector.

On the connected Windows machine, the original standalone tests compiled and passed repeatability and account separation. The final fixed-vector test must be rerun after the commit. The existing GUI is unchanged; importing or creating production wallets remains blocked.

Caveats: Solana tools use multiple mnemonic derivation conventions, and the reference here covers only the exact hardened path stated. Supporting old Solana CLI mnemonic recovery and other wallet styles requires explicit derivation-path selection and independent parity testing. The component presently returns a private seed as bytes to its caller; future integration must restrict exposure, clear buffers, and avoid plaintext storage. Complete actual create/restore GUI workflow, 12/24-word recovery vectors, vault backup restore on a clean computer, signed transaction acceptance, library provenance, and independent cryptographic review before mint-authority custody.

No private owner keys, wallet funds, mFRG issuance, Oracle mainnet activation or public sale involved.
