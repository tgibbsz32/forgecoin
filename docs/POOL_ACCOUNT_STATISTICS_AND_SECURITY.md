# ForgeCoin mining pool statistics and public address lookup

**Engineering requirements, not currently running production services.** The pool and Pool Observer pages provide detailed metric inventory and offline mining calculators. Live pool readings, payout changes, transaction signing and account administration are disabled until the FRG-native backend is deployed, integrated and audited.

## Observability coverage

- Native network: verified genesis and latest canonical chain height/hash, synchronized status, peers, current/band difficulty, network hashrate and trend, target and observed block intervals, valid blocks, orphan/reorg counts, block reward, tails, mempool, fees, verified block age.
- Pool server: native RandomX worker count and actual socket capacity, 5m/1h/24h pool hashrates, miner account count, uptime and backend health, current round, target difficulty, accepted weighted shares, response latency, pool effort, last block, 24h/7d/30d block count, 10/50/100 confirmed block luck, orphaned pool blocks, downtime.
- Share accounting: accepted/rejected/stale/duplicate shares by 5m/24h and worker, per-worker 5m/1h/24h hashrates and share difficulty; per-worker last activity, worker online/offline status and uptime; miner contribution weights and current round eligibility.
- Monetary: reward policy and PPLNS/PROP window, current native reward, 1% actual operator fee on *eligible pooled rewards* (not consensus fee), pool immature/mature allocations, reorg reversals, unpaid balances, minimum payout and next window, pending/settled payouts, actual transaction hashes, transaction fees, worker-level history, maturity and dust handling.
- Pool Observer: solo and pool probability, mean time, expected rewards under explicit input values, finite range and monotonicity checks, normalized effort distribution and realistic uncertainty; separately label actual timestamped read-only measurements. Never display calculated expectation as actual wallet balance, worker shares or payout.

The static pages currently contain **57 detailed public metric placeholders and 22 additional observer metric placeholders** plus existing overview and calculator fields. Missing metrics display “Unavailable,” never zero or fabricated readings. Only a reviewed read-only data provider may assert the FRG mainnet identity and freshness. The public JS contract is frg-pool-stats-v1; it requires HTTPS, same-origin endpoint, exact chain identity, explicit ready/source fields and observedAt within 120 seconds. Real backend output must follow that contract.

## Public-address mining statistics — no account required

**Product decision:** Miners and visitors may look up a miner's read-only pool statistics simply by entering the public native FRG payout address used for mining. No registration, login, password, wallet signature, membership status or identity verification is required to **view** these records. The public address is a lookup key, not authentication or proof of wallet ownership.

The read-only address lookup should show, where the verified backend supports it: 5m/1h/24h hashrate, workers and last-seen status, accepted/rejected/stale shares, round contribution, immature/unpaid/paid FRG, confirmed payout transactions, payout history and next estimated payout. Mark unsupported or unavailable values clearly; never fabricate balances or shares.

**Privacy:** Anyone who knows an address can see the statistics published for that address. Do not publish IP addresses, worker passwords, session tokens, private keys, wallet seeds, view keys or internal operator records. Worker aliases may reveal information, so consider masking aliases or allowing privacy-preserving worker labels. Rate-limit queries and avoid unnecessary logging of searched addresses.

**Security boundary:** Public lookup must be read-only and must not permit changing payout destinations, payout thresholds or account configuration. Any future sensitive modification requires separate wallet-control verification and a reviewed authorization workflow. The user does not need such a workflow merely to view mining statistics.

**Deployment gate:** The current public website and preview bridge do not expose a verified native FRG per-address statistics API. Implement and test the pool-side address-indexed read-only API, FRG amount conversion, payout reconciliation, data freshness, CORS/HTTPS, input validation and rate limiting before enabling live results. Never proxy unaudited `miner_balance` values or imply that a public address can authorize payout changes.

## Operational release gates

- Native backend accepts valid PoW shares and rejects malformed, duplicate, stale, wrong-seed and wrong-difficulty submissions against an exact bound block template, with hardware-representative RandomX throughput.
- Durable share, rewards, payout and balance ledger survives restart/crash, handles chain reorgs and reverses immature/orphan rewards; confirm mature payouts to **two separately controlled test wallets** and verify exact 8-decimal integer reconciliation.
- Verify a minimum of 100 concurrent worker connections only after load testing; 100 is not a capacity claim before measurement. Publish algorithm, pool fee, final threshold, fee and PPLNS policy.
- Native signing challenge and account auth including replay/CSRF/brute-force checks, confidential dashboard access and independent wallet ownership proofs pass security review.
- Public status API and frontend gracefully handle stale/wrong-network/offline data, no fake statistic fallback, mobile/accessibility, network errors and unavailable status.
- Oracle public nginx serves static readiness only until safe Stratum/backend ready; public forge-wallet-rpc, arbitrary daemon RPC and signing interfaces must remain private. No on-chain blocks or payouts should be made before the mainnet launch freeze is formally cleared.

**Current state:** The documentation and public preview are improved. They do **not** constitute an enabled pool login, functioning payout editor or a deployed production pool.
