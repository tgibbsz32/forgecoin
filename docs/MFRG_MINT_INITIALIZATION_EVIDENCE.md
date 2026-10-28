# mFRG Step 15 — Solana mint initialization evidence checklist

**October 28, 2026 · OFFLINE-ONLY verification code · NO minting or sale authorized**

As of this step, the repo contains **no independently authenticated real mFRG Solana mainnet mint address, creation/initialization transaction signature or authenticated mainnet signer/treasury inventory**. The previously known devnet test mint is not a valid mainnet identifier. An unconfigured desktop planning file does not establish absence of an on-chain mint. This is a procedure to collect and check **read-only** evidence.

For operator-invoked **read-only HTTPS queries** that verify two RPC endpoints report the expected Solana mainnet genesis before comparing the existing mint and initialization transaction, see [Step 16 live mainnet provenance preflight](MFRG_LIVE_MAINNET_PROVENANCE.md). This does not prove legal issuer identity or authorize any token transaction.

## Verification tool

The new [mint initialization evidence parser](../tools/verify_mfrg_mint_initialization.py) compares **two separately saved `getTransaction` results** with a saved `getAccountInfo` mint-account snapshot, all in Solana RPC `jsonParsed` representation. It requires the same expected mint and 64-byte base58 signature in both transaction responses, successful transaction metadata, a writable mint account key and exactly one original SPL Token Program `initializeMint` or `initializeMint2` parsed instruction with **six decimals**. It accepts outer and decoded inner instructions and checks identical transaction slot, initialization authority, program and mint across the two results. The later mint account must be the standard SPL Token Program and observed at a slot **at least as new** as the initializing transaction.

This is **not a cryptographic signature verifier or trusted chain reader**. A `jsonParsed` response contains a signature string and decoded instructions but not a cryptographically authenticated transaction by itself. Two hostnames and two JSON files are not proof of independent providers; even identical files could be copies. The tool does not demand different bytes because the same immutable transaction response may legitimately be identical across providers. It always returns:

- `initialized_mint_on_mainnet_authenticated=false`
- `independent_rpc_provenance_verified=false`
- `transaction_signature_cryptographically_verified=false`
- `project_issuer_identity_verified=false`
- `mint_and_holder_custody_verified=false`
- `sale_or_issuance_authorized=false`

**The initialization instruction does not by itself establish creation of a treasury, ownership by ForgeCoin, current beneficial custody or public distribution.** The mint authority recorded at initialization can differ from the current mint authority if it was subsequently changed or revoked. If the current mint authority is null, do not assume the token can be increased to 500M.

## Obtain the actual Solana mainnet evidence

First obtain the real mint public key and a verifiable transaction signature from the issuer's original authorized deployment record, wallet transaction list, transaction link or project-owned signed record. Do not search by ticker and assume the resulting token is genuine. Record the authorized operator responsible for the asset and independently verify source/provider network.

Example **read-only** PowerShell commands; replace placeholders. An RPC may not retain full historical transactions, so `result:null` is **not proof that a mint never existed**.

```powershell
$mint = "REPLACE_WITH_OWNER_VERIFIED_MAINNET_MFRG_MINT"
$signature = "REPLACE_WITH_REAL_MINT_INITIALIZATION_TRANSACTION_SIGNATURE"
$rpc1 = "https://api.mainnet-beta.solana.com"
$rpc2 = "https://YOUR_INDEPENDENT_SOLANA_MAINNET_RPC_PROVIDER"

$txBody = @{
  jsonrpc = "2.0"; id = $signature; method = "getTransaction"
  params = @($signature, @{encoding="jsonParsed"; commitment="finalized"; maxSupportedTransactionVersion=0})
} | ConvertTo-Json -Depth 10

(Invoke-RestMethod -Uri $rpc1 -Method Post -ContentType "application/json" -Body $txBody) |
  ConvertTo-Json -Depth 50 | Set-Content -Encoding utf8 ".\mfrg-init-one.json"
(Invoke-RestMethod -Uri $rpc2 -Method Post -ContentType "application/json" -Body $txBody) |
  ConvertTo-Json -Depth 50 | Set-Content -Encoding utf8 ".\mfrg-init-two.json"

$mintBody = @{
  jsonrpc = "2.0"; id = $mint; method = "getAccountInfo"
  params = @($mint, @{encoding="jsonParsed"; commitment="finalized"})
} | ConvertTo-Json -Depth 10

(Invoke-RestMethod -Uri $rpc1 -Method Post -ContentType "application/json" -Body $mintBody) |
  ConvertTo-Json -Depth 50 | Set-Content -Encoding utf8 ".\mfrg-mint-account.json"

python tools/verify_mfrg_mint_initialization.py `
  --mint $mint --signature $signature `
  --first-transaction ".\mfrg-init-one.json" `
  --second-transaction ".\mfrg-init-two.json" `
  --mint-json ".\mfrg-mint-account.json" `
  --first-origin "https://api.mainnet-beta.solana.com" `
  --second-origin "https://YOUR_INDEPENDENT_SOLANA_MAINNET_RPC_PROVIDER"
```

The hostname flags should be clean HTTPS origins without private API-key paths or query strings; they remain *unverified labels*. Preserve raw RPC captures privately with actual UTC observation time, provider and finalized slot. Never submit wallet recovery phrases, private keys, provider API keys or transaction-signing requests to these tools.

## Policy remains a proposal until live evidence exists

- Intended **500M mFRG** at six decimals; the actual mint supply is not independently verified.
- Nine planned allocations: 50M lifetime fundraising (still **5M first-pilot ceiling**), 100M operations, 100M ecosystem, 85M finite staking incentives, 60M liquidity, 65M engineering/security, 15M unrestricted founder (at actual distribution), 15M team-labeled **same-founder-beneficial** deferred and 10M emergency.
- Founder total **30M / 6%**, with 625,000 mFRG monthly unlocks at ends of months 13–36 for the deferred 15M, **not deployed**.
- No treasury signers, holder ownership, multisig/PDA derivation, legal authority, sale, checkout, staking, liquidity or active vesting is verified by this tool.
- Native FRG RandomX consensus and emission remain separate and unchanged.

Run synthetic verification:

```sh
python3 tools/test_verify_mfrg_mint_initialization.py
python3 tools/test_reconcile_mfrg_mint_snapshots.py
python3 tools/test_verify_mfrg_multisig_pda.py
python3 tools/test_mfrg_policy.py
```

**Next evidence gate:** Independently confirm both RPC providers' actual mainnet provenance, the genuine original initialization transaction, owner authorization, current mint/freeze authorities, current holder inventory, and signer/beneficial custody. Do not deploy vaults or collect USDC/SOL until approved security/legal reviews and authentic proof are complete.

**References:** [Solana RPC getTransaction](https://solana.com/docs/rpc/http/gettransaction), [parsed JSON structures](https://solana.com/docs/rpc/json-structures), and [Step 14 custody safeguards](MFRG_MULTISIG_PDA_READINESS.md).
