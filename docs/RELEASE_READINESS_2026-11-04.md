# ForgeCoin public-release readiness — November 4, 2026

**Status: PRELAUNCH / NOT AUTHORIZED FOR PUBLIC MINING, FUNDED WALLETS OR POOL PAYOUTS.**

This is the release-candidate evidence ledger for the **native FRG coin**. It
separates actual native test-chain results from planned features, old desktop
packages and the currently unlaunched public chain. It supersedes historical
"pending" checkpoint paragraphs where a newer exact CI result is listed, but
does **not** override security gates or grant permission to deploy.

## Frozen network identity

| Item | Selected, currently locked specification |
| --- | --- |
| Native ticker / precision | FRG / 8 decimals (100,000,000 atoms = 1 FRG) |
| Genesis nonce | `20261026` |
| Genesis hash | `4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c` |
| Network UUID | `bd936359-09e4-4fdb-8ec0-12fa9d6ef090` |
| Standard / integrated / subaddress prefixes | 190 / 191 / 192 |
| P2P / daemon RPC / ZMQ | 39480 / 39481 / 39482 |
| Windows local telemetry / wallet RPC | 39483 / 39484 (localhost only; Tauri wallet RPC is dynamic) |
| PoW / target | RandomX / 120 seconds; startup difficulty 500,000, floor 400,000, LWMA90 from height 16 |
| Operator fee | 1% of eligible **pooled** rewards; not a consensus block deduction |
| Release controls | `release_authorized=false`; zero mainnet blocks permitted; public Stratum and payout signing disabled |

See [selected consensus/tokenomics](CURRENT_MAINNET.md), [machine-readable documentation identity](mainnet.identity.json), and [network port inventory](NETWORK_PORTS.md). Documentation and hashes **cannot by themselves establish runtime identity**.

## Verified actual native test-chain evidence

| Gate | Evidence | Meaning / limitations |
| --- | --- | --- |
| Actual native RandomX C Stratum block acceptance | [x86_64 41726516379](https://github.com/tgibbsz32/forgecoin/actions/runs/41726516379) | Native C pool + same-revision daemon accepted a valid **disposable FAKECHAIN** block. Not a production pool release. |
| 61-block maturity, exactly 99% miner / 1% operator, restart | [x86_64 41730254226](https://github.com/tgibbsz32/forgecoin/actions/runs/41730254226) | Real test reward **2,384,185,222 atomic FRG**, 2,360,343,370 miner atoms, 23,841,852 operator atoms; no wallet payment signing. |
| 62-block reversal after credit; persistent payout hold | [x86_64 41731489643](https://github.com/tgibbsz32/forgecoin/actions/runs/41731489643), [ARM64 41731489619](https://github.com/tgibbsz32/forgecoin/actions/runs/41731489619) | Actual higher-work fork orphaned credited block; pool preserved credits, marked LMDB quarantine and rejected startup; no spendable payout. |
| Native signed transaction and mempool admission | [x86_64 41775386686](https://github.com/tgibbsz32/forgecoin/actions/runs/41775386686), [ARM64 41775386697](https://github.com/tgibbsz32/forgecoin/actions/runs/41775386697) | Fresh native wallet mined 80 test blocks; signed 16-member ring; local FAKECHAIN mempool accepted exactly once with **no relay**. |
| Separate native wallet received confirmed 1 FRG | [x86_64 41792342842](https://github.com/tgibbsz32/forgecoin/actions/runs/41792342842), [ARM64 41792342746](https://github.com/tgibbsz32/forgecoin/actions/runs/41792342746) | Real mined FAKECHAIN transfer was visible to a **distinct** receiving wallet as 100,000,000 atoms; not a pool payout. |
| Recipient wallet process restart and exact ledger persistence | [x86_64 41796542812](https://github.com/tgibbsz32/forgecoin/actions/runs/41796542812), [ARM64 41796542671](https://github.com/tgibbsz32/forgecoin/actions/runs/41796542671) | Native receiving wallet closed, process stopped/restarted, password-reopened and confirmed credit/history retained **once**. Merged into **test-only branch**, not public `main`. |
| Native Windows candidate wallet create, 25-word recovery, disk and process restart | [merged #218](https://github.com/tgibbsz32/forgecoin/pull/218) and [desktop CI 41814512396](https://github.com/tgibbsz32/forgecoin/actions/runs/41814512396); native QA executed locally on authorized Windows PC | Hash-pinned candidate wallet-RPC created and restored disposable same-address wallet, rejected incorrect password, and preserved wallet after RPC restart **with no daemon, peers, mining or public FRG**. WinForms restore UI compiled, but its interactive end-to-end use and final reviewed binary provenance remain pending. |
| Android ARM64 RandomX one-shot debug harness | [merged #219](https://github.com/tgibbsz32/forgecoin/pull/219), [Android debug CI 41815524641](https://github.com/tgibbsz32/forgecoin/actions/runs/41815524641) | Debug UI invokes vendored native RandomX for **one known-answer hash** on a worker thread subject to battery, thermal and memory checks. **Actual physical ARM64 native execution is pending. This is not a miner.** |
| Genesis public output & valid signed ring decoys | [x86_64 41771459088](https://github.com/tgibbsz32/forgecoin/actions/runs/41771459088) | Actual LMDB genesis output has height 0; valid native signed-ring policy disallows genesis decoy. **Not a full signed MAINNET transaction-input rejection**. |
| Two disposable native nodes and critical 66-deep reorg observation | [x86_64 41771760913](https://github.com/tgibbsz32/forgecoin/actions/runs/41771760913) | Two local processes on one runner, not independent operators/providers or eclipse resistance. |
| C pool graceful stop / shared WebUI event loop | [merged #200](https://github.com/tgibbsz32/forgecoin/pull/200) | Linux x86_64 and ARM64 builds passed. Shutdown safety fixed in `main`; no payout enablement. |

The advanced native validation source is reviewed as separate **draft frozen-consensus PR #185** and **isolated wallet PR #203**; passing *test-only* CI does not mean the old `main` runtime implements this final chain.

## Release tracks — as of this checkpoint

### Windows desktop wallet + solo / pool miner

**Available:** Windows Forms GUI source compiles and private candidate desktop bundles exist. Windows port/identity source checks have been merged. [Desktop packaging PR #208](https://github.com/tgibbsz32/forgecoin/pull/208) **merged** after Linux desktop endpoint tests, Tauri frontend build, Windows Forms source-only QA compile, public packaging refusal, and tampered native sidecar hash rejection passed [Windows/Linux CI 41806531368](https://github.com/tgibbsz32/forgecoin/actions/runs/41806531368). This only controls packaging and existing prelaunch candidate hashes: it is NOT final source/binary provenance or an operational wallet release. Earlier Tauri frontend and local installer source checks do **not** establish a clean-machine release.

**Updated native Windows QA:** [PR #218](https://github.com/tgibbsz32/forgecoin/pull/218) is merged and passed both desktop CI jobs. In a strict disposable loopback-only test on the connected Windows PC, the SHA-256-pinned prelaunch native wallet RPC created a new 25-word wallet, restored the same address, rejected a wrong password and reopened it after an actual RPC process restart. The Windows Forms GUI gained a matching private-QA restore dialog, exact eight-decimal atomic amount parsing and launch-locked send/mining entrypoints. An isolated **37,129,593-byte Windows QA ZIP** was created in the user's local Downloads. This is not a signed public installer, nor has the new GUI been interactively acceptance-tested with a funded wallet.

**Subsequent WinForms UI acceptance (November 4):** [PR #224](https://github.com/tgibbsz32/forgecoin/pull/224) runs the actual Windows Forms GUI at **900×680** and **1040×760** in an isolated, temporary, compile-time-only QA profile; **46 real GUI layout/release-lock checks passed** and **38 Python desktop source/security tests passed**. The second test drove the **actual GUI Create Wallet → 25-word backup → Close Wallet → Restore Wallet → matching public address → Close Wallet** against the SHA-256 pinned historical private wallet-RPC sidecar; **49 actual native wallet GUI assertions passed**. No secrets, addresses, keys or passwords were printed, no user wallet was accessed, and the native test wallet was removed after test. The test exposed and fixed a **timer-refresh bug that could re-enable Solo Mining when no daemon was running**; startup, offline-node toggle and all timer update paths now keep public mining and spending controls locked. The native wallet creation/open/recovery RPC uses appropriate longer cold-start timeouts, with mandatory local Digest authentication. **No daemon, FRG mining, transfer, public peer connection or Oracle service was started. This is private prelaunch acceptance, not production release proof.**

**Outstanding before public executable/installer:** Reviewed frozen native Windows daemon and wallet sidecars built from the identical approved consensus source; create/restore and 25-word recovery; fresh private wallet address/balance/transaction signing; confirmed send/receive and rescan/restart; solo RandomX proof and pool Stratum/1% fee/accounting; start/stop, thread and intensity settings, user-visible errors, offline/unreachable node; safe RPC secret isolation, installed DLL provenance, clean-device install/uninstall, dependency/license audit, signing, checksums. Do not run testing on existing owner wallets.

**What users may download today:** No approved public FRG mainnet desktop installer. An old `ForgeCoin-Mainnet-20261026-Prelaunch-Wallet-v0.x` folder is historical private QA, **not** a signed public wallet or active-mainnet package.

### Android ARM64 wallet + solo / pool miner

**Available:** a restricted **debug UI preview** with the ForgeCoin brand, read-only network/pool links, JNI RandomX support/probe libraries, read-only battery/thermal/CPU diagnostic panel and a **user-confirmed, one-shot RandomX known-answer JNI test**. It does not start mining, mine blocks, send shares, or connect to a pool. The Android build requires debug mode, battery/thermal/memory preflight and confirms exactly one hash; on-device ARM64 execution still needs a physical phone. Android Gradle 8.11.1 / AGP 8.9.2 / JDK21 / SDK35 build & source security gates passed on a Windows QA checkout, plus [GitHub Android restricted preview CI](https://github.com/tgibbsz32/forgecoin/actions/workflows/android-preview-safety-ci.yml). Debug application ID `org.forgecoin.p2ptest.isolatedqa`; **not** a native wallet/miner.

**Updated Android QA:** [PR #219](https://github.com/tgibbsz32/forgecoin/pull/219) was merged after Android and desktop CI passed; the connected Windows build passed **23 JVM tests and eight source-security tests**, restricted debug APK verifier, and produced a **3,634,999-byte** APK with SHA-256 `f3fb70edf3c71ce887072d6059bb707ed74ea7bcb2185f3ec13e1c13f20bf224`. Only JNI RandomX and runtime-probe support libraries are bundled. The actual known-answer hash cannot be claimed verified on a physical ARM64 handset; ADB detected only x86_64 emulators.

**November 4 Android wallet-address advancement:** [merged PR #221](https://github.com/tgibbsz32/forgecoin/pull/221) added a Bouncy Castle Keccak-256 + CryptoNote 8-byte-block Base58 **public-address checksum/prefix verifier** for standard 190, integrated 191 and subaddresses 192, plus a restricted debug input screen. Actual public address from the isolated Windows native mining QA and independent Keccak reference vectors passed; negative checks reject invalid Base58, checksum and wrong-network prefixes. The connected Windows Gradle build passed **28 JVM tests / zero failures**, and **10 Android source guard tests**, and generated a **3,638,316-byte** restricted debug APK with SHA-256 `8261942742f97196efd3ed38bc945114d4ec87970bd1be6dd3a9fd043ff63ca5`. GitHub Android preview and desktop endpoint CI passed. **This verifies public address syntax/checksum only**; it neither establishes curve-point validity nor controls a wallet, derives seed keys, scans balances, mines, sends FRG or authorizes mainnet. Physical ARM64 handset acceptance and a native FRG wallet remain pending. The private QA APK ZIP was created on the operator's connected Windows PC and is not an approved public download.

**Missing:** Verified Android `arm64-v8a` native FRG daemon, RandomX miner and wallet signing interfaces compiled against the frozen consensus; 25-word create/restore and encrypted local custody with user/device authorization; balance scanning, signed receive/send; solo/pool accepted work and rejected-share accounting; thread/intensity controls, thermal shutdown/throttling, battery/charging policies, foreground service and Android background execution compliance; native clean-device restore, real-phone install and stop/restart/network-loss tests. ADB found **no connected physical ARM64 handset** at this checkpoint. **Never submit a test seed to a public node or pool.**

**What users may download today:** No approved Android FRG miner/wallet APK. The existing preview is intentionally incapable of mining and spending native FRG.

### Official native FRG mining pool, read-only statistics and explorer

**Available:** a genuine native C pool has accepted RandomX work, matured reward allocations into exact LMDB miner/operator atomic amounts, restarted without double-credit, and persisted a quarantine after a deep actual test reorg. The read-only localhost bridge now accepts **public FRG payout-address lookups without accounts** and can return only worker count and observed hashrate. The public GitHub Pages form deliberately does **not** transmit an address until a reviewed same-origin HTTPS stats API is deployed. No balances or payouts are exposed by this read bridge. A fixed 100-worker capacity must **not** be advertised without real load testing.

**Pool journal status:** [PR #214](https://github.com/tgibbsz32/forgecoin/pull/214) added durable LMDB payout intent/ambiguous-result holds and [PR #216](https://github.com/tgibbsz32/forgecoin/pull/216) added source-bound canonical SHA-256 payout manifests. Both are merged; they do **not** execute wallet transfers, debit balances or prove exactly-once settlement. The unjournaled sender remains compile-locked by [P0 #210](https://github.com/tgibbsz32/forgecoin/issues/210).

**Missing:** Real spend-key-isolated wallet RPC payout integration, transaction signing, idempotent persistent payout journal, mined confirmation in recipients, 1% operator reconciliation, withheld/failed payout recovery, dust/fees/minimum threshold policy, payout reorg handling before/after sending, unaffiliated independent node confirmations, authenticated operational controls and wallet backups. Separately verify Android/Windows clients against the actual pool. Explorer and all API/website metrics must be tied to the approved canonical chain and protected by HTTPS, CSP, freshness/error handling and deployment monitoring. Pool stats require **no miner registration**.

### Oracle / production launch and releases

Public P2P/RPC/Stratum, explorer HTTPS and firewall configuration need an authorized, independently reviewed cutover. Legacy port 19480/19481 retirement must be checked against live Oracle service and firewall, not inferred from source. Never expose wallet RPC/spend keys or unrestricted daemon RPC publicly.

No FRG core node, wallet, pool or Android miner becomes live merely by merging source or receiving a green CI check. Native consensus, wallet payout acceptance, independently operated peers and distribution security must all be approved before changing network or payout switches. Any Github Release asset should have a documented source commit, build environment, checksum, publisher signature, malware/security review, licenses/attributions and **explicit release authorization**.

## Exact release decision sequence

1. Independent consensus/source review of draft #185, permanent Genesis output-spend prohibition with a **full signed native MAINNET transaction input/mempool test**, and accepted canonical agreement across independent hosts (including adversarial forks/restarts).
2. Complete native C-pool payout signer and public read-only stats/explorer with exact atomic accounting; prove multiple recipient wallets, fees and 60-block maturity/reorg/idempotence.
3. Finish Windows and Android native wallets/miners on matching approved consensus; verify actual solo and pool work, wallet restore/send, thermal/foreground safety, release package install on clean target devices.
4. Audit mainnet identities, URLs, retired listeners/firewall, peer bootstrap, backups, payout controls and operational monitoring. Publish audited standalone read-only stats and accessibility-complete pages.
5. Owner release authorization and independently reproducible signed/checksummed GitHub Releases for Windows and Android; controlled public opening only after the required security gates are reviewed.

## Contact, contribution and transparency

Code contributions and external consensus/security reviews are welcome through
[GitHub issues and pull requests](https://github.com/tgibbsz32/forgecoin).
Do not post wallet seeds, private keys, recovery phrases, node passwords or
other secrets in issues. Read [responsible disclosure](../SECURITY.md).

mFRG/Solana bridge, staking, DEX integrations and Discover Your City payments
are **proposed later utility** and do not belong in native FRG launch binaries
or release authorization. Governance procedures are to be determined and
published before mFRG distribution. See [roadmap](../ROADMAP.md).

*Evidence is only as strong as the named build and CI job; a passing synthetic,
source-level or regtest assertion must never be relabeled a production launch.*
