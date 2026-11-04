# Current ForgeCoin mainnet specification

Identity selected October 26, 2026; consensus source merged November 4, 2026. **Frozen identity; public launch is not authorized.** This is the selected new-mainnet specification, not a claim that a public network is running. The retired development chain and October 20 candidate are archive-only; balances do not automatically migrate.

## Network identity

| Parameter | Frozen value |
| --- | --- |
| Native asset / decimals | FRG / 8 (100,000,000 atomic units per FRG) |
| Proof of work / target | RandomX / 120 seconds |
| Genesis nonce | 20261026 |
| Genesis hash | `4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c` |
| Network UUID | `bd936359-09e4-4fdb-8ec0-12fa9d6ef090` |
| Standard / integrated / subaddress prefixes | 190 / 191 / 192 |
| P2P / daemon RPC / ZMQ RPC | 39480 / 39481 / 39482 |
| Desktop local services | Windows Forms wallet RPC **127.0.0.1:39484**; XMRig statistics API **127.0.0.1:39483**; Tauri wallet RPC uses a separate dynamic localhost port. Neither is native ZMQ. |
| Protocol | v1 genesis, v19 from height 1 |
| Initial difficulty / minimum | 500,000 / 400,000 |
| Difficulty schedule | Fixed startup through height 15; progressive LWMA90 from height 16 |
| Coinbase maturity | 60 blocks |

For all selected network-service defaults, local-only exposure rules, retired endpoints and staged deployment gates, use the [network port contract](NETWORK_PORTS.md). **The presence of configured ports is not evidence of live mainnet services.**

## Tokenomics

50,000,000 FRG is the primary-emission reference, **not a maximum supply**. The perpetual tail reward is 0.20 FRG per 120-second block. Native block subsidies go to PoW miners; no founder/team/ICO or governance allocation is authorized. The official pool's planned 1% operator fee applies to eligible pooled rewards and is separate from transaction costs and any future voluntary treasury allocation.

For an unpenalized two-minute block, calculate in atomic units: `max((5,000,000,000,000,000 - already_generated_coins) >> 21, 20,000,000)` before adding transaction fees and applying relevant block-weight rules. With 1,192,092,895 genesis atomic units already generated, the height-1 base reward is 2,384,185,222 atomic units (23.84185222 FRG). Actual rewards follow validated consensus, not a website estimate.

**Genesis blocker:** the transaction contains 11.92092895 FRG with unlock height 60. This is a maturity lock, not proof of permanent unspendability. The zero-allocation policy does not establish a cryptographic burn. Independent proof or a separately reviewed consensus treatment remains required before launch.

## Separate Solana miniFORGE and planned protocol developments

Native FRG consensus issuance is independent of miniFORGE (mFRG). Native FRG mining and public launch are planned to precede any mFRG deployment. mFRG is a separate proposed standard six-decimal Solana SPL token with a **50,000,000 mFRG fixed-supply target**: 5M initial presale, 5M future liquidity and 40M combined ecosystem/staking/collateral reserve. The proposed flat presale price is $0.12 per mFRG; proposed gross sale proceeds are 90% project and 10% founders, with half the founder share immediately and half released over six months. There is no separate founder token allocation. No mFRG mint, sale or staking program is authorized; see [current mFRG policy](MFRG_50M_CITY_TOKENOMICS.md).

The project intends to determine and publish governance procedures **before mFRG is introduced, minted, bridged, staked, sold or distributed**. No fixed ten-seat chamber, staking mandate or voter rights exist. The intended later mFRG utility is a fully reserved **1 native FRG : 1 eligible mFRG bridge**, faster Solana transfers, supported DEX liquidity/trades, optional finite-reserve staking and optional mFRG payments for USD-priced CITY packs in ForgeCoin's planned Discover Your City game. Every mFRG presented as FRG-redeemable requires one independently verifiable native FRG reserve, including presale/DEX/staking inventory represented as backed. The proposed 50M mFRG ceiling limits bridge capacity despite perpetual FRG tail emission; conversion is not a guaranteed market-price peg. No bridge, reserves, redemption, DEX market, staking or game checkout is live. Future native privacy research includes a preferred in-place FCMP++/CARROT hard fork if safely implemented, plus native atomic swaps, potential L2 settlement and L3 applications.

See [technical roadmap](../ROADMAP.md), [miniFORGE sale details](miniforge-sale.html), [mFRG custody/specification](MINIFORGE_SPL_TREASURIES.md) and [future privacy architecture](SOLANA_FCMP_CARROT_FUTURE_ARCHITECTURE.md).

## Potential future Tari and Monero merged-mining integrations (not approved)

The selected and unlaunched FRG mainnet remains **independent RandomX PoW**. Neither merged-mining mode is implemented, promised, or part of the frozen genesis/launch rules.

- **Tari + FRG:** study FRG as a *parent* and Tari as an auxiliary chain, using a patched Tari proxy and FRG's Monero-derived templates on an isolated test network. Tari must independently accept the proof structure and parent RandomX seed. If successful, FRG miners might also compete for Tari rewards; this does not automatically increase FRG's security or attach Monero hashrate.
- **XMR + FRG:** study Monero as a *parent* and FRG as an auxiliary chain using a newly reviewed FRG AuxPoW consensus path. Actual adoption by independent Monero miners and pools—not protocol compatibility alone—would determine possible security benefits. This is **consensus-changing** and would require a separately approved hard fork, full tests and external review.

Early low-hashrate 51% risks are instead addressed first through diversified mining and peers, independently monitored chain tips/reorganizations, conservative settlement confirmations, and persistent pool payout holds. These controls detect or limit loss; **they do not make a majority-hashpower attack impossible**. See [security research and engineering gates](SECURITY_51_PERCENT_AND_TARI_MERGE_MINING_2026-11-02.md).

## Source and release status

**Current status, November 4:** Following owner approval of the numeric parameters, [consensus PR #185](https://github.com/tgibbsz32/forgecoin/pull/185) **merged into source `main` at `b2afc6047db6a229cc0e780efc67cf916b2957ae`**, retaining a compile-time mainnet mining/block-acceptance lock. All seven required PR CI workflows passed, including native x86_64/ARM64 daemon builds, mainnet mining refusal, loopback peer acceptance, frozen difficulty policies and isolated regtest reorganization. No Oracle node, public Stratum, pool payout, owner wallet or public mining service was started. **`release_authorized=false`, `pool.stratum_public=false` and `pool.payouts_enabled=false` remain unchanged.** Code integration is **not** permission to activate mainnet.

The [public-release readiness matrix](RELEASE_READINESS_2026-11-04.md) records separate isolated FAKECHAIN accepted Stratum blocks, matured 1% pool accounting, reorg quarantine, native signed wallet transfer and separate-recipient confirmation. These tests do not establish final MAINNET payout signing or an independently audited launch. [Test-only wallet PR #203](https://github.com/tgibbsz32/forgecoin/pull/203) remains isolated, and signed adversarial genesis-spend rejection, independently operated mainnet peer agreement, Windows/Android installer acceptance and production deployment approval remain explicit release prerequisites.

The machine-readable [documentation identity](mainnet.identity.json) and `config/mainnet.identity.json` now match the frozen source consensus on `main` (same nonce, network UUID, genesis hash and ports). Prior draft PRs #111/#114 remain historical, not the current consensus source of truth. **Never run a mainnet node from this prelaunch-locked source as a production service or attempt to bypass its restrictions.**

Windows Forms create/restore tests were reported in MAINNET-003. Subsequent Tauri static audit, compilation and local debug installer construction passed; that installer was not installed or runtime-validated. Real solo/pool acceptance and payouts, funded transfers, clean-machine installation, ARM64 consensus agreement, security review and monitored infrastructure cutover remain release gates.

RPC and wallet control services must remain protected and local. No official public bootstrap peer or production pool is approved for this new chain. Old Oracle explorer/pool preparation pages are not evidence of new-mainnet operation. Historical reports retain the original chain parameters and test results, clearly marked as archives.
