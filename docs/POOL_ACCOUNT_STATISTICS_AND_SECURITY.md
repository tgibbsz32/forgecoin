# ForgeCoin mining pool statistics, worker accounts and payout controls

**Engineering requirements, not currently running production services.** The pool and Pool Observer pages provide detailed metric inventory and offline mining calculators. Live pool readings, login, registration, pool wallet balance adjustments, transaction signing and payout changes are disabled until the FRG-native backend is deployed, integrated and audited.

## Observability coverage

- Native network: verified genesis and latest canonical chain height/hash, synchronized status, peers, current/band difficulty, network hashrate and trend, target and observed block intervals, valid blocks, orphan/reorg counts, block reward, tails, mempool, fees, verified block age.
- Pool server: native RandomX worker count and actual socket capacity, 5m/1h/24h pool hashrates, miner account count, uptime and backend health, current round, target difficulty, accepted weighted shares, response latency, pool effort, last block, 24h/7d/30d block count, 10/50/100 confirmed block luck, orphaned pool blocks, downtime.
- Share accounting: accepted/rejected/stale/duplicate shares by 5m/24h and worker, per-worker 5m/1h/24h hashrates and share difficulty; per-worker last activity, worker online/offline status and uptime; miner contribution weights and current round eligibility.
- Monetary: reward policy and PPLNS/PROP window, current native reward, 1% actual operator fee on *eligible pooled rewards* (not consensus fee), pool immature/mature allocations, reorg reversals, unpaid balances, minimum payout and next window, pending/settled payouts, actual transaction hashes, transaction fees, worker-level history, maturity and dust handling.
- Pool Observer: solo and pool probability, mean time, expected rewards under explicit input values, finite range and monotonicity checks, normalized effort distribution and realistic uncertainty; separately label actual timestamped read-only measurements. Never display calculated expectation as actual wallet balance, worker shares or payout.

The static pages currently contain **57 detailed public metric placeholders and 22 additional observer metric placeholders** plus existing overview and calculator fields. Missing metrics display “Unavailable,” never zero or fabricated readings. Only a reviewed read-only data provider may assert the FRG mainnet identity and freshness. The public JS contract is frg-pool-stats-v1; it requires HTTPS, same-origin endpoint, exact chain identity, explicit ready/source fields and observedAt within 120 seconds. Real backend output must follow that contract.

## Account design: address + worker aliases + password + wallet proof

The user wants FRG-native addresses, workers and passwords for private dashboards and payout changes. These are valid requirements, but a **public address is not proof of ownership**. Do not enable unauthenticated address-based private data or destination changes.

1. **Enroll a payout address:** server issues a cryptographically random, one-time, short-lived challenge bound to the exact FRG address, current hostname, nonce and intent. Owner signs it through a reviewed native FRG wallet signing mechanism; verifier checks using native signature verification (not Solana or Bitcoin signature formats). Fail closed until live FRG-compatible wallet-signing verification is tested. Do not collect recovery seeds or wallet passwords on the website.
2. **Password:** owner sets a *separate pool account password* hashed with Argon2id or reviewed equivalent, with per-account salt, policy and rate limiting. No plaintext storage or credential logging. Require second-factor protection for high-impact payout changes where possible.
3. **Worker access:** register unique aliases and optional per-worker credentials/tokens; hash or safely derive pool authentication material, scope workers to one verified miner account and enforce connection quotas. Stratum accepted-share evidence, not owner self-report, determines hashrate and rewards.
4. **Session auth:** HTTPS-only Secure, HttpOnly and SameSite cookies; short session age; CSRF defenses, rotation, lockout and replay protections; no cross-origin private responses; account enumeration controls and robust failure statuses.
5. **My account dashboard:** list and detail worker names, 5m/1h/24h/7d hashrate windows, accepted/rejected/stale shares, recent job events, last-seen, downtime, share reward allocation, immature/unpaid/paid FRG, threshold, payment schedules, transaction hashes and confirmations, fees and adjustments/reorgs. Private history is never available by entering someone else's public payout address.
6. **Change payout threshold:** CSRF-protected authenticated request with enforced numeric min/max, recomputation of valid maturity/dust, cooldown and append-only audit trail. Changes must not mutate previously accrued round weights.
7. **Change payout destination:** require recent authentication, a challenge signed from the *current* payout wallet **and** a new-address control proof, challenge uniqueness, notifications when feasible, a hold period, anti-race transaction controls, rejection of in-flight payout mutation, audited approval, and explicit user review before activation. Address access alone is insufficient.
8. **Account recovery:** fresh native-wallet challenge plus cooldown and notification; no password reset just because a request names an address or worker. Operator administrative overrides require multi-approver logging.
9. **Payout signing:** isolate hot wallet daemon RPC from the frontend and public API. Treat private pool account password solely as account authentication, not wallet spending authorization. Native wallet signer must enforce caps and idempotent queued instructions, sufficient coin maturity, paid/unpaid reconciliation, reorg rollback and disaster recovery. Pool admin may freeze outgoing signing safely without changing shares.

## Operational release gates

- Native backend accepts valid PoW shares and rejects malformed, duplicate, stale, wrong-seed and wrong-difficulty submissions against an exact bound block template, with hardware-representative RandomX throughput.
- Durable share, rewards, payout and balance ledger survives restart/crash, handles chain reorgs and reverses immature/orphan rewards; confirm mature payouts to **two separately controlled test wallets** and verify exact 8-decimal integer reconciliation.
- Verify a minimum of 100 concurrent worker connections only after load testing; 100 is not a capacity claim before measurement. Publish algorithm, pool fee, final threshold, fee and PPLNS policy.
- Native signing challenge and account auth including replay/CSRF/brute-force checks, confidential dashboard access and independent wallet ownership proofs pass security review.
- Public status API and frontend gracefully handle stale/wrong-network/offline data, no fake statistic fallback, mobile/accessibility, network errors and unavailable status.
- Oracle public nginx serves static readiness only until safe Stratum/backend ready; public forge-wallet-rpc, arbitrary daemon RPC and signing interfaces must remain private. No on-chain blocks or payouts should be made before the mainnet launch freeze is formally cleared.

**Current state:** The documentation and public preview are improved. They do **not** constitute an enabled pool login, functioning payout editor or a deployed production pool.
