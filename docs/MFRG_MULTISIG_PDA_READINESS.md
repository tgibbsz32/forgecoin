# miniFORGE treasury custody — SPL multisig and program-derived authority preflight

**Step 14 · October 28, 2026. Read-only planning and offline verification only.**

The actual ForgeCoin miniFORGE (mFRG) Solana mainnet mint remains **unverified**. No treasury accounts, authorized multisig signers, vesting program or founder recipient have been authenticated from actual mainnet evidence. This document and its corresponding test suite do **not** deploy custody or transfer tokens.

## Why Step 13 is insufficient

A direct Ed25519 consent signature can establish that a wallet key signed a precisely scoped message, but cannot prove beneficial ownership, a multisig's authorized threshold, or control over a program-derived address (PDA). A Solana **PDA has no private key** and can only act through its deriving program and verified cross-program invocation. An SPL multisig is a separately parsed SPL Token Program account with a list of signer public keys and an *m-of-n* threshold. Neither a mere authority address nor an unauthenticated JSON response is proof of organizational custody.

## New fail-closed verifier

[`tools/verify_mfrg_multisig_pda.py`](../tools/verify_mfrg_multisig_pda.py) reads an inert local purpose claim, a saved `getAccountInfo(jsonParsed)` mint record, a saved mint-filtered `getProgramAccounts(withContext=true,jsonParsed)` token-account scan, and—only for SPL multisig—a saved `getAccountInfo(jsonParsed)` response for the token account's reported owner authority. **No RPC, private key, transaction signing, minting, token transfer or filesystem write.**

For `authority_type: spl_multisig`, the tool checks the following details **against the submitted snapshots**:

- Exactly matching token-account mint, owner authority and purpose; valid six-decimal raw balance greater than zero and no greater than that single purpose's planned allocation.
- Standard SPL Token Program account, parsed type `multisig`, initialized state, five distinct signer public keys, and exact correspondence with the five *declared* keys.
- Proposed normal operational accounts require **3-of-5** signers; proposed emergency account requires **4-of-5**. Those thresholds are still a policy proposal, not an approved deployed account.
- Token account must not be frozen, delegated, or subject to a separate close authority in the supplied snapshot.
- Mint, token account and multisig evidence slots must be within 1,500 slots, to reject clearly stale and contradictory records.
- Founder immediate and deferred allocations are **not accepted as SPL multisig vesting proof**. The deferred 15M requires a separate independently audited timelock and beneficiary evidence.

The strongest possible positive result is `OFFLINE_SPL_MULTISIG_STRUCTURE_CONSISTENT_ONLY`. It *does not* prove the account exists on mainnet, that the issuer owns it, which human controls the signer keys, signer independence, a 3/5 or 4/5 transaction authorization, governance consent, beneficial ownership, treasury funding or legally sufficient custody. All such authorization, audit and live-network flags remain **false**.

For `authority_type: program_pda`, the tool **never claims to have validated the PDA**. It only records the claimed program ID and returns `BLOCKED_REQUIRE_AUTHENTICATED_PDA_DERIVATION_AND_PROGRAM_AUDIT`. Completing a real on-chain PDA custody proof additionally requires authenticated program ID, exact binary seeds, **canonical bump**, actual derived address check, authenticated deployed program bytecode and upgrade authority, code/permission audit, token account association and any beneficiary/vesting-program terms. The program authority cannot pass the Step 13 direct-wallet Ed25519 signature protocol.

## Operator instructions after mint authentication

Start with [mint evidence Step 9](MFRG_SOLANA_MINT_VERIFICATION.md), [dual-source mint evidence Step 11](MFRG_DUAL_SOURCE_MINT_VERIFICATION.md), [complete holder snapshot Step 12](MFRG_TOKEN_ACCOUNT_INVENTORY.md), and [direct-wallet consent Step 13](MFRG_OWNER_PURPOSE_ATTESTATIONS.md).

Only if owner-controlled mainnet mint creation records are authenticated and trusted finalized snapshots exist, prepare a local non-public manifest using the [inert custody template](mfrg-multisig-pda.template.json). A hypothetical example with placeholders:

```json
{
  "schema": "mfrg-custody-preflight-v1",
  "network": "mainnet-beta",
  "mint": "VERIFIED_REAL_MAINNET_MINT_PUBLIC_KEY",
  "claim": {
    "purpose": "operations",
    "authority_type": "spl_multisig",
    "token_account": "VERIFIED_SIX_DECIMAL_SPL_TOKEN_ACCOUNT",
    "owner_authority": "VERIFIED_MULTISIG_PUBLIC_KEY",
    "expected_signer_keys": ["SIGNER_1", "SIGNER_2", "SIGNER_3", "SIGNER_4", "SIGNER_5"]
  }
}
```

Read-only query for the multisig authority can be made using `getAccountInfo` at finalized commitment:

```powershell
$auth = "VERIFIED_EXISTING_SPL_MULTISIG_AUTHORITY"
$rpc = "https://INDEPENDENT_MAINNET_RPC_PROVIDER"
$body = @{jsonrpc="2.0"; id=$auth; method="getAccountInfo"; params=@($auth, @{encoding="jsonParsed"; commitment="finalized"})} | ConvertTo-Json -Depth 10
(Invoke-RestMethod -Uri $rpc -Method Post -ContentType "application/json" -Body $body) | ConvertTo-Json -Depth 30 | Set-Content -Encoding utf8 ".\mfrg-multisig-account.json"
```

Then on the same trusted local computer, only after collecting the actual mint and token-account JSON:

```sh
python3 tools/verify_mfrg_multisig_pda.py --manifest ./local-custody-manifest.json --mint-json ./local-mint.json --inventory-json ./local-accounts.json --authority-json ./local-mfrg-multisig-account.json
```

Do not publish private access-provider URLs, personal identifiers or wallet secrets in GitHub, and **never** ask signers to transfer tokens simply to test an address.

## Treasury budget constraints remain unchanged

500M mFRG intended supply, with nine buckets: 50M lifetime fundraising (**only 5M first pilot**), 100M operations, 100M ecosystem, 85M finite staking, 60M liquidity, 65M engineering/security, 15M founder unrestricted at actual valid launch, 15M **same-founder-beneficial team-labeled** deferred with 625,000 mFRG monthly at ends of months 13–36, and 10M emergency. Founder total beneficial allocation is **30M / 6%**.

The project still has **no verified mFRG mainnet mint address, current supply, actual authority, treasury account holdings, or deployment authorization**. No mint, sale, staking, liquidity, vesting, or native FRG consensus changes occur in Step 14.

## Automated regression tests

```sh
python3 tools/test_verify_mfrg_multisig_pda.py
node --test tools/test_verify_mfrg_purpose_attestations.cjs
python3 tools/test_reconcile_mfrg_token_accounts.py
python3 tools/test_mfrg_policy.py
python3 tools/test_mfrg_treasury_vesting_preflight.py
```

**Reference:** [Solana program-derived accounts](https://solana.com/docs/core/pda) and [Solana parsed RPC structures](https://solana.com/docs/rpc/json-structures). Both describe the technical protocol, **not** ForgeCoin's actual on-chain deployment.
