# Step 15 — mFRG mainnet mint evidence intake and release hold

**2026-10-28 · Evidence assessment: BLOCKED.**

## Discovery result

A fresh repository search for `mFRG mainnet mint`, `miniFORGE mint address`, and `Solana creation transaction` did not establish a genuine owner-authenticated Solana mainnet mFRG mint address or initialization transaction. The repository records the historic address `9HuHPHPeWZBtRJmhsne17pVzUkFYMf9Rg1ZwdH45ebkw` as **devnet-only**. It must not be used as a mainnet treasury or token identity. The target 500M mFRG supply is a **proposal, not observed issuance**.

The existing [read-only live provenance tool](../../tools/read_mfrg_mainnet_provenance.py) is already implemented. It requires the real mint and creation signature and checks independent operator-specified HTTPS RPC origins; there is no valid reason to invoke it with fabricated addresses or signatures.

## Evidence required from authorized issuer

Provide **public identifiers only**:

1. The exact mainnet mFRG **mint public key** from the owner's issuance transaction or verified custody records.
2. The corresponding **initialize-mint transaction signature** or trusted public explorer link to that transaction.
3. Confirmation that this is the project's genuine mint, not a name/ticker match or historic devnet experiment.

**Never provide seed phrases, wallet backups, private keys, API secrets or multisig recovery material.** Do not publish sensitive personal details or unapproved custody account addresses.

## Next execution once evidence is available

Use the existing [mainnet provenance guide](../MFRG_LIVE_MAINNET_PROVENANCE.md) to run `tools/read_mfrg_mainnet_provenance.py` in read-only mode against two separately selected and authenticated Solana mainnet RPC providers. Validate genesis, SPL Token Program owner, six decimals, actual atomic supply, initialize-mint transaction, mint/freeze authorities and finalized snapshot agreement. Then run the Step 12 holder inventory and Step 14 multisig/PDA structure checks **only against actual evidence**. A passing parser does not establish beneficial ownership or authenticated governance.

If the mint authority has been revoked while the observed supply is less than the proposed 500M, do **not** assume the balance can be minted later. Document the discrepancy and obtain explicit policy approval before any migration or alternative.

## Non-negotiable release holds

- No verified mainnet mFRG mint identity or issuance is established.
- No live treasury, signer independence, founder beneficiary or audited vesting contract is established.
- The nine proposed 500M allocations and **50M lifetime fundraising / 5M initial pilot** separation remain unchanged.
- The founder-beneficial **30M (6%)** includes both the 15M founder bucket and the 15M same-founder team-labeled deferred bucket; the latter remains 625k monthly at ends of months 13–36 **only if separately deployed and audited**.
- No SOL/USDC checkout, token issuance, transfer, vesting release, staking, liquidity, exchange listing or native FRG consensus change was authorized or performed.

**Step 15 handoff outcome:** Evidence intake reviewed, existing live verification tooling identified, and blocker documented. On-chain identity verification cannot be completed without authentic public mint and transaction identifiers. The next continuation should begin by supplying these identifiers, not by treating placeholder fixtures as mainnet.
