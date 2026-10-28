# mFRG — Step 12 read-only token-account inventory

**October 28, 2026. No verified mainnet mint, token transfers, account funding, sale or issuance authorized.**

The [Step 9 mint identity procedure](MFRG_SOLANA_MINT_VERIFICATION.md) and [Step 11 two-source mint procedure](MFRG_DUAL_SOURCE_MINT_VERIFICATION.md) are prerequisites. The genuine mFRG mainnet mint address has **not** been independently authenticated in the repository. Do not substitute the devnet mint or select a token by name.

## New offline validator

The [inventory validator](../tools/reconcile_mfrg_token_accounts.py) reads a saved Solana `getAccountInfo(jsonParsed)` mint response plus two saved `getProgramAccounts` responses. It performs **no RPC calls** and no signing. Both account responses must use `withContext:true`, `encoding:jsonParsed`, the original SPL Token Program, accounts of **165 bytes**, and the mint filter at byte offset zero.

It compares token-account public keys, amounts, owner authorities, delegates, freeze state, and close authorities. It rejects duplicates, mismatched programs/mints, malformed amounts, missing nonzero accounts, supply mismatches, authority conflicts, excessive slot gaps and overflow. Delegated balances are counted **once** in the token account, not again under the delegate.

The sum of listed account balances must equal the **observed mint supply** in the supplied mint snapshot (not necessarily the 500M target). This **cannot prove completeness**: filters, source identities and responses can be forged. All output explicitly reports `rpc_provenance_authenticated=false`, `scan_filter_and_completeness_proven=false`, `live_chain_state_verified=false`, `beneficial_owner_or_treasury_identity_proven=false` and `sale_or_issuance_authorized=false`.

## Read-only PowerShell commands

First independently confirm the mainnet mFRG mint address against the owner's real mint-creation transaction and trusted independent RPC/explorer evidence. Replace the placeholders. Public RPC services may restrict large `getProgramAccounts` queries; failure is **not** evidence of zero holders.

```powershell
$mint = "REPLACE_WITH_OWNER_VERIFIED_MAINNET_MFRG_MINT"
$rpc1 = "https://api.mainnet-beta.solana.com"
$rpc2 = "https://INDEPENDENT_SOLANA_MAINNET_RPC_PROVIDER"
$mintQuery = @{jsonrpc="2.0"; id=$mint; method="getAccountInfo"; params=@($mint, @{encoding="jsonParsed"; commitment="finalized"})} | ConvertTo-Json -Depth 10
(Invoke-RestMethod -Uri $rpc1 -Method Post -ContentType "application/json" -Body $mintQuery) | ConvertTo-Json -Depth 30 | Set-Content -Encoding utf8 ".\mfrg-mint.json"
$inventoryQuery = @{jsonrpc="2.0"; id=($mint + ":inventory"); method="getProgramAccounts"; params=@("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA", @{encoding="jsonParsed"; commitment="finalized"; withContext=$true; filters=@(@{dataSize=165}, @{memcmp=@{offset=0; bytes=$mint}})})} | ConvertTo-Json -Depth 20
(Invoke-RestMethod -Uri $rpc1 -Method Post -ContentType "application/json" -Body $inventoryQuery) | ConvertTo-Json -Depth 40 | Set-Content -Encoding utf8 ".\mfrg-accounts-one.json"
(Invoke-RestMethod -Uri $rpc2 -Method Post -ContentType "application/json" -Body $inventoryQuery) | ConvertTo-Json -Depth 40 | Set-Content -Encoding utf8 ".\mfrg-accounts-two.json"
python tools/reconcile_mfrg_token_accounts.py --mint $mint --mint-json ".\mfrg-mint.json" --first-accounts ".\mfrg-accounts-one.json" --second-accounts ".\mfrg-accounts-two.json" --first-origin "https://api.mainnet-beta.solana.com" --second-origin "https://INDEPENDENT_SOLANA_MAINNET_RPC_PROVIDER"
```

Origin flags contain HTTPS **hostnames without API keys or private paths** and are unauthenticated claims. Keep unmodified evidence and independently record provider provenance, capture time and finalized slot. Do not commit wallet credentials or private provider details to GitHub.

## Remaining verification gates

- A token-account owner address is not proof of beneficial ownership by the project or founder. Treasury custodians, delegate powers, LP vaults, frozen accounts, and escrow contracts need separate authorized verification. A matching sum does not prove a complete inventory.
- Source mismatches may indicate stale data, transfers, provider limits or incomplete filtering. Obtain fresh evidence instead of editing JSON to force agreement.
- Only real independently verified token-account addresses, signer authority and project authorization can identify the nine planned treasury accounts. **This tool does not label any wallet as the founder or a treasury.**
- The 500M mFRG lifetime plan remains a **target**, not an observed supply. The **50M lifetime fundraising** budget does not widen the **5M initial pilot cap**. The **30M founder-beneficial 6%** is 15M unrestricted at actual launch and 15M labeled team but owned by the same founder, vesting 625k monthly in months 13–36. No distribution has been verified here.
- No native FRG RandomX consensus rules, mint authority, token balances, sale flags, founder vesting or liquidity were changed by this documentation.

## Synthetic tests

```sh
python3 tools/test_reconcile_mfrg_token_accounts.py
python3 tools/test_reconcile_mfrg_mint_snapshots.py
python3 tools/test_verify_mfrg_mint_snapshot.py
python3 tools/test_mfrg_treasury_vesting_preflight.py
python3 tools/test_mfrg_policy.py
```

**Next step:** authenticated on-chain mint and account evidence, then independently audited owner/authority-to-purpose ledger and future custody deployment plan.
