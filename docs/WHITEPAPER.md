# ForgeCoin Technical and Economic Whitepaper

[Current mainnet specification and release status](CURRENT_MAINNET.md). The October 26 identity is frozen and unlaunched; main-branch runtime remains legacy pending separate implementation review.

Version 0.3 — October 28, 2026 (mFRG lifetime policy revision)

## Abstract

ForgeCoin is a privacy-preserving, proof-of-work digital currency derived from Monero v0.18.5.1. It combines private-by-default transactions, RandomX CPU mining, independent full-node validation, and a desktop application with a local blockchain explorer. The network is designed so users can validate balances, blocks, transactions, and consensus rules without trusting a hosted website.

ForgeCoin is presently in its bootstrap stage. The selected mainnet is unlaunched; release requires attracting independent nodes and miners, distributing hash power across operators, reviewing the forked source, and maintaining a transparent release process.

## Mission

ForgeCoin aims to provide private, CPU-accessible peer-to-peer digital cash that people can validate, mine, and explore on their own computers without relying on a central custodian or hosted block-explorer website.

The project follows four operating principles:

1. Users should be able to verify the chain with their own node.
2. Transaction privacy should be the default rather than an optional feature.
3. Mining should remain accessible on commodity CPUs through RandomX.
4. Consensus changes should be published in source, reviewed publicly, and activated only through a clearly announced network upgrade.

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

## Separate miniFORGE (mFRG) — updated 500M lifetime policy

miniFORGE is an economically separate, **500,000,000 target fixed-supply** standard SPL token (6 decimals) that would support Solana-side adoption, treasury governance, software services, participation incentives and liquidity. This is an approved **project allocation plan**, **not verified mainnet minting, a sale approval, a live staking product or FRG-backed collateral**. There is no fixed FRG/mFRG conversion. FRG retains its own primary-emission reference and continuing tail reward.

| Proposed purpose | mFRG | Share |
| --- | ---: | ---: |
| Staged crypto-denominated fundraising | 50,000,000 | 10% |
| Long-term operations/development | 100,000,000 | 20% |
| Ecosystem adoption/grants | 100,000,000 | 20% |
| Staking/participation rewards | 85,000,000 | 17% |
| Liquidity | 60,000,000 | 12% |
| Engineering/security | 65,000,000 | 13% |
| **Founder, freely unlocked immediately** | **15,000,000** | **3%** |
| **Founder-beneficial team-labeled vesting, months 13–36** | **15,000,000** | **3%** |
| Emergency | 10,000,000 | 2% |
| **Total** | **500,000,000** | **100%** |

Both 3% buckets belong to **the same founder**. The deferred 15M unlock **625,000 mFRG monthly from month 13 through 36**. Fundraising can exchange mFRG for **USDC/SOL or other expressly approved crypto**, with 5M pilot, 15M additional year 1, 20M years 2–3 and 10M years 4–10. No live price, purchase facility, authority revocation or verified mainnet custody is claimed. The sale must meet independent engineering, legal and accounting gates.

The 85M reward reserve is finite, does not secure FRG's PoW chain, and does not guarantee APY. Prospective 30/90/180/365-day staking locks, weekly accrued claims and seven-day post-expiry cooldown remain subject to audit and approval. Liquidity needs separately acquired matching assets. Optional token burns would apply only to designated mFRG service fees, **not ordinary SPL transfers**. Project assets and founder benefits must be disclosed separately.

See the [complete lifetime tokenomics and release table](MFRG_LIFETIME_TOKENOMICS_500M.md), [treasury custody summary](MINIFORGE_SPL_TREASURIES.md), [planned website sale](miniforge-sale.html), and [future architecture](SOLANA_FCMP_CARROT_FUTURE_ARCHITECTURE.md).

## Governance milestone

Governance rules, treasury signers, conflicts-of-interest protections, approvals and public accountability must be adopted **before any approved mFRG distribution**, not after one has begun. Native FRG node consensus cannot be commanded by mFRG token votes. Former representative-chamber proposals do not establish binding voting rights.

## Proposed FCMP++/CARROT privacy upgrades

Subject to dedicated independent security review and a separate stressnet, plan authenticated curve-tree databases, full-chain membership proof and generalized Bulletproof component verification, CARROT wallet/address integration, legacy output compatibility, deterministic consensus execution and mempool revalidation. The preferred route is a reviewed **in-place native FRG hard fork** where continuity remains safe. A separate successor chain and voluntary, supply-conserving migration are only a fallback research option.

Future extensions also include native cross-chain atomic swaps, independently backed stable-denominated systems, TSS/MPC-controlled trading, L2 payments/batching, and possible L3 applications including private markets, merchants and selective disclosure. None is already live. Solana transfers and staking are publicly observable unless distinct independently reviewed privacy systems are added.

See the [technical roadmap](../ROADMAP.md), [mFRG treasury specification](MINIFORGE_SPL_TREASURIES.md), [public sale information](miniforge-sale.html), and [future protocol architecture](SOLANA_FCMP_CARROT_FUTURE_ARCHITECTURE.md).

## Disclaimer

This document describes software behavior and project intent. It is not a promise of value, investment return, anonymity, uninterrupted operation, or regulatory treatment. Network participants are responsible for evaluating software, operational, legal, and financial risk.
