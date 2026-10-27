# ForgeCoin Technical and Economic Whitepaper

[Current mainnet specification and release status](CURRENT_MAINNET.md). The October 26 identity is frozen and unlaunched; main-branch runtime remains legacy pending separate implementation review.

Version 0.2 — October 26, 2026

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

There is no token-sale, staking, governance-token, or protocol treasury mechanism in the current consensus code. Coins enter circulation through the genesis transaction and proof-of-work block rewards.

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

## Planned interoperability and future protocol upgrades

<small>Proposed future upgrades; implementation and timing are not guaranteed.</small>

ForgeCoin's intended Solana ecosystem asset is **miniFORGE (mFRG)**, with a proposed future independently reviewed native FRG staking/locking protocol targeting **1:1 FRG backing** only after public mining and observed price discovery. The presale is not itself FRG-backed and does not imply redemption rights.

A later technical objective is an **FCMP++/CARROT upgrade of the existing ForgeCoin blockchain via a coordinated hard fork**, if independently validated compatibility makes this safe. A separate successor network and voluntary migration plan would be considered only as a fallback. Plans for eventual Solana-wrapper retirement require a usable redemption process.

FCMP++/CARROT engineering includes authenticated curve-tree databases, membership-proof and Generalized Bulletproof consensus validation, CARROT wallet/address and legacy-output compatibility, mempool revalidation during upgrades, reviewed performance improvements and a separate high-volume stressnet.

Further planned systems include native cross-chain atomic swaps, collateralized stable-denominated private transfers, independently secured multi-party trading vaults, L2 payment/settlement systems and possible L3 private applications. These are future research items rather than features of the present network. See [the complete future architecture](SOLANA_FCMP_CARROT_FUTURE_ARCHITECTURE.md).

## Planned miniFORGE (mFRG) value-accrual and native FRG staking relationship (not live)

miniFORGE (mFRG) is intended to become the principal **ecosystem value-accrual asset associated with native ForgeCoin (FRG)**. This is a project design objective, **not** a claim that mFRG presently holds the market value of FRG, is collateralized by FRG, has a guaranteed exchange rate, or provides legal ownership of FRG reserves.

**Proposed sequence:** (1) independently validate and launch native FRG proof-of-work mining; (2) separately launch an mFRG SPL presale, subject to legal review, mint verification and operational readiness; (3) observe organic FRG mining participation, liquidity, price discovery and market stability over a meaningful but currently undefined period; (4) only after this evidence exists, design and independently review a mechanism enabling holders to **stake or lock native FRG in connection with mFRG**. The timing, economics and feasibility of this mechanism remain to be determined.

A staking mechanism does **not** automatically transfer FRG value to mFRG: the specification must state whether FRG is deposited into transparent custody, locked by a verifiable protocol, used to back issued mFRG units, earns rewards, supports redemption, or serves another explicit purpose. Any conversion, ratio, backing representation, yield or redemption entitlement would require separate public rules, reserves and security validation; **none is promised or presently active**. Staking must not silently alter native FRG proof-of-work issuance or infer that mFRG has existing native-FRG backing or guaranteed conversion.

**Pre-implementation gates:** obtain a market-observation methodology and published activation criteria; define custody and key management, accounting, contract roles, user withdrawal/redemption rules, risks, insolvency handling, independent testing and audits; assess securities, custody, money-transmission and tax treatment before accepting deposits. Solana transactions remain publicly observable despite native FRG's privacy properties.


## Proposed future development commitment — mFRG staking and protocol collateral (October 27, 2026)

**Committed roadmap direction; proposed implementations, not deployed features or guaranteed outcomes.** ForgeCoin intends for miniFORGE (mFRG), a separate Solana SPL asset, to become the ecosystem's staking and protocol-collateral asset linked to native mined FRG. This supersedes the proposal to launch a separate wFRG token. The following development workstreams are planned, subject to security, feasibility, governance and legal review:

1. **FRG staking with mFRG rewards:** after the native chain and mFRG presale have launched and FRG has undergone a meaningful period of mining and independent price discovery, design a voluntary, verifiable FRG lock/stake facility and distribute bounded mFRG allocations under published eligibility, accounting, and withdrawal rules. Staking does not alter native RandomX proof of work.
2. **mFRG collateral for cross-chain settlement:** evaluate mFRG security bonds for bridge operators and independently verified cross-chain swap/settlement roles, with enforceable penalties for objectively provable misconduct, transparent reserve requirements, and an explicit failure-recovery process.
3. **mFRG collateral for future L2/L3:** research use of mFRG in optional settlement-operator bonds and higher-layer financial protocols where collateral serves a real security function; do not require mFRG for ordinary L1 transfers, mining, or base privacy.
4. **Protocol governance:** evaluate clearly limited mFRG governance participation for the services backed by mFRG, without overriding native FRG consensus or miner/security governance.
5. **FRG reserve relationship:** investigate whether mFRG can develop a verifiable reserve connection to native FRG. **There is no current 1:1 FRG redemption promise, guaranteed peg, collateral coverage, staking yield, or right to a reserve.** The circulating presale supply and FRG reserve needs must be reconciled before any backing claim.

Fundamental **FCMP++/CARROT privacy upgrades must remain available without mFRG ownership**. Native FRG should continue operating if Solana, mFRG, or any future cross-chain mechanism is unavailable. Exact schedules, amounts, staking rewards, custody, slashing, contracts, audits and economics remain future specifications; none is operational or guaranteed.

## Disclaimer

This document describes software behavior and project intent. It is not a promise of value, investment return, anonymity, uninterrupted operation, or regulatory treatment. Network participants are responsible for evaluating software, operational, legal, and financial risk.


**Revised mFRG-first policy (October 27, 2026):** No separate wFRG token is currently planned. miniFORGE (mFRG), a distinct Solana SPL asset, is intended to serve as the ecosystem's FRG-linked asset. Following the mFRG presale and a period of native FRG public mining and observed price discovery, a separately audited protocol may allow FRG holders to lock or stake native FRG for mFRG-related rights. The **target is an eventual 1:1 FRG-backed relationship**, but this is a future design goal, not an existing 1 FRG = 1 mFRG redeemability promise. Because mFRG presale tokens may circulate before FRG collateral exists, the project must define how unbacked presale supply, reserves, new issuance, redemption rights and total circulating supply will be reconciled before calling mFRG fully backed. No bridge, staking, 1:1 reserve, conversion or redemption is live; native FRG mining rules are unchanged.


## Fixed mFRG supply, staged presale and risk disclosures (October 27, 2026)

**Approved planning specification, not a live offer:** 50,000,000 miniFORGE (mFRG) standard SPL tokens (6 decimals), provisionally apportioned to a 5,000,000 mFRG presale vault (10%), 5,000,000 mFRG liquidity reserve (10%) and 40,000,000 mFRG future staking, collateral and distribution reserve (80%). No separate wFRG mint is planned. Mint authority, custody, vesting and whether mint authority can be revoked require publication and independent review before issuance.

**Presale proposal:** five inventory rounds of exactly 1,000,000 mFRG each, at $0.01, $0.02, $0.03, $0.04 and $0.05 USD per token, respectively, totaling **up to $150,000 USD gross only if every round sells out**. Accept **native Solana USDC** (mint `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v`) and native SOL through independently verified, expiring USD-based quotes. **Ethereum and ETH payments are excluded from this presale.** No purchase endpoint, token delivery or presale contract is operational today.

**Anticipated use of proceeds, subject to actual costs and legal review:** 50% DEX liquidity, 20% network development, 10% infrastructure/security/audits and 20% founder compensation. The founder allocation is proposed to release 50% after defined sale settlement and the remainder in six equal monthly installments. These are intended budget percentages, not commitments to particular liquidity levels, deliverables, or investment outcomes; final terms must explain any administrative flexibility without misleading purchasers. Report actual USD fair values and spending. A qualified finality policy for properly completed sales may be considered, but **statutory refund, rescission and fraud remedies cannot be excluded by a no-refunds disclaimer**.

mFRG has no assured resale market, price appreciation, revenue share, 1:1 FRG redemption, or guaranteed staking reward. Future FRG staking and collateral integration remain proposed, depend on new reviewed protocols, and are not a buyer entitlement. These statements do not determine securities, money-transmission, consumer-protection or tax status; obtain qualified legal review, jurisdictional eligibility rules, disclosures and applicable registrations or exemptions **before inviting funds**. No marketing or disclaimer should imply legal immunity.
