# ForgeCoin future FCMP++/CARROT, L1/L2/L3 architecture

**Updated October 27, 2026. All capabilities listed here are future proposals, not production features.** The former wFRG/wrapped-FRG bridge was a superseded planning direction and is **not part of the current roadmap**.

## Intended sequence

1. Finish the independent FRG Proof-of-Work network and audit native wallet, RandomX mining, official pool, read-only explorer, node infrastructure and security release gates.
2. Separately issue **miniFORGE (mFRG)** on Solana once reviewed: 50M target SPL supply (6 decimals), **5M initial sale**, **5M designated to a post-sale liquidity/staking treasury**, and **40M to a future issuance/development treasury**. This token does not represent a guaranteed amount of FRG, is not an automatic native privacy wrapper and is not a dividend or yield promise.
3. Choose and publish governance rules **before the mFRG sale concludes**, with transparent treasury custody, approval thresholds, security and community oversight. No prescribed number of seats or vote type is adopted.
4. Pursue a reviewed FCMP++/CARROT **in-place hard fork** of the existing FRG chain if proven safe. Maintain valid legacy outputs and owners' rights, or propose a separately approved supply-conserving successor migration only if necessary.
5. Research native swaps, secure multiparty execution and optional future L2/L3 systems under independent threat models.

## mFRG distribution versus native FRG

The three mFRG allocations are **planned**, not verified funded mainnet token accounts. No sale is open, and a public Solana token or staking system cannot hide balances by virtue of association with native FRG. Future issuance from the 40M treasury means phased distribution of reserved mFRG; it does not authorize minting beyond the 50M target. Any true fixed maximum requires a validated issued supply and properly revoked mint authority.

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

No change in this architecture authorizes mining, new consensus activation, Solana minting, token-sale payment collection, staking/yield, custody transfers or deployment of unaudited financial services. Existing release freezes and exact identity verification remain required. See the [roadmap](../ROADMAP.md), [mFRG allocation controls](MINIFORGE_SPL_TREASURIES.md) and [governance design charter](../governance-charter.md).
