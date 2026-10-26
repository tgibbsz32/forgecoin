> **Historical archive — superseded for current configuration.** Original evidence and decisions below retain their original dates and network parameters. Do not use old ports, genesis, balances, token proposals or release claims as current instructions. See [current mainnet specification](CURRENT_MAINNET.md) and the current roadmap.

# Oracle FRG pool continuation — 2026-10-25

## Current authorization and boundaries

The user authorizes Oracle VM setup, public website/pool preparation and public
testing, replacing the earlier blanket no-public-network restriction. They
explicitly prohibit initiating the new mainnet or premining coins. Do not start
mining, submit blocks, initialize a new chain, change genesis, or enable payouts.
Use synthetic work for initial verification; it creates no chain or coins.
The user identified the existing height-519 chain as the OLD network. They
authorize retiring it when prudent. Preserve a recoverable backup first. Do not
stop it merely because it is old; remove dependencies and preserve rollback first.
No main-branch merge is authorized. Continue review branches and draft PRs.
After EACH completed stage, append an evidence-backed handoff here and refresh
the user-facing copy in the current chat outputs directory.

## Stage 0 completed: access recovered and read-only VM inventory

- Repository: tgibbsz32/forgecoin.
- Checkout: C:\Users\tgibb\Documents\Codex\2026-10-25\referenced-chatgpt-conversation-this-is-an\work\forgecoin
- Branch: codex/mining-preflight-pe-validation; pushed HEAD 0c4be4cae29931d086d3ad2043491d9eb731edb7.
- Draft PR: https://github.com/tgibbsz32/forgecoin/pull/92 . Prior PR 91 was already merged before this session.
- Existing untracked build-disposable/ is native build output: never add binaries.
- Oracle SSH: ubuntu@150.136.209.227. Hostname foregcon-vnic; aarch64.
- Existing key: C:\Users\tgibb\.ssh\oracle_forgecoin.key . Never print, copy into deliverables, or commit key material.
- Use BatchMode=yes, StrictHostKeyChecking=yes, ConnectTimeout=12. Existing known-host verification succeeded.
- Oracle identity URL supplied by user is a sign-in endpoint, not the pool hostname.
- VM observed: 11 GiB RAM, approximately 10 GiB available; 45 GiB root disk, 39 GiB free; zero load. These are observations, not quota/capacity guarantees.
- Active services: forgecoin, forgecoin-explorer, nginx and explorer firewall units.
- Existing daemon: /home/ubuntu/blockchain/forgecoin/build/arm64-release/bin/forged,
  data /home/ubuntu/forgecoin-test-data. P2P public 19480; RPC 127.0.0.1:19481;
  ZMQ 127.0.0.1:19482. No change made.
- get_info: height 519, nettype mainnet, difficulty 500000, peers 0,
  synchronized false. Tip 484316a1ff2e221849be859130c8a88f1e8b6212f19947e442a1aca7b2cf31e5.
  User confirms this is the OLD network; mainnet flag alone does not identify the future launch network.
- mining_status: active false, speed 0, threads_count 0.
- Explorer: 127.0.0.1:19800; /opt/forgecoin-explorer and /home/ubuntu/explorer.
- nginx listens 80/443; proxies explorer; ACME root /var/www/html;
  existing TLS certificate /etc/letsencrypt/live/150.136.209.227/fullchain.pem.
- /home/ubuntu/forgecoin-mainnet-staging contains source/build/smoke and candidate
  service files. Do not run any of them. A file/directory name is not authorization.
- No server changes, process starts, mining, chain initialization or coins created.

## Earlier engineering evidence and remaining work

See DESKTOP_MINING_PREFLIGHT_2026-10-25.md for exact native artifact digests,
MinGW build provenance and nine system DLL imports. Sidecar staging is digest
pinned; Windows Cargo and development staging refuse unreviewed artifacts.
Four Rust tests and nineteen Python tests passed; two process-launching Rust
tests remained ignored. Nine evidence controls passed. The ignored mining test
requires an externally-enforced egress acknowledgement; that is NOT enforcement.

XMRig candidate supplied by user:
C:\Users\tgibb\Downloads\xmrig-6.26.0-windows-x64\xmrig.exe
SHA256 6fa80698d7268f6e88aa88c06fb27ee99e1bcee747c2e76911e6206a5b1aeeb3.
Read-only x64 PE inspection passed; imports list only Windows system DLLs.
Its sibling downloaded ZIP has SHA256
99fe357f055577123c395b323d585b4ede8a326210b75fc73a47b88cc919e524,
which differs from upstream's v6.26.0 windows-x64 ZIP checksum
bba8097cb37d9b458a1cb1137876b27cde6740d17fe4ccbc086ba07d87d9e147.
Its executable matches that ZIP's executable; official provenance remains unverified.
Do not launch its existing scripts/config or WinRing0 driver. No miner was run.
For a controlled build fetch pinned upstream SOURCE, not binaries. Upstream
donation is not disabled by config zero; source policy and OS isolation matter.
Sources: https://github.com/xmrig/xmrig/releases/tag/v6.26.0 and https://xmrig.com/docs/miner .

services/pool_research is experimental offline code, NOT a deployable pool.
There is no verified production Stratum listener/payout pipeline. Mock Pool
acknowledgement does not validate RandomX. A native offline reference harness
exists in services/pool_research/tests; synthetic verification is allowed and
must not be described as actual accepted chain blocks or credited rewards.

## Next stages

1. Inspect existing nginx/explorer configuration and stage a separate honest
   pool-readiness website without changing the node or exposing its RPC.
2. Verify and deploy static pages on Oracle with a reversible nginx change,
   preserving explorer and ACME. Clearly label pool/mining/payouts unavailable.
3. Build native synthetic-work verification and real listener/accounting guards.
   Keep daemon block submission and payout connections absent/disabled.
4. Retire the old network only after dependency review and verified backup.
5. New-mainnet launch and coin-producing tests require separate authorization.

## Stage 1 completed: native ARM64 synthetic-work verification

2026-10-25, Oracle work directory /home/ubuntu/pool-preparation/20261025-native.
Copied only the offline adapter/bound-job dependencies and native reference
source/harness; no daemon or wallet was copied or launched. Compiled with g++
-std=c++17 -O2 against the existing development RandomX header/static library.

- Existing library SHA256: 5826e9ff627150c8565b6b1a2f1696250b23306122e794bc6430a9ba8356f18a.
- Header SHA256: 3187bf9ce958da3c2333a5dbc281340e5008ddd8a5811356032427a1d6ba845d.
- Reference source SHA256: d82b7ec64a5617bf16e38239c1aa96b6c2b1b54859b1b786aafccbfe5cab3647.
- Built reference executable SHA256: 14d500e51085622e44d5b840d727d7964c25d76291b2d6fc5f5c513564322781.
- compare_randomx_reference: expected vector and input-mutation check passed.
- Extended run_bound_native_offline: known vector passed; real native digest
  met difficulty-one threshold as UNcredited work; fixed work failed the maximum
  difficulty threshold; duplicate, stale, malformed and unknown submissions
  rejected before hash callback. Existing difficulty-500000 case: LOW_DIFFICULTY.
- Local adapter/bound-job regressions: 13 tests passed.
- Post-check daemon mining_status remains active=false, speed=0, threads=0.

Reproduce from that VM work directory:

```sh
python3 -m services.pool_research.tests.compare_randomx_reference --source-root /home/ubuntu/blockchain/forgecoin --library /home/ubuntu/blockchain/forgecoin/build/arm64-release/external/randomx/librandomx.a
python3 -m services.pool_research.tests.run_bound_native_offline --executable ./randomx_reference
```

Scope: synthetic fixed work and existing development library, NOT an independent
source attestation, live Stratum/miner integration, new-mainnet compatibility,
accepted chain block, credited share, production throughput, or payout proof.
No nonce search, chain initialization, block submission, coin creation, new
service or public listening port. Existing chain and explorer remain unchanged.
Next: complete/evaluate static pool preparation page, then reversible /pool/
deployment preserving existing explorer routes, ACME and disabled mining.

## Stage 2 completed: Oracle preparation website published

Public URL: https://150.136.209.227/pool/ . This is a preparation/readiness
website, NOT a functioning mining pool or live hashrate/payout dashboard.
Source: apps/pool-site/ . Exact authentic logo preserved. No JavaScript, external
font/image requests, analytics, forms, wallet inputs, API polling or connect/mining
controls. Explicitly labels old network, new-mainnet non-launch, disabled mining,
block submission and payouts; planned 1% fee is not represented as active charging.

Independent design review: PASS. Desktop browser and overflow checks passed.
Exact mobile/tablet pixel screenshots were unavailable in the browser control
surface; responsive CSS reviewed. No different-provider evaluator was available;
review was performed by a separate agent on the inherited model. No such limits
are evidence of a failed functional test; mobile visual QA remains outstanding.

Deployment helper: apps/pool-site-deploy.sh, Oracle-only, root via sudo.
It admits only static file extensions, refuses symlinks, validates existing nginx,
backs up its configuration, adds /pool/ routes to both existing HTTP/HTTPS server
blocks, validates/reloads nginx and checks assets/explorer. It never starts or
configures a miner, node or wallet. Existing explorer/ACME routes are preserved.
The first attempt failed its immediate route check and restored the original
configuration automatically. Inspection showed correct files/permissions; the
second attempt added a bounded readiness wait for graceful nginx worker turnover
and succeeded. Old failed v1 release/backup are retained for audit; do not mistake
their existence for the active deployment.

- Active release: /opt/forgecoin-pool/releases/preparation-20261025-v2/pool/ .
- Backup: /var/backups/forgecoin-pool/preparation-20261025-v2/nginx.conf .
- Staged source: /home/ubuntu/pool-preparation/site-20261025-v1/ .
- HTML SHA256 b953328f993725fa8ae69372edf881d90a4121fa73c09487bf821432e829a8c7.
- CSS SHA256 8a8eb25a481793f6527566b13c697791f31917423df786dcd08a476ebb85fcca.
- Logo SHA256 fd4aede81c6b50e78449722ba584e7cd3e0b94d4186e1ed7fc46fa938aca5a25.
- External HTTPS page/CSS/logo: HTTP 200; downloaded public HTML hash matches source.
- External POST /pool/: 405; old explorer root: 200.
- nginx -t passed; forgecoin, forgecoin-explorer and nginx remain active.
- Both forgecoin-mainnet-staging and forgecoin-mainnet-explorer-staging inactive.
- Daemon mining_status: active false, speed 0, threads 0; listening ports unchanged.
- No new chain, genesis change, block submission, premine or payout occurred.

Rollback (via the already verified SSH connection):

```sh
sudo cp -a /var/backups/forgecoin-pool/preparation-20261025-v2/nginx.conf /etc/nginx/sites-available/forgecoin-explorer
sudo nginx -t && sudo systemctl reload nginx
```

This restores the earlier explorer-only routing; static files can remain inert.
The helper intentionally refuses an already installed /pool/ route; future
updates must inspect/replace only that root rather than rerun initial install.
Old chain retirement is authorized but deferred while the old explorer remains
useful. No old-chain deletion or backup is claimed; take a consistent backup
and handle explorer dependencies before retiring it.

## Resume after stage 2

The pool website is published and native synthetic-work checks now execute on
Oracle ARM64. There is still no deployed Stratum listener or production accounting
service. Next implement bounded synthetic Stratum integration with the native
verifier, unique worker/job assignment, difficulty/duplicate/stale checks and
durable share bookkeeping. Keep chain submission and wallet/payout integrations
absent/disabled; never connect it to the old node as the future mainnet. Validate
timeouts, overload, restart and per-worker isolation before any miner-facing beta.
Trusted XMRig source build remains needed for later controlled client integration;
do not use the unverified download scripts. Actual coin-producing tests and new
mainnet launch remain outside current authorization. Append the next stage result
here, refresh the user-facing outputs handoff and push the review branch.

## Stage 3 completed: loopback native-verifying synthetic listener

Implemented services/pool_research/synthetic_listener.py and socket integration
tests. The listener binds ONLY 127.0.0.1 on an ephemeral port, serves distinct
synthetic work/session tokens per connection, and uses BoundJobVerifier plus
NativeRandomXAdapter. It compares miner-claimed digests against its own native
hash. A successful synthetic check is explicitly uncredited, never status OK
or a claimed accepted block. It has no chain/node/wallet/submission endpoints,
never searches nonces, and is NOT a miner-facing production pool.

Bounds: four default sessions (max eight), one verifier call at a time with
immediate busy rejection and no queued nonce consumption, 4096-byte frames,
32 requests per connection (max64), 10-second idle timeout, 60-second job TTL.
Login strings are unauthenticated labels. Session/job state is memory-only.
Subprocess-per-hash verification is for integration evidence, not throughput.

Tests: eight local socket tests with explicitly fake digest callbacks passed;
the same eight tests on Oracle ARM64 with the real native reference executable
passed in 16.151 seconds. They cover threshold success/uncredited, duplicate,
digest mismatch, cross-worker/session/job isolation, stale/malformed work,
low difficulty, verifier failure, capacity/idle cleanup, oversized frames,
request limits, login ordering, duplicate request IDs and busy retry without
nonce consumption. Eighteen existing protocol/bound-job/adapter tests passed.

Remote source lives under /home/ubuntu/pool-preparation/20261025-native/services/
pool_research. Tests create/close listeners within their process. No systemd
service was installed and no pool listener remains running. No public ingress,
daemon configuration, mainnet staging or payout settings were changed.
This is native hash verification over real loopback sockets with SYNTHETIC jobs,
not an XMRig compatibility result, real FRG block-template validation, public
Stratum acceptance, restart-safe credits, payout proof or production load result.

Reproduce native socket checks on Oracle from the stage-1 work directory:

```sh
FORGE_SYNTHETIC_NATIVE=/home/ubuntu/pool-preparation/20261025-native/randomx_reference python3 -m unittest services.pool_research.test_synthetic_listener -v
```

Next: add bounded durable synthetic-verification records/restart checks without
balances or spending authority, then a reviewed persistent native verifier and
trusted-source client compatibility harness. Keep the new-mainnet no-launch and
no-premine boundaries. Website continues to say share verification is in
development, which is accurate: full pool/client/accounting integration is absent.

## Stage 4 completed: durable synthetic verification records and restart checks

Added synthetic_journal.py and integrated mandatory journal writes into the
loopback listener. A synthetic success response now requires a committed record
and includes recorded=true, synthetic=true, credited=false. Jobs still use fixed
test nonces; there is no mining search, daemon, block submission or wallet.

SQLite stores job+nonce, session token, computed digest, difficulty, hashing-blob
SHA256, seed and timestamp, with synthetic=1/credited=0 constraints. No login,
password, wallet address, balances or reward claims are stored. Duplicate
identical evidence is idempotent; conflicting evidence is refused. Transactions
use FULL synchronous/DELETE journaling, 100 ms lock wait, 10,000-record maximum
and 16,384-page ceiling. Unrelated existing databases are rejected untouched.
Use private research paths: this is not a hostile-filesystem defense or
tamper-proof/independently attested audit system.

On restart, evidence persists but old live jobs/session tokens are not restored;
old jobs are rejected and clients receive new synthetic work. Journal failure
does not return success. Such failure can consume a live in-memory nonce; there
are no earnings to recover. A commit can precede a lost network response, so
these records are not a production exactly-once crediting guarantee. Expiry is
checked again after native hashing, before recording a result.

Validation:

- 35 local tests passed (journal, socket, protocol, bound-job and native adapter),
  with ResourceWarnings enabled as errors. Local socket hashes explicitly fake.
- 17 Oracle ARM64 journal/socket tests passed in 41.092 seconds using the real
  native RandomX reference executable for socket checks.
- Includes reopen/dedup/conflict tests, schema refusal of credited=1, invalid
  inputs, capacity, locked/read-only storage, unrelated-database preservation,
  abrupt child-process exit before commit and SQLite integrity recovery.
- Socket tests confirm records survive listener restart, old jobs cannot replay,
  no success on failed/full storage, and no recording if work expires mid-hash.
- Initial local cleanup test leaked its fixture connection; corrected explicit
  close and the final run passed. Initial native expiry test counted client hash
  time incorrectly; adjusted deadline to exercise expiry during server hashing.
  Neither failed test was treated as acceptance evidence.
- New-mainnet staging services remained inactive; daemon mining active=false,
  speed=0/threads=0; public preparation site HTTPS remained 200. No production
  data directory, chain configuration, nginx route or payout setting changed.

Remote sources remain under /home/ubuntu/pool-preparation/20261025-native . Tests
use disposable databases and clean them up; no listener service or live database
was deployed. CLI now requires --journal /private/research/checks.sqlite in
addition to --executable. The listener's caller owns the journal lifecycle.

Reproduce Oracle checks from that work directory:

```sh
FORGE_SYNTHETIC_NATIVE=/home/ubuntu/pool-preparation/20261025-native/randomx_reference python3 -W error::ResourceWarning -m unittest services.pool_research.test_synthetic_journal services.pool_research.test_synthetic_listener -v
```

This validates process-exit rollback, not hardware power-loss resilience or
production accounting. Full share accounting/reorg maturity, public listener
hardening, persistent native verifier throughput and trusted-source XMRig
compatibility remain unfinished. Next stage: replace subprocess-per-hash with
a bounded persistent native verifier and test crash/timeout recovery, retaining
the synthetic-only boundary. Do not enable new-mainnet or coin-producing work.
Append subsequent stage evidence and refresh this chat's outputs handoff.

## Stage 5 completed: persistent native verification worker

Added tests/randomx_worker.cpp and persistent_randomx.py. The C++ helper reuses
one default/light-mode cache and VM per seed, reinitializes on seed changes and
exits after 64 requests. It accepts only bounded tagged lines, rejects malformed
or out-of-order input, and never searches nonces or contacts a network/chain.
Parent adapter validates request/response association, bounds response reads,
and enforces a write+read deadline through a bounded exchange thread. Only one
request is permitted at a time. Errors discard/reap the worker, never silently
retry the failed request; later explicit requests may start a fresh worker.
Cleanup failure disables the adapter. Windows helpers use CREATE_NO_WINDOW.

Listener CLI now uses this protocol by default. --one-shot-reference explicitly
selects the old reference protocol for diagnostics. Both require an explicit
trusted executable and --journal path; no compilation/download happens at runtime.
The listener still binds only loopback and records synthetic/uncredited evidence
before success. Journal/session ownership and no-mainnet/no-coins boundaries
are unchanged. None of this is a production sandbox or verified public capacity.

Oracle compilation (no warnings reported):

```sh
cd /home/ubuntu/pool-preparation/20261025-native
g++ -std=c++17 -O2 -Wall -Wextra -I /home/ubuntu/blockchain/forgecoin/external/randomx/src services/pool_research/tests/randomx_worker.cpp /home/ubuntu/blockchain/forgecoin/build/arm64-release/external/randomx/librandomx.a -o randomx_worker
python3 -m services.pool_research.tests.run_persistent_native_offline --worker ./randomx_worker --reference ./randomx_reference
FORGE_SYNTHETIC_PERSISTENT=/home/ubuntu/pool-preparation/20261025-native/randomx_worker python3 -W error::ResourceWarning -m unittest services.pool_research.test_persistent_randomx services.pool_research.test_synthetic_journal services.pool_research.test_synthetic_listener -v
```

- Native executable SHA256: 36026e5222b5a481ecc1897e4618fecef450e27e7ec4dcafc83cd9a975e91a86.
- Native source SHA256: 9589b5baf932a309cdbb25d77add4f39ba067f81148e646a77046aac70c4b610.
- Links the same existing development library/header with digests recorded in stage 1.
- 65 known-vector requests passed; exactly two worker starts verified recycle.
- Mutated input and seed-switch/back results matched the one-shot reference.
- Malformed/tag/oversized/partial native input returned refusal with no digest.
- Diagnostic harness duration 19.549s includes reference work; NOT a throughput benchmark.
- 23 Oracle worker/journal/socket tests passed in 23.555s; native socket hashes
  used the actual persistent helper. Fault tests use an explicitly fake Python
  worker to exercise real crash, timeout/blocked-stdin, wrong-tag, overlong-output,
  recycle, invalid-input, closed-state and concurrent-call behavior.
- 41 local worker/journal/socket/protocol/bound-job/adapter tests passed in 12.364s.
- No generated native executable or database is committed. Helpers are in the
  private Oracle research directory only; no systemd listener service installed.

Known limits: default interpreted/light-mode synthetic reference work; same
development RandomX implementation on both sides, not an independent source
attestation. No public miner/XMRig result, canonical FRG job validation, production
throughput, durable financial credits, accepted chain blocks or payouts claimed.
Next: trusted-source XMRig build and controlled synthetic client compatibility,
then proper per-worker job/difficulty/accounting integration. Such tests must
remain separated from old/new mainnet and cannot submit blocks or create coins.
Retain stage handoffs, append actual evidence and refresh the outputs copy.
