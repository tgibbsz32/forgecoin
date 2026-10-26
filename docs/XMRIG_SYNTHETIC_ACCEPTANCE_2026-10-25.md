> **Historical archive — superseded for current configuration.** Original evidence and decisions below retain their original dates and network parameters. Do not use old ports, genesis, balances, token proposals or release claims as current instructions. See [current mainnet specification](CURRENT_MAINNET.md) and the current roadmap.

# XMRig v6.26.0 — isolated native-verified synthetic integration

Date: 2026-10-25. **Result: PASS for the synthetic protocol/PoW boundary only.**
No ForgeCoin daemon, blockchain peer, wallet, live Stratum pool, rewards, or payouts
were used. Do **not** treat this as Solo or Pool block acceptance.

## Inputs and build evidence

- XMRig upstream tag: `v6.26.0`, pinned Git commit
  `b2ca72480c58d197e18c885d9fc1a0c8d517e60a`.
- Source changes before building: only `src/donate.h`, changing
  `kDefaultDonateLevel` and `kMinimumDonateLevel` from 1 to 0. The build
  script checks the pinned revision and refuses unrelated tracked changes.
- Build script: `tools/build_xmrig_synthetic.sh`; local Linux build finished
  `[100%] Built target xmrig-notls`. GPU, MSR, HTTP, TLS and additional
  nonessential mining features were disabled via that script's CMake options.
- XMRig ELF SHA-256:
  `391f766cadc49f4cb349e680b363994147af54651235fb51d5b1219f33fbd24e`.
  Its recorded direct dynamic dependencies were libuv, libc, libm and the
  Linux ELF interpreter.
- Native worker: `services/pool_research/tests/randomx_worker.cpp`, linked
  to a locally built `external/randomx` static library from this ForgeCoin
  checkout. Worker SHA-256:
  `5be16e696e17f6214c07243522672d905945ec01990b5baa0b29e0e8a363a77b`.
- Build location: disposable `ForgeCoinBuild` WSL Linux instance. No
  generated executable was added to Git.

## Isolation and observed outcome

The test executable was staged with the native worker in
`/tmp/forgecoin-xmrig-run`, owned as a private test directory by UID 65534.
The launcher `tools/run_xmrig_synthetic_isolated.sh` creates a new Linux
network namespace, brings up only loopback and checks the namespace interfaces
via `ip -o link show`, with no IPv4 or IPv6 routes. It drops to UID/GID 65534,
removes Linux capabilities, sets no-new-privileges and invokes the runner.
The Python runner independently requires UID != 0, only loopback via
`socket.if_nameindex()`, zero effective/permitted/inheritable/ambient
capabilities, `NoNewPrivs=1` and an unreachable external test route before
launching XMRig. The launcher refuses to fall back to host networking.

The first run failed to record a submission. Source inspection found XMRig's
`Job::nonceOffset()` defaults to **byte 39** for rx/0; the synthetic fixture
previously placed the nonce at byte 35. The fixture now uses a canonical
five-byte timestamp varint, placing its synthetic nonce at offset 39, and
regression tests use that same offset. **The corrected run passed:**

```text
ISOLATION: unprivileged, no capabilities, no-new-privileges, only loopback/no external route
PASS: XMRig client submitted native-verified rx/0 synthetic work; records=2; credited=0
PASS: client, listener and worker stopped; disposable evidence removed; no chain/block/payout calls
```

The Stratum parser/listener/journal offline suites passed **25 tests**.
The test runner's temporary journal contained two independently verified
synthetic submissions with `synthetic=1, credited=0`. This evidence is not a
network-native block and does not create any FRG entitlement.

## Remaining release blockers

Native miner share equivalence is established for the **synthetic rx/0 work
sample**, not for source-matched real block templates. Real ForgeCoin
template reconstruction, consensus difficulty/seed boundaries, actual daemon
block submission, canonical block maturity, PPLNS allocations, payout signing
and settlement remain unverified. Keep public and payout services disabled.


## Follow-up diagnostics and fail-closed check (2026-10-25)

The isolated run was repeated successfully using the pinned binary hashes
above: XMRig login, job delivery, two `submit` requests and native RandomX
verification produced `records=2; credited=0`. The test exits after stopping
client and verifier processes. The runner now records only request method names,
response status/error classifications, and the client exit code on failure;
it does **not** log raw block/seed material or claimed digests.

As an isolation negative control, the same Python runner was invoked directly
in the ordinary WSL network context. It raised
`RuntimeError: requires unprivileged loopback-only network namespace` before
opening the listener or spawning XMRig. The updated Stratum/listener/journal/
persistent-worker offline test selection passed **31/31** cases.

GitHub tracking remains open: #28 requires candidate-daemon provenance/shutdown
follow-up, #29 requires end-to-end native candidate template-to-job proof, and
#30 requires fully source-matched mining share acceptance and safeguards.
Neither the synthetic result nor this report closes those release blockers.
