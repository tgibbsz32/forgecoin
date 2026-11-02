# ForgeCoin Technical and Economic Whitepaper

[Current mainnet specification and release status](CURRENT_MAINNET.md). The October 26 identity is frozen and unlaunched; main-branch runtime remains legacy pending separate implementation review.

Version 0.4 — November 2, 2026 (revised mFRG utility and 1:1 Solana bridge intentions)

## Abstract

ForgeCoin is a privacy-preserving, proof-of-work digital currency derived from Monero v0.18.5.1. It combines private-by-default transactions, RandomX CPU mining, independent full-node validation, and a desktop application with a local blockchain explorer. The network is designed so users can validate balances, blocks, transactions, and consensus rules without trusting a hosted website.

ForgeCoin is presently in its bootstrap stage. The selected mainnet is unlaunched; release requires attracting independent nodes and miners, distributing hash power across operators, reviewing the forked source, and maintaining a transparent release process.

## Mission

ForgeCoin aims to deliver privacy-preserving, CPU-accessible peer-to-peer money with independent native FRG validation, then extend its utility to Solana through the planned miniFORGE (mFRG) token. Its intended ecosystem includes **1 FRG : 1 eligible mFRG audited reserve-backed interoperability**, faster Solana transfers, supported DEXs, opt-in finite-reserve staking, and mFRG purchases of USD-priced CITY packs in ForgeCoin's planned Discover Your City game. These are future goals after native launch validation and the formal establishment of governance, not live conversion rights or verified deployments.

The project follows four operating principles:

1. Users should be able to verify the chain with their own node.
2. Transaction privacy should be the default rather than an optional feature.
3. Mining should remain accessible on commodity CPUs through RandomX.
4. Consensus changes should be published in source, reviewed publicly, and activated only through a clearly announced network upgrade.
5. Any 1:1 representation must carry independently verifiable native FRG reserves for all redeemable units, transparent redemption liabilities and explicit risk disclosures.
6. Solana utility does not inherit native FRG privacy or guarantee a fixed market exchange price.

## Architecture

ForgeCoin uses a CryptoNote-derived transaction model. The isolated fresh-mainnet candidate has a genesis block at protocol v1 and activates protocol v19 at height 1; this is not a public release or activation. The inherited technology includes RingCT confidential amounts, CLSAG signatures, Bulletproofs+, view tags, stealth addressing, and a fixed ring size of 16 under version 16 rules.

Full nodes verify every accepted block and transaction. Miners select valid transactions, perform RandomX proof of work, and extend the chain with the greatest cumulative difficulty. A miner with majority hash power can reorganize recent blocks or censor transactions, but it cannot create rewards or transactions that violate the rules enforced by honest full nodes.

## Network identity

| Item | Frozen October 26 mainnet (prelaunch) |
| --- | --- |
| Network name | ForgeCoin |
| Currency symbol | FRG |
| Address prefixes | 190 standard, 191 integrated, 192 subaddress |
| P2P port | 39480 TCP |
| RPC port | 39481 TCP |
| ZMQ RPC port | 39482 TCP |
| Network UUID | `bd936359-09e4-4fdb-8ec0-12fa9d6ef090` |
| Genesis nonce | 20261026 |
| Genesis hash | `4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c` |
| Consensus version | v1 at height 0, v19 from height 1 |
| Initial next-block difficulty | 500,000 through height 15 |
| Difficulty adjustment | Progressive LWMA from height 16, up to 90 intervals, 400,000 floor |

**Provenance:** Frozen manifest from new-mainnet source snapshot `62fc0b8`, draft PR #111; see [current specification](CURRENT_MAINNET.md). Main still contains legacy runtime code; documentation is not activation or release approval.

**Release blocker:** The genesis output of 11.92092895 FRG is indexed but not yet independently proven permanently unspendable.
Changing the genesis transaction or network UUID would create a different network. Ordinary application, seed-node, packaging, and user-interface updates do not require a chain restart.

## Proof of work and difficulty

ForgeCoin uses RandomX proof of work. RandomX is designed to favor general-purpose CPUs and reduce the advantage of specialized mining hardware. It does not guarantee equal participation: large CPU farms, botnets, cloud resources, or a dominant pool can still acquire substantial hash power.

The target is 120 seconds; initial difficulty is 500,000 through height 15, followed by progressive LWMA90 from height 16 with a 400,000 floor. The height-500/600/700 schedule belongs to the retired development implementation. Changes to consensus require reviewed software and coordinated activation.

## Tokenomics

ForgeCoin uses 100,000,000 atomic units per FRG, giving eight decimal places. The protocol defines a 50,000,000 FRG primary-emission reference and an emission-speed factor of 22 per minute. With the version 16 two-minute target, the effective per-block calculation uses a shift of 21:

`base reward = max((50,000,000 FRG - generated primary emission) / 2^21, 0.20 FRG)`

Block-weight penalties can reduce a miner's base reward when a block exceeds the permitted median weight. Transaction fees are paid in addition to the base reward.

| Economic parameter | Programmed value |
| --- | ---: |
| Primary-emission reference | 50,000,000 FRG |
| Decimal places | 8 |
| Genesis transaction output | 11.92092895 FRG |
| Initial height-1 base reward | approximately 23.84185222 FRG |
| Tail reward | 0.20 FRG per block |
| Expected blocks per day | 720 |
| Expected tail issuance per year | approximately 52,596 FRG |
| Coinbase maturity | 60 blocks, approximately 2 hours |
| Default ordinary output spendable age | 10 blocks, approximately 20 minutes |

The indexed genesis output in the tested candidate has unlock time 60. It has not been proved permanently unspendable; identifying an unlock time or maturity condition does not establish that any party knows its private spend key. The source code alone cannot establish who, if anyone, controls that key. The project should publicly document whether that output is spendable and its intended treatment before seeking exchange listing or material outside investment.

The primary emission approaches its reference gradually rather than using periodic halvings. The estimates below assume uninterrupted 120-second blocks, no reward penalties, and the currently programmed rules.

| Years from genesis | Estimated primary emission issued | Estimated base reward |
| ---: | ---: | ---: |
| 0 | 11.92 FRG | 23.84185222 FRG |
| 1 | 5,892,639 FRG | 21.03 FRG |
| 5 | 23,289,886 FRG | 12.74 FRG |
| 10 | 35,731,392 FRG | 6.80 FRG |
| 20 | 45,928,136 FRG | 1.94 FRG |
| 30 | 48,838,003 FRG | 0.55 FRG |
| approximately 38.1 | 49,580,570 FRG | 0.20 FRG tail reward |

Tail emission continues indefinitely. ForgeCoin therefore does not have a permanent maximum supply. Annual percentage inflation declines as circulating supply grows, while continuing to fund miners after primary emission reaches the tail threshold.

There is no native FRG token-sale, mFRG treasury, staking or project governance issuance mechanism in the FRG consensus code. Native FRG units are accounted for by genesis and Proof-of-Work block rewards, subject to the documented genesis release blocker. The separate proposed Solana mFRG token and future sale do not alter FRG consensus issuance.

## Privacy model

The public chain exposes block headers, transaction identifiers, proof-of-work data, fees, sizes, and confirmation depth. It does not expose ordinary transaction sender identities, recipient addresses, or transferred amounts in the form expected from a transparent UTXO ledger.

Privacy is not anonymity against every adversary. Wallet compromise, address reuse outside the protocol, exchange records, network observation, malware, poor operational security, and future cryptographic research can reveal information. Users must protect wallet files and recovery seeds and should connect through infrastructure they trust.

## Local blockchain explorer

The historical Windows Forms desktop included a local explorer reading from the daemon at `127.0.0.1`. The current Tauri desktop does not embed an explorer; a separate read-only explorer is maintained under `apps/explorer`. Each full-node user can inspect recent blocks and look up a block height, block hash, or transaction identifier without depending on a project website. Synchronized nodes should converge on the same valid chain. During a temporary network split, each explorer displays the chain currently accepted by its own node.

## Network security

Proof-of-work security is economic and relative. An early network with little independent hash power can be reorganized by an attacker with modest resources. Confirmation counts reduce risk from short reorganizations but cannot defeat an attacker who continuously controls a majority of hash power.

Security requires multiple independent miners and full nodes, geographic and provider diversity, distributed pool hash rate, reproducible builds, signed releases, published checksums, private vulnerability reporting, and conservative confirmation policies while total hash rate remains small.

The project should treat 30 percent pool share as a warning, coordinate miner migration near 40 percent, and treat a sustained majority as an incident requiring exchanges and merchants to pause deposits. Pool identities can be split or disguised, so these thresholds are operational signals rather than enforceable consensus limits.

## Governance and upgrades

ForgeCoin has no administrator key that can remotely rewrite consensus. Maintainers control the official repository, releases, branding, and default peer lists, but independently operated nodes decide which software to run.

Changing block rewards, monetary supply, proof of work, difficulty rules, or transaction-validity rules requires a scheduled consensus upgrade. If participants disagree and both rule sets retain support, the network can split into incompatible chains. Proposed consensus changes should include a written rationale, source diff, test results, activation height, migration instructions, and a public review period.

## Current limitations

ForgeCoin is not yet an independently audited production network. Its inherited Monero codebase is mature, but fork-specific configuration, economics, packaging, and applications introduce new risk. Mainnet currently lacks published stable seed infrastructure, release binaries are unsigned, and testnet and stagenet require ForgeCoin-specific identities before public use.

## License and provenance

ForgeCoin is derived from Monero v0.18.5.1 and CryptoNote code and is distributed under the BSD 3-Clause license included with the source. XMRig, when distributed with a desktop release, remains a separate GPLv3 component with its matching source and license.

## miniFORGE (mFRG) — proposed 50M Solana token and bridge

miniFORGE is intended as a **standard six-decimal Solana SPL token** with a **50,000,000 mFRG proposed maximum**, enabling Solana-side transfers and use in supported DEXs, optional staking and ecosystem services. The planned bridge would convert **1 native FRG to 1 eligible redeemable mFRG** with fully verifiable reserves and secure reverse conversion. Neither the bridge nor any redemption right currently exists.

| Proposed allocation | mFRG | Share |
| --- | ---: | ---: |
| Initial presale inventory | 5,000,000 | 10% |
| Future DEX/liquidity reserve | 5,000,000 | 10% |
| Combined staking, collateral and ecosystem/game reserve | 40,000,000 | 80% |
| **Total proposed fixed supply** | **50,000,000** | **100%** |

The 40M is a **single combined ceiling** pending approved suballocations. No founder token allocation exists under the present proposal. Proposed sale terms are **$0.12/mFRG** for up to 5M presale tokens, a $600,000 illustrative gross ceiling, and 90% project / 10% founder share of actual proceeds, with founder share half immediately and half in six monthly releases. Sale terms do not prove FRG backing or fix a future DEX market price.

**Technical and economic dependencies:** Each mFRG represented as 1:1 redeemable—including any presale, liquidity or staking units sold or distributed as backed—must correspond to one independently verifiable native FRG in secure custody. The 50M fixed SPL supply caps total eligible bridge capacity despite native FRG's continuing tail issuance. A pre-minted SPL token with revoked mint authority needs audited lock/release inventory, not unbounded mint-on-deposit. FRG uses eight decimals while mFRG uses six; conversion logic needs explicit dust, rounding and fee rules. Bridge security, chain-finality/reorg handling, proof-of-reserves, solvency audits, operator governance, emergency procedures and legal review are prerequisites. An unbacked fungible allocation cannot also promise 1:1 redemption.

**Intended uses:** mFRG transfers on Solana, trading through supported DEX liquidity pools with independently funded counterpart assets, voluntary staking incentives from a finite governed reserve (no guaranteed APY), and optional mFRG payments for USD-priced CITY packs in ForgeCoin's planned **Discover Your City** game. The server must verify finalized payments and credit CITY exactly once; all mFRG received for game purchases is allocated to the ecosystem treasury. Solana transfers are transparent and do not inherit native FRG privacy.

No mint, sale, bridge, reserve, DEX liquidity, staking, game checkout or price is verified active. See [tokenomics and bridge conditions](MFRG_50M_CITY_TOKENOMICS.md), [treasury design](MINIFORGE_SPL_TREASURIES.md), [exchange design](MFRG_EXCHANGE_DESIGN.md), [sale status](miniforge-sale.html) and [game integration](discover-your-city.html).

## Governance milestone

Governance rules, treasury signers, conflicts-of-interest protections, approvals and public accountability must be determined and published **before mFRG introduction, minting, sale, bridge activation, staking or distribution**, not after one has begun. Native FRG node consensus cannot be commanded by mFRG token votes. Former representative-chamber proposals do not establish binding voting rights.

## Proposed FCMP++/CARROT privacy upgrades

Subject to dedicated independent security review and a separate stressnet, plan authenticated curve-tree databases, full-chain membership proof and generalized Bulletproof component verification, CARROT wallet/address integration, legacy output compatibility, deterministic consensus execution and mempool revalidation. The preferred route is a reviewed **in-place native FRG hard fork** where continuity remains safe. A separate successor chain and voluntary, supply-conserving migration are only a fallback research option.

Future extensions also include native cross-chain atomic swaps, independently backed stable-denominated systems, TSS/MPC-controlled trading, L2 payments/batching, and possible L3 applications including private markets, merchants and selective disclosure. None is already live. Solana transfers and staking are publicly observable unless distinct independently reviewed privacy systems are added.

See the [technical roadmap](../ROADMAP.md), [mFRG treasury specification](MINIFORGE_SPL_TREASURIES.md), [public sale information](miniforge-sale.html), and [future protocol architecture](SOLANA_FCMP_CARROT_FUTURE_ARCHITECTURE.md).

## Disclaimer

This document describes software behavior and project intent. It is not a promise of value, investment return, anonymity, uninterrupted operation, or regulatory treatment. Network participants are responsible for evaluating software, operational, legal, and financial risk.
