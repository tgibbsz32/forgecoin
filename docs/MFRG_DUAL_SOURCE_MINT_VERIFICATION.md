# miniFORGE (mFRG) — two-source mainnet mint evidence comparison

**Step 11 · October 28, 2026 · READ-ONLY. No issuance, custody or sale authorized.**

The actual owner-controlled Solana mainnet mFRG mint address is **still not independently authenticated** in this repository. This procedure cannot identify it from its symbol, artwork or a devnet test mint. Follow [Step 9 identity and mint checks](MFRG_SOLANA_MINT_VERIFICATION.md) first.

## Purpose and limitations

The tool [tools/reconcile_mfrg_mint_snapshots.py](../tools/reconcile_mfrg_mint_snapshots.py) accepts two separately obtained, saved Solana mainnet `getAccountInfo` JSON responses for one purported SPL mint. It checks whether both agree on the program, six decimals, raw token supply, mint authority, freeze authority, and snapshot slots.

**Agreement is not authentication.** A user could fabricate both documents or label one host as another. The tool cannot prove the provider's actual identity, network, token ownership, token-account balances or an authorized sale. Even on success the output sets `rpc_provenance_authenticated=false`, `independent_network_sources_proven=false`, `mint_ownership_proven=false`, `account_holdings_reconciled=false`, and `sale_or_issuance_authorized=false`. It does not perform network requests or use wallets.

## Collect evidence before running

1. Get the exact mainnet mFRG mint address from the owner's real mint-creation signature, verified wallet history or authorized project deployment record. The historical devnet test mint is NOT a valid mainnet identity.
2. Choose **two genuinely independent** Solana mainnet RPC providers. Query `getAccountInfo` at **finalized** commitment, using `encoding: jsonParsed`. Preserve both unmodified responses locally, with time/slot and provider identity.
3. Use an independent mainnet explorer and trusted RPC service to authenticate the mint, its source and its creation transaction. Do not merely rely on this tool's self-reported source labels.
4. Keep API credentials, private RPC paths, wallet secrets and unrelated personal records out of the public repository.

### Windows PowerShell (read-only)

Replace the placeholders with the genuine mint and distinct RPC hosts.

```powershell
$mint = "REPLACE_WITH_VERIFIED_MAINNET_MFRG_MINT"
$rpc1 = "https://api.mainnet-beta.solana.com"
$rpc2 = "https://INDEPENDENT_SOLANA_MAINNET_RPC_ORIGIN"
$body = @{ jsonrpc="2.0"; id=$mint; method="getAccountInfo"; params=@($mint, @{encoding="jsonParsed"; commitment="finalized"}) } | ConvertTo-Json -Depth 8
(Invoke-RestMethod -Uri $rpc1 -Method Post -ContentType "application/json" -Body $body) | ConvertTo-Json -Depth 20 | Set-Content -Encoding utf8 ".\mint-one.json"
(Invoke-RestMethod -Uri $rpc2 -Method Post -ContentType "application/json" -Body $body) | ConvertTo-Json -Depth 20 | Set-Content -Encoding utf8 ".\mint-two.json"
python tools/reconcile_mfrg_mint_snapshots.py --mint $mint --first-json ".\mint-one.json" --second-json ".\mint-two.json" --first-origin $rpc1 --second-origin $rpc2
```

Only supply **HTTPS origin hostnames** (not private API paths/keys) to the tool's origin flags. A provider label is an unverified claim. If both documents happen to be identical at one slot, request fresh independent observations; **do not edit the response files just to pass a test**.

## Interpretation

| Comparable provided data | Meaning if authenticated independently | Still blocked |
| --- | --- | --- |
| 500M supply, null mint authority | Existing mint may be permanently fixed at the policy quantity | Holder accounting, founder transfers, treasury funding, sales |
| Below 500M, null mint authority | Cannot mint the remainder on that existing token; needs disclosed migration/policy review | Unilateral minting or claiming 500M issued |
| 500M, authority active | Minted amount at target, but supply not immutable | Fixed-supply claim and unapproved authority changes |
| Less than 500M, authority active | Minting might technically remain possible under signer control | Actual issuance without explicit owner, security/legal approval |
| Different authorities, supply or decimals between sources | Inconsistent evidence | All mainnet mint assertions |
| Matching mint data with unknown owners | Does not reveal who holds the tokens | All treasury/founder distribution actions |

The total mFRG **proposed lifetime allocation remains 500M**, including 50M maximum fundraising (only **5M initial pilot**), 100M operations, 100M ecosystem adoption, 85M finite staking rewards, 60M liquidity, 65M engineering/security, 10M emergency and the **30M total founder-beneficial 6%**: 15M liquid at actual launch and another 15M labeled team but owned by the same founder, intended to vest 625,000 at the end of each calendar month 13–36. None are shown here as distributed or held on-chain.

The next step after independently verifying mint identity is collecting a **complete token-account inventory**, identifying owner and delegated authorities and reconciling balances with the actual minted supply and the nine intended project accounts. A mint account alone does not establish treasury custody.

## Offline tests

```sh
python3 tools/test_reconcile_mfrg_mint_snapshots.py
python3 tools/test_verify_mfrg_mint_snapshot.py
python3 tools/test_mfrg_treasury_vesting_preflight.py
python3 tools/test_mfrg_policy.py
```

A passing offline test is neither an external security audit nor evidence of issued assets. No native FRG RandomX consensus or chain issuance has been modified.
