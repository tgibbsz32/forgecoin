# ForgeCoin future FCMP++/CARROT, L1/L2/L3 architecture

**Updated November 2, 2026.** The 50M mFRG token, audited native FRG↔Solana bridge, staking, DEX liquidity and game payments are planned capabilities, not live services.

## Intended development sequence

1. Independently verify native FRG genesis, RandomX, mainnet miners, wallets, pool, explorer and release infrastructure.
2. **Determine, ratify and publish governance procedures before any mFRG introduction**, including participants, bridge signers, treasury custody, reserve oversight, conflict procedures and emergency authority.
3. Introduce the proposed **50,000,000 standard six-decimal Solana SPL mFRG** only after release/legal/security gates: 5M initial presale, 5M DEX/liquidity reserve and 40M combined staking/collateral/ecosystem reserve. Provisional sale: $0.12/mFRG and 90% project / 10% founder proceeds, with half founder proceeds immediately and half over six months. There is no founder token allocation.
4. Design an audited **1 native FRG : 1 eligible mFRG** bidirectional bridge with one independently verifiable native FRG reserve for each outstanding redeemable mFRG, including presale, liquidity or staking tokens if marketed as backed. The 50M mFRG supply restricts bridge capacity despite native FRG's uncapped tail emissions. Build secure lock/release, 8-to-6 decimal conversion, proof-of-reserves, chain-finality and withdrawal safety.
5. Support faster Solana ecosystem transfers, independently funded DEX trading and optional finite-reserve mFRG staking; integrate optional mFRG purchases of USD-priced CITY packs in ForgeCoin's planned **Discover Your City** game. CITY is credited only after finalized payment verification, exactly once; all received mFRG goes to the ecosystem treasury.
6. Pursue independent FCMP++/CARROT native-chain upgrade research and later L1/L2/L3 services only after separately reviewed consensus and security gates.

## Proposed 1:1 objective versus current status

The targeted conversion ratio is not a currently supported redemption, guaranteed market price or claim of native FRG reserves. The fixed SPL supply requires audited, prefunded bridge inventory if mint authority is revoked. Solana transactions remain transparent and do not inherit FRG confidentiality. No bridge, reserve, mint, exchange, staking or game checkout is activated by this roadmap.

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
