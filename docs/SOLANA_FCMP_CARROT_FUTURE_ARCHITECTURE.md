# ForgeCoin interoperability and FCMP++/CARROT evolution

**Roadmap intentions — updated October 27, 2026. All functionality below is unimplemented.** These are prospective engineering goals, not active consensus, public services, token issuance, audited guarantees, regulatory exemptions or announced activation dates. Native ForgeCoin's frozen-genesis mainnet (nonce `20261026`) has **not launched**. The 11.92092895 FRG genesis output's permanent unspendability remains unproven.

## Intended sequence

1. **Launch and secure the existing native FRG L1.** Release a tested RandomX CPU miner, wallet and daemon, independent nodes, explorer, and verified mining pool; validate the emissions, chain identity, genesis, custody and public-release process first.
2. **First planned expansion: independent mFRG SPL token on Solana.** Prepare a legacy SPL Token asset with a proposed total allocation of **50,000,000 mFRG**: **5,000,000** reserved for potential USDC-denominated sale/trading/liquidity and **45,000,000** held for future decisions. It is **not** a 1:1 wrapper or redeemable claim on native FRG. No token, mint authority distribution, USDC market or sale has been launched. Any eventual sale requires its own legal and security reviews. A separate, optional, independently audited native-FRG-backed bridge could be considered later, with verifiable FRG locks, Solana burns, redemption, reserve reconciliation, reorg protections and distinct asset labeling. Solana activity is publicly observable and does not inherit native FRG privacy.
3. **Later native privacy upgrade: FCMP++ with CARROT.** Prefer a coordinated **in-place hard fork of ForgeCoin**, preserving the existing blockchain, issuance history, coin ownership and native FRG unit if the upgrade can safely support legacy output spends and wallets. A hard fork updates consensus and does **not** necessarily require a separate new blockchain. Independently verify chain continuity, migration tooling, pool and exchange compatibility, and broad node adoption before selecting an activation height.
4. **Separate successor network only if necessary.** If rigorous testing proves the in-place upgrade unsafe or infeasible, publish and audit a separate-chain, opt-in migration/bridge design: legacy-FRG lock/burn or equivalent proof, successor-chain claim, nonduplicated supply, user recovery, privacy review, replay protection, reorg/finality handling, redemption/dispute windows and explicit community consent. **No automatic copying of development-chain balances, no hidden premine, no involuntary swap.**
5. **Avoid confusing independent SPL supply with future bridged claims.** The initial mFRG allocation is not backed by native FRG. If a separate native FRG wrapper is later introduced, provide a distinct identity, audited custody, provable circulating-versus-backed supply and user redemption. Any eventual wind-down must honor outstanding obligations and provide notice and a verified redemption path; no forced forfeiture.

See [the proposed 50-million SPL distribution](SPL_TOKENOMICS_2026-10-27.md) and [the current launch infrastructure status](MAINNET_INFRASTRUCTURE_STATUS_2026-10-27.md). *These future upgrades are proposals, not guaranteed.*

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

Complete **native L1 wallet/miner -> validated node/pool/explorer -> independent mFRG SPL rollout (50M allocated, 5M potential USDC/trading) -> optional audited bridge as a separate project -> researched FCMP++/CARROT in-place upgrade -> optional atomic-swap/private-execution/L2/L3 services**. The FCMP++/CARROT successor is a **future implementation track**, not permission to replace the new-mainnet genesis, generate a second coin supply or abandon redemption for existing owners. See [the main roadmap](../ROADMAP.md) and [governance charter](../governance-charter.md).
