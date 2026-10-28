# miniFORGE (mFRG) — read-only LIVE Solana mainnet provenance preflight

**Step 16 · October 28, 2026 · opt-in network reads ONLY · no token transactions.**

There is **still no independently authenticated existing mFRG Solana mainnet mint address or mint-creation transaction signature in the ForgeCoin repository**. The 500M mFRG policy does not prove minting. Do not substitute the historical devnet test mint or select a token based only on its ticker/name.

## What this adds over offline-only Steps 9–15

The [read-only mainnet provenance checker](../tools/read_mfrg_mainnet_provenance.py) is an operator-invoked Python command using standard-library HTTPS with certificate hostname validation. Given **two independent HTTPS RPC provider origins** and **the real owner-sourced existing mainnet mint public key + initialization transaction signature**, it makes just **six JSON-RPC requests**:

1. `getGenesisHash` on RPC provider A. Stop unless it reports the known Solana Mainnet Beta genesis `5eykt4UsFv8P8NJdTREpY1vzqKqZKvdpKuc147dw2N9d`.
2. `getAccountInfo` on A with `encoding=jsonParsed`, `commitment=finalized`; check standard SPL token mint type, six decimals, current supply (up to intended 500M), mint/freeze authorities.
3. `getTransaction` on A for the existing initialization transaction, `encoding=jsonParsed`, `commitment=finalized`, `maxSupportedTransactionVersion=0`, checking parsed successful `initializeMint` or `initializeMint2` evidence.
4. Repeat the same three **read-only** calls for provider B, require the same mainnet genesis and cross-check mint supply/authorities and initialization transaction details against provider A.

The code **does not** call `sendTransaction`, `requestAirdrop`, a mint-instruction builder, wallet signing, freeze/revoke authority or any other state-changing RPC. It also does not save response files or accept a signing key. It does not follow HTTP redirects, requires direct public HTTPS hostname origins (no embedded credentials or private paths), uses a 12-second per-call timeout and limits responses to 2 MB.

For convenience the CLI requires no Python packages outside the standard library and the existing project utilities.

### Operator example (not runnable without authentic existing mint data)

```powershell
python tools/read_mfrg_mainnet_provenance.py `
  --mint "ACTUAL_VERIFIED_EXISTING_MAINNET_MFRG_MINT_ADDRESS" `
  --signature "ACTUAL_INITIALIZE_MINT_TRANSACTION_SIGNATURE" `
  --rpc-one "https://api.mainnet-beta.solana.com" `
  --rpc-two "https://INDEPENDENT_PUBLIC_MAINNET_RPC_HOST"
```

Use two **actually independent** trusted providers, not simply two aliases for one backend. This example intentionally contains placeholders. Do not replace them with made-up public keys, old devnet tokens, another issuer's ticker-matching mint, a seed phrase or wallet secret. Some public Solana RPC providers do not retain sufficiently old transaction history or limit requests; a `getTransaction` error is *not* proof that the mint does not exist. Obtain approved archive/history RPC if required.

### What a passing result does and does not prove

The checker may report the **network's known genesis hash was returned over two TLS connections to operator-specified hostnames**, matching raw supply, consistent mint authority and freeze authority, and consistent parsed initialization transaction details. This is stronger than trusting locally saved copies of arbitrary RPC results, but it is **not cryptographic validation of Solana consensus or the transaction signature**. A faulty or malicious RPC can still forge replies. Two different hostnames do not prove two independently operated validators.

The output always states:
- `cryptographic_transaction_signature_verified=false`
- `operator_provider_independence_proven=false`
- `project_issuer_and_beneficial_owner_verified=false`
- `treasury_custody_or_funding_verified=false`
- `sale_or_issuance_authorized=false`

**The code's successful preflight must never activate any wallet, checkout, presale, staking, LP or minting state.** It does not establish the actual project owner, signer authority, current circulating supply or nine funded treasury accounts. Independently corroborate the creation signature in a trustworthy Solana mainnet explorer and compare the current mint/account holdings with the previous Steps 11–14 procedures before any proposed custody deployment.

### Constraints from existing mFRG policy

Intended maximum: **500M mFRG** at six decimals (not verified issuance). Nine mutually exclusive budget allocations: 50M fundraising **lifetime** (initial pilot max **5M**, still disabled); 100M operations; 100M ecosystem; 85M finite rewards; 60M liquidity; 65M engineering/security; 15M founder unrestricted at valid launch; 15M team-labeled but beneficially owned by the same founder, vesting 625,000 per calendar month at ends of months 13–36; 10M emergency. Founder total beneficial allocation **30M / 6%**. Do not represent the deferred 3% as independently employee-owned or locked on-chain before a real audited vesting escrow is funded.

No on-chain action is currently authorized. Native FRG RandomX consensus and tail emission remain separate and unchanged.

## Testing

GitHub CI uses **synthetic injected RPC responses**, not production Solana calls. Run:

```sh
python3 tools/test_read_mfrg_mainnet_provenance.py
python3 tools/test_verify_mfrg_mint_initialization.py
python3 tools/test_verify_mfrg_multisig_pda.py
python3 tools/test_mfrg_policy.py
```

**NEXT:** Obtain genuine owner-approved Solana mFRG mainnet mint public key and creation transaction signature, then perform the *read-only* live check. Until the owner provides independently verifiable identifiers, the live readiness gate must remain blocked; do not claim mFRG has been issued or is absent. Do not collect wallet recovery data.

**Technical references:** [Solana `getGenesisHash`](https://solana.com/docs/rpc/http/getgenesishash); [Solana mainnet genesis identifier](https://github.com/solana-labs/solana/blob/master/sdk/src/genesis_config.rs); [Solana `getTransaction`](https://solana.com/docs/rpc/http/gettransaction).
