# Current ForgeCoin mainnet specification

Updated October 26, 2026. **Frozen identity; public launch is not authorized.** This is the selected new-mainnet specification, not a claim that a public network is running. The retired development chain and October 20 candidate are archive-only; balances do not automatically migrate.

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
| Desktop wallet RPC | Local protected service; distinct from ZMQ (Windows Forms uses 39483) |
| Protocol | v1 genesis, v19 from height 1 |
| Initial difficulty / minimum | 500,000 / 400,000 |
| Difficulty schedule | Fixed startup through height 15; progressive LWMA90 from height 16 |
| Coinbase maturity | 60 blocks |

## Tokenomics

50,000,000 FRG is the primary-emission reference, **not a maximum supply**. The perpetual tail reward is 0.20 FRG per 120-second block. Native block subsidies go to PoW miners; no founder/team/ICO or governance allocation is authorized. The official pool's planned 1% operator fee applies to eligible pooled rewards and is separate from transaction costs and any future voluntary treasury allocation.

For an unpenalized two-minute block, calculate in atomic units: `max((5,000,000,000,000,000 - already_generated_coins) >> 21, 20,000,000)` before adding transaction fees and applying relevant block-weight rules. With 1,192,092,895 genesis atomic units already generated, the height-1 base reward is 2,384,185,222 atomic units (23.84185222 FRG). Actual rewards follow validated consensus, not a website estimate.

**Genesis blocker:** the transaction contains 11.92092895 FRG with unlock height 60. This is a maturity lock, not proof of permanent unspendability. The zero-allocation policy does not establish a cryptographic burn. Independent proof or a separately reviewed consensus treatment remains required before launch.

## Separate Solana miniFORGE and planned protocol developments

Native FRG consensus issuance is not affected by miniFORGE (mFRG), a separate standard 6-decimal Solana SPL token with a **50M mFRG target**: **5M initial sale inventory**, **5M post-sale liquidity/staking treasury** and **40M future issuance/development treasury**. “Future issuance” means later releases of reserved mFRG units, not new minting over that target. No mainnet mFRG mint/sale allocation or public sale is independently verified ready, and there is no approved payment recipient, price or active liquidity/staking program.

The project intends to establish a governance solution **before the mFRG sale concludes**. No fixed ten-seat chamber, staking mandate or voter rights exist. Future native FRG privacy research includes a preferred in-place FCMP++/CARROT hard fork if safely implemented, plus native atomic swaps, potential L2 settlement and L3 applications. No wrapper bridge or guaranteed mFRG/FRG conversion is part of the current roadmap.

See [technical roadmap](../ROADMAP.md), [miniFORGE sale details](miniforge-sale.html), [mFRG custody/specification](MINIFORGE_SPL_TREASURIES.md) and [future privacy architecture](SOLANA_FCMP_CARROT_FUTURE_ARCHITECTURE.md).

## Source and release status

The machine-readable [documentation identity](mainnet.identity.json) mirrors the frozen manifest from new-mainnet source snapshot `62fc0b875431d7fa64f887bb20b7b51d67abcdfa` on draft PR #111. **Main still includes legacy runtime/consensus code. Updating documentation does not retarget a main-branch binary.** Do not build main and assume it implements this identity. PR #111 and #114 remain unfinished and unmerged; no public release or network activation is authorized.

Windows Forms create/restore tests were reported in MAINNET-003. Subsequent Tauri static audit, compilation and local debug installer construction passed; that installer was not installed or runtime-validated. Real solo/pool acceptance and payouts, funded transfers, clean-machine installation, ARM64 consensus agreement, security review and monitored infrastructure cutover remain release gates.

RPC and wallet control services must remain protected and local. No official public bootstrap peer or production pool is approved for this new chain. Old Oracle explorer/pool preparation pages are not evidence of new-mainnet operation. Historical reports retain the original chain parameters and test results, clearly marked as archives.
