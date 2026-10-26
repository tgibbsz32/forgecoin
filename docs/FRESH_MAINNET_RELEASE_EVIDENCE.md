> **SUPERSEDED HISTORICAL CANDIDATE (20261020).** This candidate was mined offline and archived; it is NOT the current mainnet. Read `config/mainnet.identity.json` and `docs/MAINNET_CUTOVER_RELEASE_GATES_2026-10-26.md` for the replacement chain. Do not mine this candidate.

# Fresh-mainnet release evidence and gates (2026-10-23)

**Status: RELEASE BLOCKED.** Evidence inventory only. No deployment, chain transition, source-merging, wallet migration, or public-mainnet approval is authorized by this document.

## Evidence reviewed

Evidence is archived **locally**, outside the public repository, at `C:\Users\tgibb\Documents\Codex\2026-10-17\referenced-chatgpt-conversation-this-is-an\final-respository-and-builds\consensus-specs`. Results below are based on archived reports unless otherwise indicated. They have not all been independently reproduced.

| Area | Archived evidence | Supported conclusion | Limitation |
| --- | --- | --- | --- |
| Startup target | `cpp-startup-validation-report.md` | Standalone candidate C++ run reported 500000 at heights 1 and 15, 495000 at 16, 486394 at 90 and 486340 at 91 | Not real integrated block acceptance at transition |
| PoW acceptance | `FRESH_MAINNET_ISOLATED_MINING_RECHECK.md`; independently reopened copies of the preserved checkpoint | Archived native mining reached RPC height 17, including acceptance after startup-to-LWMA activation; copied checkpoint tip and next difficulty 400000 reproduced | Existing Windows candidate binary, not a fresh build; height 90–92 and ARM64 transition acceptance remain untested |
| Peer sync | `2026-10-20-ISOLATED-BRANCH-SYNC-RESULT.md` | Independent Windows node caught up to same tip | Not a competing-chain reorg |
| ARM64 agreement | `2026-10-20-HEIGHT3-MINING-AND-ORACLE-PROPAGATION.md` | Isolated Oracle ARM64 copy and Windows candidate agreed on persisted tip at RPC height 3 | Not cross-platform agreement through LWMA transition |
| Source integration | `candidate-integration-audit.md`, `difficulty-history-correction.md` | Genesis-history inclusion discrepancy was found; candidate source-level corrective edits were described | End-to-end correctness unproven |
| Genesis | `src/cryptonote_config.h` in archived candidate vs GitHub main | Candidate changes network ID, address prefixes, ports and nonce but keeps same genesis transaction | No proof that genesis output is permanently unspendable |

## Network identity — must not mix

Public source currently uses mainnet ports **19480/19481/19482**, address prefix set **90/91/92**, genesis nonce **10000**. Archived isolated fresh candidate uses **39480/39481/39482**, **190/191/192**, and genesis nonce **20261020**, while reusing the same genesis transaction bytes. Distinct configuration does not prove a secure completed fresh-mainnet protocol. Older local source snapshots and uncommitted development changes are not automatically the release baseline.

## Release-blocking mandatory checks

1. **Genesis/preallocation:** Decode and independently verify the output key, amount and all consensus conditions governing whether genesis outputs can be included in a valid spend. No zero-spendable-premine claim until proof is produced.
2. **Consensus startup:** Test real native blocks through heights **1–17** and the history transition **90–92**, with network-specific genesis history included consistently in template selection, main-chain acceptance, recalc and alternative chain validation.
3. **Forks:** Build two genuinely divergent isolated branches with valid PoW; verify fork-choice by cumulative work, reorg behavior and wallet rewind/recovery.
4. **Cross-platform:** Run matching deterministic consensus vectors and sync the same chain past both transitions on Windows x64 and Linux ARM64.
5. **Security:** Fuzz timestamp drift, difficulty floors, overflow, malformed blocks and alternate-branch history; independently review changes before freezing consensus.
6. **Launch fairness:** Account for existing development-chain owners and balances, publish unambiguous migration/transition policy, unique peer seeds and signed binary hashes. No silent reset.

## Guardrails

Do not merge old local difficulty edits blindly; do not connect isolated fresh-chain binaries to the live development network; do not expose public P2P/RPC or package wallets/miners as mainnet. Public governance-bond implementation is a separate unresolved security gate.
