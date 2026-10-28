# miniFORGE Step 17 — opt-in live mainnet holder inventory verification

**2026-10-28 · READ-ONLY · no keys, payment, signing, minting or token transfers.**

The ForgeCoin repository still contains **no independently authenticated existing Solana mainnet miniFORGE (mFRG) mint public key or mint-initialization transaction signature**. The intended 500M policy supply is not an on-chain issuance certificate. The historical devnet mint `9HuHPHPeWZBtRJmhsne17pVzUkFYMf9Rg1ZwdH45ebkw` must **not** be substituted.

Step 15 recorded this evidence blocker. Step 16 introduced an opt-in live **mainnet genesis + mint initialization** checker. **Step 17 now extends that checker to a full read-only SPL holder-account enumeration**, compared across two separately selected HTTPS RPC providers, without hiding uncertainty about provider honesty or scan completeness.

## Read-only flow (exactly 10 RPC requests on a successful run)

The [opt-in live holder checker](../tools/read_mfrg_mainnet_inventory.py) accepts the actual mint public key, the genuine existing `initializeMint` / `initializeMint2` transaction signature, and **two separate public HTTPS RPC origins** (no API-key path, embedded credentials or private hosts). It makes these requests:

1. Existing [Step 16 six-request provenance gate](MFRG_LIVE_MAINNET_PROVENANCE.md): for **each** provider, `getGenesisHash`, `getAccountInfo` for the mint, and `getTransaction` for its initialization signature. Every genesis must match the known Solana Mainnet Beta genesis; supply, token program, six decimals, mint/freeze authorities and transaction details must reconcile under existing tools.
2. A **fresh** `getAccountInfo` for the mint on provider A and B.
3. `getProgramAccounts` on provider A and B, querying only the original **SPL Token Program** `TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA`, with `encoding=jsonParsed`, `commitment=finalized`, `withContext=true`, and both filters `dataSize:165` and `memcmp offset 0 == actual mint address`.
4. Compare the two fresh mint snapshots and both holder-account arrays using the existing [Step 12 accounting validator](MFRG_TOKEN_ACCOUNT_INVENTORY.md). Require identical token-account pubkey sets, exact atomic amounts, authorities, frozen/delegated state, close authorities, reasonably close finalized slots, and sum of listed balances exactly equal to the fresh mint supply and Step 16 supply. Any disagreement or missing account **blocks** success rather than defaulting to zero.

No unfiltered global program scan is permitted. RPC transport uses direct HTTPS TLS hostname checks with no redirects, 12-second per-request timeout and a **2 MB per-response limit**. On a large network or rate-limited endpoint, the response can exceed that cap or the provider can refuse `getProgramAccounts`: in either case the tool **fails closed**, not “no holders.”

## Operator command (only after obtaining real authentic public identifiers)

```powershell
python tools/read_mfrg_mainnet_inventory.py `
  --mint "REAL_OWNER_VERIFIED_EXISTING_MFRG_MAINNET_MINT" `
  --signature "REAL_INITIALIZEMINT_TRANSACTION_SIGNATURE" `
  --rpc-one "https://api.mainnet-beta.solana.com" `
  --rpc-two "https://SECOND_INDEPENDENT_MAINNET_RPC_HOST"
```

This example **cannot** be executed with real project identifiers until the project owner provides them. Use genuinely separate independently administered providers; differently spelled hostnames are not proof of independent operation. Never supply mnemonic, private key, signing requests, RPC credentials or sensitive custody exports. Do not alter raw chain data or use the historical devnet test mint to make a local test pass.

### What a green result establishes—and does not

It establishes only that **two TLS-connected, operator-selected RPC hosts** reported the mainnet genesis, consistent parsed mint-initialization and supply evidence, and matching parsed token-account data at approximately compatible slots, with listed balances summing to the claimed minted supply.

Even then, the tool explicitly returns **false** for independently cryptographic authentication of RPC answers and transaction signatures, provider independence, independently proven account-scan completeness, the ForgeCoin issuer's identity, founder/treasury beneficial ownership, verified live vesting, and authorized issuance/sale. A deceptive provider could fabricate internally consistent JSON. Additional signed/public chain verification and legal/custody approval remain essential.

**Do not misrepresent a matching account list as proof that all nine intended treasury vaults are funded or that the founder possesses 30M mFRG.** The nine category allocations have not been matched to real authenticated treasury accounts.

## Protocol and economic safeguards unchanged

The proposed SPL supply remains **500,000,000 mFRG**, at six decimals; actual issuance unverified. Nine nonoverlapping categories: **50M lifetime fundraising (only 5M first-pilot limit)**, 100M operations, 100M ecosystem, 85M finite staking rewards, 60M liquidity, 65M engineering/security, 15M founder unrestricted at actual launch, 15M team-labeled but beneficially held by the same founder (625k monthly at ends of months 13–36 under a future audited funded escrow), and 10M emergency. **Founder total beneficial allocation is 30M / 6%.** Native FRG RandomX PoW, its tail emission and mainnet are independent and unchanged.

No production mint, treasury token account, signer, vesting program, staking, pool, checkout, payment collection or quote was configured or enabled during this step.

## Automated verification (synthetic only)

```sh
python3 tools/test_read_mfrg_mainnet_inventory.py
python3 tools/test_read_mfrg_mainnet_provenance.py
python3 tools/test_reconcile_mfrg_token_accounts.py
python3 tools/test_verify_mfrg_mint_initialization.py
python3 tools/test_mfrg_policy.py
```

**Next:** Once the actual owner-authenticated mint and creation signature are available, execute the opt-in read-only check with independent provider corroboration, and verify which **real** account signers/program controllers have authority over the nine allocations. Until then preserve sale/issuance/treasury deployment holds.
