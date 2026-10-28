# mFRG Solana mainnet mint verification — read-only preflight

**Step 09, October 28, 2026 · Status: MAINNET MINT UNVERIFIED. No on-chain operation is authorized.**

This is a practical procedure for determining whether the *user's actual, independently sourced* miniFORGE (mFRG) SPL token exists on **Solana mainnet**, what total supply has been minted, and whether mint/freeze authorities remain. Do **not** create a replacement mint because a repo config has `network_mint_address: null`. The known historical mint `9HuHPHPeWZBtRJmhsne17pVzUkFYMf9Rg1ZwdH45ebkw` is a **devnet** test asset, not evidence of a mainnet mint. Earlier October 27 fee-payer SOL balance is historical and not current.

## 1. Obtain the correct mint identity; never infer from a ticker

Acquire the exact **Solana mainnet mint address** from the project owner's actual issuance transaction, verified Solana wallet/account history or signed deployment record. A symbol, image, metadata field, search hit or ticker “mFRG” is **not identity proof**; tokens may impersonate names. Record who supplied the address, the creation transaction signature, network, independently verifiable mint owner, time/slot and the authoritative treasury signers. Do not disclose seed phrases or private keys.

**Current state:** No independently authenticated mainnet address, supply, authorities or account holdings have been established in the current GitHub planning records. The goal is **500,000,000 mFRG (500,000,000,000,000 atomic units at six decimals)**, *not* a claim that these assets have already been minted.

## 2. Fetch an actual mainnet RPC mint snapshot without signing

On the project owner's Windows computer, replace only the placeholder with an **independently sourced, verified mainnet mint address**. This makes a read-only RPC request and saves the result locally:

```powershell
$mint = "REPLACE_WITH_ACTUAL_MAINNET_MFRG_MINT_ADDRESS"
$rpc = "https://api.mainnet-beta.solana.com"
$body = @{
  jsonrpc = "2.0"
  id = $mint
  method = "getAccountInfo"
  params = @($mint, @{ encoding = "jsonParsed"; commitment = "finalized" })
} | ConvertTo-Json -Depth 8
$reply = Invoke-RestMethod -Uri $rpc -Method Post -ContentType "application/json" -Body $body
$reply | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 ".\mfrg-mainnet-mint-snapshot.json"
python tools/verify_mfrg_mint_snapshot.py --mint $mint --rpc-json ".\mfrg-mainnet-mint-snapshot.json"
```

The script **does not contact RPC**: it only examines the saved JSON. It rejects wrong programs, bad decimals, stale devnet address, invalid mint data, missing authority fields, empty accounts, supply beyond the policy cap and mismatched RPC IDs. The returned status remains **snapshot self-consistent, not independently authenticated**. A static file can be forged. Verify the mint on an independent Solana mainnet explorer and through a second trusted mainnet RPC provider before any operational decision.

### What is checked

- Response must be from `getAccountInfo`, with `encoding=jsonParsed`, account type `mint`, positive context slot, and the requested mint address echoed as the RPC `id`.
- Account owner must be the **original SPL Token program**: `TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA`, not Token-2022 or an arbitrary program.
- `isInitialized=true`, **decimals=6**, raw minted supply a nonnegative integer not exceeding 500,000,000,000,000 units.
- Record **mintAuthority** and **freezeAuthority** exactly (including non-null controls). Missing keys are **invalid evidence** and must never be interpreted as authority revocation.
- Output decision clearly distinguishes fixed supply at target, irreversibly fixed below target, target with mint authority still active, and below target with mint authority active.

**No authority actions, supply changes or transfers occur.**

## 3. Critical mint authority decisions

| On-chain state **if independently verified** | Interpretation and required next action |
| --- | --- |
| 500M minted, mintAuthority null | Target quantity fixed at that supply under standard mint controls. Verify freezes, token holders and all allocated accounts before further use. |
| Fewer than 500M minted, mintAuthority null | Supply cannot be increased on that mint. **Do not mint or claim 500M**. Prepare a documented, legally reviewed migration or amend policy through a new owner decision. |
| 500M minted, mintAuthority active | Mint is **not fixed** even if the current supply equals 500M. Owner/security review must verify proper authority control; eventual revocation only after supply and custody reconciliation. |
| Fewer than 500M minted, mintAuthority active | Potential future issuance only if legitimately controlled by project signers; **not authorized by this document**. Reconcile mint inventory and obtain security/legal approval before an issuance decision. |
| More than 500M minted, wrong token program or decimals | Stop: conflicts with current allocation plan or token identity. Do not label it official. |
| Freeze authority active | The freeze administrator may restrict token accounts. Disclose and separately review this centralized power; revocation requires an actual signed instruction and cannot be undone once permanently removed. |

On-chain minted supply is **not circulating supply**. Proving the allocations requires independently querying the token accounts and owner/authority for all nine project purposes, vesting vault contents, outside holders and LP inventory. Add balances without double counting delegated/escrowed/LP-held tokens. Do not publish treasury addresses before authenticating the parties who control them.

## 4. Gate before any founder or treasury allocation

1. Verify real mainnet mint address through two independent sources, correct network, official token program, decimals, supply and authority.
2. Get the mint issuer's **explicit authorization** to reconcile or operate it, and identify any existing minted balances, commitments or holder rights.
3. Confirm the permitted total supply (or document a properly disclosed migration if incompatible). Never assume an address is yours because it shares a logo or ticker.
4. Approve a project multisig, account registry and independent signer recovery / compromise procedures.
5. Fund independent earmarked vaults; verify **15M unrestricted founder** and **15M contract-enforced founder-beneficial vesting**, with 625k monthly unlocks across months 13–36. These are **not yet executed**.
6. Validate the remaining seven earmarked mFRG treasury allocations and the independent non-mFRG **USDC/SOL proceeds** treasury.
7. Obtain legal, accounting and smart-contract review before any mFRG-for-crypto exchange, staking or cross-chain program.

See [current lifetime tokenomics](MFRG_LIFETIME_TOKENOMICS_500M.md), [nine-account treasury and vesting gates](MFRG_TREASURY_VESTING_GATES.md), [desktop non-transactional config](../apps/desktop/config/miniFORGE.mainnet.plan.json), and [Step 08 handoff](handoffs/MFRG_500M_STEP_08_OFFLINE_SALE_BACKEND_2026-10-28.md).

**Sources:** [Solana parsed RPC response structures](https://solana.com/docs/rpc/json-structures), [reading a mint account from the network](https://solana.com/docs/intro/quick-start/reading-from-network), and [mint/freeze authority revocation](https://solana.com/docs/tokens/basics/set-authority).
