# ForgeCoin Technical and Economic Whitepaper

Version 0.1 - September 2026

## Abstract

ForgeCoin is a privacy-preserving, proof-of-work digital currency derived from Monero v0.18.5.1. It combines private-by-default transactions, RandomX CPU mining, independent full-node validation, and a desktop application with a local blockchain explorer. The network is designed so users can validate balances, blocks, transactions, and consensus rules without trusting a hosted website.

ForgeCoin is presently in its bootstrap stage. The chain is operational, but security depends on attracting independent nodes and miners, distributing hash power across operators, reviewing the forked source, and maintaining a transparent release process.

## Mission

ForgeCoin aims to provide private, CPU-accessible peer-to-peer digital cash that people can validate, mine, and explore on their own computers without relying on a central custodian or hosted block-explorer website.

The project follows four operating principles:

1. Users should be able to verify the chain with their own node.
2. Transaction privacy should be the default rather than an optional feature.
3. Mining should remain accessible on commodity CPUs through RandomX.
4. Consensus changes should be published in source, reviewed publicly, and activated only through a clearly announced network upgrade.

## Architecture

ForgeCoin uses a CryptoNote-derived transaction model and Monero's version 16 consensus feature set from block height 1. The inherited technology includes RingCT confidential amounts, CLSAG signatures, Bulletproofs+, view tags, stealth addressing, and a fixed ring size of 16 under version 16 rules.

Full nodes verify every accepted block and transaction. Miners select valid transactions, perform RandomX proof of work, and extend the chain with the greatest cumulative difficulty. A miner with majority hash power can reorganize recent blocks or censor transactions, but it cannot create rewards or transactions that violate the rules enforced by honest full nodes.

## Network identity

| Item | Mainnet value |
| --- | --- |
| Network name | ForgeCoin |
| Currency symbol | FRG |
| Address prefixes | 90 standard, 91 integrated, 92 subaddress |
| P2P port | 19480 TCP |
| RPC port | 19481 TCP |
| Network UUID | `388dca1c-ba93-41d9-9641-8a012126310c` |
| Genesis nonce | 10000 |
| Genesis hash | `a9651ecf2aec7c92443e7e7e8bfd4c6e6d5de3de8a52c04f9a98274d5031f9b9` |
| Consensus version | v1 at genesis, v16 from height 1 |

Changing the genesis transaction or network UUID would create a different network. Ordinary application, seed-node, packaging, and user-interface updates do not require a chain restart.

## Proof of work and difficulty

ForgeCoin uses RandomX proof of work. RandomX is designed to favor general-purpose CPUs and reduce the advantage of specialized mining hardware. It does not guarantee equal participation: large CPU farms, botnets, cloud resources, or a dominant pool can still acquire substantial hash power.

The target interval is 120 seconds. Difficulty is recalculated from recent block timestamps and cumulative work using a configured 720-block window. Users do not manually set the current network difficulty. Changing the target interval, window, or difficulty algorithm is a consensus change and requires a coordinated network upgrade.

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

The source code cannot establish who, if anyone, controls the private key corresponding to the genesis output. The project should publicly document whether that output is spendable and its intended treatment before seeking exchange listing or material outside investment.

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

The ForgeCoin desktop application includes an explorer that reads from the daemon on `127.0.0.1`. Each full-node user can inspect recent blocks and look up a block height, block hash, or transaction identifier without depending on a project website. Synchronized nodes should converge on the same valid chain. During a temporary network split, each explorer displays the chain currently accepted by its own node.

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

## Disclaimer

This document describes software behavior and project intent. It is not a promise of value, investment return, anonymity, uninterrupted operation, or regulatory treatment. Network participants are responsible for evaluating software, operational, legal, and financial risk.
