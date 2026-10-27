> [Current mainnet specification, tokenomics and release status](CURRENT_MAINNET.md) — October 26, 2026; prelaunch.

# ForgeCoin interoperability and FCMP++/CARROT evolution

**Committed development direction — October 26, 2026.** The capabilities below are planned engineering work and are not implemented on the current network.

<small>Proposed future upgrades; implementation and timing are not guaranteed.</small>

## Intended sequence

1. **Launch and secure the existing native FRG L1.** Release a tested RandomX CPU miner, wallet and daemon, independent nodes, explorer, and verified mining pool; validate the emissions, chain identity, genesis, custody and public-release process first.
2. **Post-launch mFRG development and eventual FRG-linked backing.** Design and pursue a user-deposit-backed 1:1 **wFRG** SPL/Token-2022 representation for easier access to Solana wallets, DEXes, payments and liquidity markets. **This is the first planned interoperability implementation.** Deposited native FRG backs the corresponding wrapped units; mint/burn/redemption must have verifiable supply conservation, exact 8-decimal handling, independently reviewed reserve custody/proofs, confirmations, replay/reorg defenses, rate limits, incident controls and audits. Token creation does not guarantee exchange listing or liquidity. The wrapper is **not** additional FRG mining or issuance. Solana activity is publicly observable and does not inherit FRG privacy automatically.
3. **Later native privacy upgrade: FCMP++ with CARROT.** Prefer a coordinated **in-place hard fork of ForgeCoin**, preserving the existing blockchain, issuance history, coin ownership and native FRG unit if the upgrade can safely support legacy output spends and wallets. A hard fork updates consensus and does **not** necessarily require a separate new blockchain. Independently verify chain continuity, migration tooling, pool and exchange compatibility, and broad node adoption before selecting an activation height.
4. **Separate successor network only if necessary.** If rigorous testing proves the in-place upgrade unsafe or infeasible, publish and audit a separate-chain, opt-in migration/bridge design: legacy-FRG lock/burn or equivalent proof, successor-chain claim, nonduplicated supply, user recovery, privacy review, replay protection, reorg/finality handling, redemption/dispute windows and explicit community consent. **No automatic copying of development-chain balances, no hidden premine, no involuntary swap.**
5. **Eventually reduce and phase out the interim wFRG reliance.** When the FCMP++/CARROT upgraded native ecosystem and safe liquidity alternatives operate, plan a gradual wrapper wind-down: notice to holders, stop new deposits/minting, maintain user redemption options, reconcile reserves and outstanding claims, coordinate venues, and only terminate custody/contracts after obligations have been addressed. No forced forfeiture or guaranteed wind-down date.

## FCMP++/CARROT core implementation gates (later, not current L1)

### 1. Curve-tree database integration

Evaluate the reviewed upstream authenticated curve-tree design, commitment/point representations, tree roots and ordering. Build incremental, crash-consistent LMDB indices or an equivalent store for block-driven additions, consensus roots, rollback/undo, deep reorganizations, pruning, snapshots, rebuilding, rescan and synchronization. Compare deterministic roots across x64 and ARM64. Profile I/O, CPU, RAM, initial sync and recovery. A broken tree index must block activation, not silently desynchronize validators.

### 2. Full consensus proof verification

Integrate FCMP++ membership/spend proofs and their **Generalized Bulletproofs components**, verified against the correct global commitment tree/root and required authorization/linkability rules. A Generalized Bulletproof is not the whole consensus proof. Define transaction versions, activation height, legacy-output inclusion, proof serialization, consensus determinism, spend/double-spend rejection, block acceptance, and malformed proof handling. Require independent vectors, adversarial tests and crypto review.

### 3. CARROT addressing and old-wallet continuity

Evaluate upstream `carrot_core` and `carrot_impl` for address derivation, wallet scans, outputs, view-only keys, seed recovery, subaddresses and cold wallets. Prefer allowing legacy unspent outputs and supported legacy wallets to remain spendable across an **in-place hard fork** and enter the new anonymity set under reviewed rules. Provide explicit address-format compatibility, backup/restore and migration UX. Privacy is not guaranteed to erase old network, exchange or counterparty metadata.

### 4. Mempool transition and performance

Handle larger proofs using bounded per-peer verification, fees/weight policy, queue/caching protections, reorg-aware transaction validation and safe block template construction. At the hard fork, **revalidate the full mempool**, evict transactions invalid under new rules while retaining valid transactions and preserving legitimate peer connections. Assess reviewed cryptographic speedups (including `fe_pow22523` changes) with known-answer and side-channel tests; one micro-optimization cannot guarantee node stability.

### 5. Independent adversarial stressnet

Operate an isolated disposable FCMP++/CARROT stressnet with separate genesis, ports and network UUID, informed by upstream Monero stressnet experience but not presumed equivalent. Test high-frequency valid and invalid transactions, heavy mempools, large templates, network partitions, deep reorgs, old/new wallet scans, DB crash/recovery and diverse hardware. Publish measured sync latency, proof throughput, memory usage, deterministic roots, failed cases, and reproducible consensus traces **before any public hard-fork schedule**.

## Later L1, L2 and possible L3 products

These are **separate, prospective protocols**, not features automatically delivered by FCMP++ or CARROT:

- **L1:** broader eligible-output anonymity sets, improved recipient wallet scanning, privacy-preserving address formats, reviewed migration of legacy outputs, and optional selective disclosure tools.
- **Cross-chain / L1-L2:** **native atomic swaps** with assets such as ETH and regulated stablecoins such as Ethereum USDC, using an explicitly developed locking/adaptor-signature or other trust-minimized design, timeouts, refunds, collateral and settlement proofs. Research a **privacy-shielded synthetic stable-denominated asset** with independently verifiable reserves, redemption, oracle, peg-risk and legal controls. An asset on a transparent chain is not inherently private.
- **L2:** payment channels, batched settlement, guarded atomic routing, cross-chain liquidity and optional privacy-preserving execution if suitable settlement/dispute and availability proofs can be built.
- **L2 / cross-chain institutional-size trading research:** a **TSS/MPC-secured private block-trade routing system** with independently controlled vaults on supported transparent chains, private order/intent submission, audited settlement delivery-versus-payment, blind/relayer execution as technically feasible, MEV and relay-collusion mitigations, and a **disclosed basis-point routing fee** as a proposed business model. TSS controls signing; it does not guarantee hidden settlement, instant finality, or anonymous counterparties.
- **Possible L3 applications:** private-market protocols, selective-disclosure business payments, encrypted auctions and settlement instructions, merchant services and programmable intent routing—each needs its own execution environment, security analysis and authorization model.

**Threat-model and legal limits:** FCMP++ privacy does not make transparent-chain settlement confidential, guarantee stable-asset backing, remove exchange records, prevent endpoint or network leakage, or make regulation inapplicable. Products must be designed for lawful privacy, security, auditable reserve/custody guarantees and applicable compliance. Institutional adoption and fee revenue are objectives, not forecasts.

## Release-order discipline

Complete **native L1 wallet/miner -> validated node/pool/explorer -> first Solana wrapper -> researched FCMP++/CARROT in-place upgrade -> optional atomic-swap/private-execution/L2/L3 services**. The FCMP++/CARROT successor is a **future implementation track**, not permission to replace the new-mainnet genesis, generate a second coin supply or abandon redemption for existing owners. See [the main roadmap](../ROADMAP.md) and [governance charter](../governance-charter.md).

## Update: mFRG is separate from wFRG (October 27, 2026)

A **separate miniFORGE / mFRG standard SPL asset** is proposed for Solana mainnet with **50 million target supply** allocated **5 million to a planned future sale/trading treasury**, **5 million to a future liquidity reserve** and **40 million reserved for later distribution**. The 6-decimal devnet mint exists with **zero issued supply**. The real mainnet mint is **not created**, a sale has not launched, the treasuries have no mainnet allocation and no SOL/USDC pool has been deployed. Mainnet issuance awaits fee funding, independent custody/metadata/authority review and on-chain verification. See [miniFORGE issuance and custody](MINIFORGE_SPL_TREASURIES.md).

**Do not confuse mFRG with the existing planned 1:1 deposit-backed wFRG bridge.** An mFRG balance does not represent a locked native FRG reserve or inherit private transaction properties. Any eventual wFRG must use an explicitly different token mint and provable native FRG collateral/mint/burn/redemption mechanics; those protocols remain future, unimplemented systems. The other long-term FCMP++/CARROT, native L1 swaps, L2 and potential L3 tasks in this document remain intended roadmap developments only and require separate technical/security validation.


## Superseding direction: mFRG replaces the proposed separate wFRG (October 27, 2026)

**Revised mFRG-first policy (October 27, 2026):** No separate wFRG token is currently planned. miniFORGE (mFRG), a distinct Solana SPL asset, is intended to serve as the ecosystem's FRG-linked asset. Following the mFRG presale and a period of native FRG public mining and observed price discovery, a separately audited protocol may allow FRG holders to lock or stake native FRG for mFRG-related rights. The **target is an eventual 1:1 FRG-backed relationship**, but this is a future design goal, not an existing 1 FRG = 1 mFRG redeemability promise. Because mFRG presale tokens may circulate before FRG collateral exists, the project must define how unbacked presale supply, reserves, new issuance, redemption rights and total circulating supply will be reconciled before calling mFRG fully backed. No bridge, staking, 1:1 reserve, conversion or redemption is live; native FRG mining rules are unchanged.

Earlier descriptions of wFRG issuance, separate bridge deployment, and wrapper phase-out in this document are historical proposals superseded by this decision, and must not be represented as the current architecture. Future audited custody, reserve verification, staking, burning and redemption designs still need explicit specifications.
