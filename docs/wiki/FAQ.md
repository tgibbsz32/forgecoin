> **Current specification — 2026-10-26:** [Frozen mainnet parameters, tokenomics and release status](../CURRENT_MAINNET.md). Public launch is not authorized. Main-branch executables still implement legacy rules; these instructions are not proof of new-mainnet compatibility.

# ForgeCoin FAQ

### Is ForgeCoin's new mainnet live?

**No.** An older development chain/explorer has been running and a separate fresh-mainnet candidate has isolated test evidence. The old daemon may report `nettype=mainnet`, but that does not mean a new approved launch occurred. See [status](Current-Status.md).

### Can I download a tested Windows wallet and mine today?

The Tauri app and mining controls exist in source, but initial Solo-and-Pool acceptance and reviewed distribution artifacts remain blocked. Do not interpret a GitHub source checkout, PE-header check, or a “mining started” UI state as release validation.

### Is there an official ForgeCoin mining pool?

**No production pool is accepting public shares or paying miners.** The [pool page](https://150.136.209.227/pool/) is a static readiness page. The research listener uses fixed synthetic work, loopback sockets and an explicitly uncredited journal.

### How are new FRG coins planned to be issued?

The current *proposed fresh-mainnet* policy is no founder/team/ICO premine, 100% of block subsidies paid to PoW miners, a primary emission **reference** of 50M FRG, and a continuing **0.20 FRG tail reward per block**. Because the tail is perpetual, do **not** advertise an absolute capped supply. These rules require final audited candidate verification.

### What are the difficulty and block-time targets?

The design uses a two-minute block target, proposed **500,000** starting difficulty and **400,000** floor with an LWMA90 bootstrap plan. These should not be confused with the old development-chain hardfork heights; publication does not mean activation.

### Is the operator pool fee 1%?

**Planned only:** the future official pool proposes a 1% fee on eligible pooled rewards, separate from transaction/payout costs and any third-party miner donation policies. Solo mining has no project pool operator fee. No fee is being collected by the synthetic test listener.

### How does miniFORGE (mFRG) relate to native FRG?

Native FRG is an independent, privacy-focused Proof-of-Work network. The **separate** miniFORGE (mFRG) Solana SPL token has a revised **500M intended fixed supply** across nine categories: 50M staged cryptocurrency fundraising, 100M operations, 100M ecosystem, 85M finite staking rewards, 60M liquidity, 65M engineering/security, **15M immediately unlocked founder allocation** and **15M team-labeled allocation vested in months 13–36 for the same founder**, and 10M emergency. No sale, mainnet mint verification, liquidity or staking is active. See [lifetime policy](../MFRG_LIFETIME_TOKENOMICS_500M.md).

### Has a governance system been selected?

No. The former fixed-size representative chamber is no longer the current governance design. The project intends to choose and publish a solution **before any authorized mFRG distribution begins**. There are no binding voter rights, FRG governance-bond contracts, staking rewards, or treasury elections in production.
