# ForgeCoin official native pool — operator-fee destination and accounting

**Policy: 1% of eligible official pool rewards to the separately configured operator fee wallet.** No protocol fee on solo mining, and no fee for unrelated independent pools. Prelaunch: the fee is a configured policy, not a currently operating transfer.

## Authoritative public destination

Official native FRG network, 20261026 genesis:

`YnJPKnrv2fk6MdHkvvAxDbe1L3Dv7WgtrjPBHnP3NokU1Zri6a8da9SfoDiF9SpQxP4Xn18BT2bBNLnVtCPqXTvr1UTsca4Z4`

The public address is present identically in the versioned frozen `config/mainnet.identity.json` manifest and `services/official_pool/jtgrassie/pool.conf` as `pool-fee-wallet`. The `pool-wallet` receives mined block rewards and **must be a distinct wallet**. It remains unset while the pool is launch-disabled.

A valid-looking receiving address and an earlier RPC format validation do **not** establish that anyone can spend or recover its private keys. Before turning on fee payments, the operator must prove ownership/recovery through a native wallet on the correct chain, without placing a seed, password, private key or encrypted spending wallet in the repository, log or pool website.

## Amounts and rounding

The pool stores values as integer atomic units (8 decimal places; 100,000,000 atomic units per FRG). For each eligible miner allocation:

- `fee_atomic = floor(allocation_atomic / 100)`
- `miner_net_atomic = allocation_atomic - fee_atomic`
- `miner_net_atomic + fee_atomic = allocation_atomic`

A 1.00000000 FRG pool reward allocation credits **0.99000000 FRG** to the miner and **0.01000000 FRG** to the operator-fee address. Very small allocations may round the 1% fee down by less than one atomic unit per allocation. Operator-fee credits accumulate as a separate account in the pool's LMDB payout ledger and are **not guaranteed delivered on-chain** until successful wallet transfer and independent confirmation.

The current source rejects: a missing fee wallet, a wrong-network fee wallet, a fee wallet identical to the pool reward wallet, a configured fee other than 0.01, and a PPLNS multiplier other than 2.0.

## Testing evidence and limitations

- Fixed operator fee address compared to frozen manifest in `test_pool_fee_route.py`.
- Native integer fee and PPLNS calculations tested by `test_currency.c` and `test_pplns_money.c`.
- Transfer RPC response validation tested by `test_transfer_receipt.c` and failure/atomicity source contracts by `test_payout_guards.py`.
- Native ARM64 pool links on Oracle with hardened accounting source.
- **Still missing:** actual matured canonical pool block, receipt-to-chain matching, pending/miner balance reconciliation across crashes and reorgs, end-to-end wallet payouts and verification of operator custody. Tests of arithmetic alone cannot replace those checks.

As of 2026-10-27, `disable-payouts = 1`, the separate `pool-wallet` and wallet RPC port are blank/zero, and public Stratum remains disabled. **No mining fee is currently being charged or remitted.**

*Future SPL mFRG sale/trading and Solana treasuries have their own allocations and no connection to this 1% native mining fee, unless a separately implemented and audited conversion bridge is explicitly adopted.*
