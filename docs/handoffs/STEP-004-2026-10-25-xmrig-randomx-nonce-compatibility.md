# STEP-004 — 2026-10-25 — real XMRig interoperability and nonce layout

## Scope, branch and provenance

- Original, native-only FRG repository: `https://github.com/tgibbsz32/forgecoin`.
- Starting branch head: `main` at `7140606fdc26c7c4ca745d4fbb520a51631bacd0` (PR #104 merged, including Steps 002–003).
- Development branch: `feat/pool-xmrig-loopback-20261025`.
- **Implementation commit:** `8022c29494daaa1e9b6f94711216d9070805086f`.
- This separate handoff commit is the record of Step 004. No changes were made to the owner's original local consensus worktree or the separate FCMP/CARROT repository. No live daemon, wallets, node installation, pool wallet signing, deposits or FRG transactions were executed.

## Real implementation

- `services/pool_research/daemon_job_source.py`: explicitly reject a daemon mining blob with a serialized CryptoNote header whose nonce begins anywhere other than byte **39**, required by the pinned XMRig `rx/0` miner contract. This check happens before job issuance. The lower-level offline generic bound-job validator still supports other canonical layouts.
- `services/pool_research/test_daemon_job_source.py`: correct the test daemon to use a five-byte timestamp varint (instead of its two-byte original) and a coinbase-derived mock merkle root. Add negative test asserting non-39 offsets fail closed.
- `services/pool_research/test_native_stratum_research.py`: align the native verifier test with the 39-byte miner header offset.
- `services/pool_research/tests/run_xmrig_native_loopback_offline.py`: explicitly bounded Windows-local-only test runner that launches an existing reviewed XMRig binary with **one CPU thread**, zero donation and RandomX **light mode**. It binds only to a random localhost Stratum port and uses a fake daemon/pinned test genesis, a disposable fake worker label, and the native persistent C++ RandomX worker from previous research. XMRig is terminated at the bounded runtime; the runner refuses premature failure and requires at least one independently confirmed native submission rather than merely observing login. No public pool host option or private keys.
- `services/pool_research/README.md`: full research-only run instructions, observed counts, threat limitations and remaining mainnet launch gates.

## Executed evidence and failures investigated

- Installed XMRig reports version **6.26.0**, built 2026-03-28 MSVC 2022. The binary resides in the owner's existing Codex work directory and was **not** modified or replaced.
- First test discovered unsupported CLI option `--no-msr`, replaced with XMRig's supported `--randomx-wrmsr=-1`. This initially caused a false-positive login-only harness outcome; fixed the runner to reject premature process exits and require genuine validated submissions.
- Second test produced many **native claimed-digest mismatches** despite XMRig receiving jobs. Inspection isolated the cause to the fixture's two-byte timestamp varint: the test header's nonce was at **byte 36**, while XMRig was patching **byte 39**. Corrected the fixture and added a protective source validation rule.
- After changing the fixture and pinning the layout, the real XMRig 6.26.0 client generated **matching share digests**, independently verified through the actual existing native C++ RandomX worker.
- Final strict run: `python -m services.pool_research.tests.run_xmrig_native_loopback_offline --xmrig-executable <reviewed path> --native-worker <reviewed path> --seconds 10`: **63 genuine miner submissions passed native digest/worker checks**. No credited, paid or submitted blocks. The XMRig process returned **1** after intentional test termination; this is not a graceful miner shutdown result. Its redirected Windows stdout was empty; server-side native result counters provide the observed evidence.
- Targeted daemon job/Stratum suite: **21 passed**.
- Full pool regression suite: `python -m unittest discover -s services/pool_research -t . -q`: **136 tests run, 132 passed, four platform-dependent skips, zero failures**.
- `git diff --cached --check` passed before committing code.

## Exact remaining release blockers

1. This runner uses a **fake daemon with a template-shaped header** and a one-thread XMRig process. It is **not** proof of XMRig mining against an actual ForgeCoin daemon-created block through the complete Stratum service. A fresh ephemeral real-daemon plus genuine XMRig pipeline, version-tied native release build, independent genesis verification and clean shutdown are still required.
2. The researched Stratum listener still lacks proactive job rotation, job-broadcast on tip/seed changes, actual miner identity/payout address validation, effective resource exhaustion limits and proven 100-concurrent-worker support.
3. A positive RandomX share at worker difficulty 1 is **not** a found blockchain block. Native `submit_block` acceptance, canonical ancestry, full target/seed verification, block maturity and reorg handling remain untested.
4. No persistent share credit, mining reward ownership, PPLNS ledger, pool-fee reconciliation, wallet payout signing, crash-resume transaction recovery, public Stratum deployment, pool dashboard live API or production security review has been implemented.
5. This step does not implement FCMP/CARROT or Solana work and does not authorize mainnet deployment.

**Next work item:** create a bounded two-XMRig local test on an authentic disposable ForgeCoin daemon template and verify hash/difficulty/seed and enforced tip rotation. Then design a strictly isolated, test-only canonical `submit_block` pathway with finality proof and block-reorg tests. Continue committing separate dated numbered handoffs after each completed step.
