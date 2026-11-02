# ForgeCoin pool payout journal — isolated QA only

**NOT A PRODUCTION PAYOUT SYSTEM.** This folder implements a local SQLite state-machine prototype and a read-only ForgeCoin wallet/daemon RPC verifier. It is not connected to the native pool's LMDB balances and must never receive real wallet credentials.

The native pool remains payout-disabled; compiling with FRG_TESTED_WALLET_PAYOUTS causes a deliberate fatal error. No released backend can send miner funds yet.

## Implemented and tested

- SQLite WAL with synchronous FULL; fixed genesis identity and mutually exclusive QA/production database flags.
- Immutable payout batches, exact uint64 FRG atomic values, one percent operator fee allocated in the native C pool, and separately held miner/operator credits (no pool fee for solo mining).
- Idempotent reservations that reject duplicate IDs with changed recipients, insufficient funds, and concurrent overlap; cancel ONLY before signing.
- Immutable TXID-to-signed-metadata record after a wallet signs with do_not_relay=true; signed state survives process restart.
- Rejects partial signed transaction broadcast acknowledgement, duplicate TXIDs across batches and any attempt to create a second different transaction for an already signed batch.
- Read-only RPC verifier restricts wallet/daemon URLs to local numeric loopback addresses; method whitelist permits only wallet get_transfer_by_txid and daemon get_info/get_transactions/get_block_header_by_height/get_block. No send/transfer/sign/relay RPC methods.
- Verifies exact 20261026 genesis, outgoing type, tx inclusion in canonical block, wallet and daemon height agreement, exact recipients/amounts, no pool/double-spend flags and a minimum of 20 confirmations.
- Fake-observation tests cover crashes after reserve/sign/relay/observe, duplicates and canonical reorganization evidence.

**Critical restrictions:** Production journal defaults to qa_mode=False and explicitly refuses direct synthetic balance crediting and local settlement. Synthetic credit_verified_mature_reward and commit_observed run only for QA journal identity. The boolean verified_canonical parameter is NOT actual proof: only tests supply it. Do not use this method in production. If a production verifier ever connects to a wallet, its authenticated RPC service, storage, credentials and signing keys require independent review.

Signed tx relay metadata may be operationally sensitive; QA tests use temporary disposable SQLite databases and fake metadata. Never upload a real settlement database, metadata, keys, wallet RPC password or signed transaction to GitHub. A production system would require encrypted storage, authenticated local wallet RPC and backups.

## Reproduce offline

From repository root, run:

    python -m unittest discover -s services/pool_settlement/tests -p test_*.py -v

All current tests use fake transaction hashes and simulated canonical chain observations. No actual FRG transfer, wallet key access or signing occurs.

## Unresolved release gates

1. Integrate the journal with the authoritative C pool LMDB in one atomic credit-reservation and settlement transaction; mirroring balances to another database is NOT safe.
2. Build a wallet transport that obtains signed transaction metadata without broadcasting, persists it DURABLY before any relay, then safely relays those same bytes and handles unknown responses, failure and crash recovery.
3. End-to-end test a consensus-valid block, 60+ block maturity, actual native wallet transfer, 20+ confirmations, canonical tx inclusion, reorg and independent second-node syncing on a disposable chain that cannot connect to public peers.
4. Secure operator-controlled, independently verified pool reward wallet and distinct one-percent fee wallet address. No secrets in pool configs, logs or public pages.
5. Review the payout state machine independently, implement authenticated worker settings and payout changes, recovery procedures, and only then authorize production wallet spending and signed releases.

The inherited height-zero 11.92092895 FRG output is disclosed as a fork artifact intended unspendable, but no independent cryptographic burn proof is established.
