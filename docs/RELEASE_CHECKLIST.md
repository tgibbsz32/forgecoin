> [Current mainnet specification, tokenomics and release status](CURRENT_MAINNET.md) — October 26, 2026; prelaunch.

# ForgeCoin public release checklist

## Source publication
- Publish only this repository directory, never the surrounding workspace.
- Inspect staged files and the complete Git history for private data.
- Verify author identity before every commit; the repository uses a project identity.
- Keep third-party license notices and public test fixtures.
- Enable a private security-reporting channel on the chosen hosting account.

## Binary releases
- Build native binaries from the exact source commit being released.
- Vendored dependencies are included; configure CMake with `-DMANUAL_SUBMODULES=1`.
- Validate the native build on each supported platform before claiming support.
- Verify genesis, network UUID, v1 genesis and v19 activation at height 1 and monetary constants.
- Test daemon startup, two-node synchronization, wallet recovery and transfers.
- Test mining start/stop, address creation, explorer and desktop resizing.
- **Desktop V1 mining release gate (both modes required):** Before labeling the Windows desktop build ready, execute and record end-to-end **Solo** and **Pool** mining acceptance tests on an isolated, disposable FRG network and a compatible test pool. A process that merely starts does **not** count as a pass.
  - Solo: start/stop the miner through the packaged desktop; verify a block is found, accepted by the daemon, survives restart/reorganization checks where applicable, and matures to the test wallet under the current coinbase rules.
  - Pool: connect the desktop-managed, user-installed XMRig to an independently verified FRG-compatible *test* pool; demonstrate valid RandomX shares accepted and invalid/stale submissions rejected; exercise reconnect, worker telemetry, stop and failure reporting; reconcile a credited test reward and matured payout to a disposable wallet, including accounting and restart behavior.
  - Capture source commit, binary hashes, Windows version, test chain parameters, XMRig version, timestamps, relevant logs and results. No keys, passwords, wallet seeds or private templates may enter the evidence or repository.
  - If either mode lacks compatible infrastructure or verifiable results, mark that mode **NOT VALIDATED** and **block the initial desktop release**; do not substitute earlier offline pool-share research or a running-process screenshot for the acceptance criteria. An official public pool is a separate later-phase deliverable, not required for V1.
- Check compiled binaries for personal build paths and debug information.
- Do not change genesis or restore inherited Monero checkpoints or seed nodes.
- If including XMRig, include its matching source and license.
- Keep signing private keys outside the repository. Public signatures can identify
  or correlate a release signer; choose the intended public identity deliberately.
- Generate checksums after final packaging/signing; publish binaries as release assets.
- Describe known limitations, bootstrap peer requirements and upgrade instructions.

## Validation status
This source export has not received a fresh full native rebuild or independent
security audit. Earlier desktop tests used packaged Phase 3 native binaries.
The testnet and stagenet identities are not ready for public use.
