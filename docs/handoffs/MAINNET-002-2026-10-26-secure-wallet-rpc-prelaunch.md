# MAINNET-002 — 2026-10-26 — secure local wallet RPC and prelaunch Windows desktop

## Scope

This follow-up to MAINNET-001 stays on the ORIGINAL ForgeCoin repository and
branch `feat/fresh-mainnet-identity-and-integration-gates-20261026`, draft
PR #111. The genesis nonce `20261026`, full genesis hash
`4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c`,
network UUID, consensus rules and native executable hashes are **unchanged**.
No work touched Oracle mainnet state, existing user wallets, private recovery
phrases, previous archived chains or the separate FCMP++/CARROT project.

## Actual CI failure and repair

- The original prelaunch GitHub Actions workflow for PR #111 ran all Python
  mainnet/desktop tests, all C pool source tests and exact FRG monetary tests
  successfully. Its Windows GUI build job failed with `CS1504: Source file
  'D:\\a\\forgecoin\\forgecoin\\Program.cs' could not be opened`, because
  the legacy .NET Framework compiler treated the slash-containing *relative*
  source path as an option-like input on that runner.
- Fixed `.github/workflows/new-mainnet-prelaunch.yml` to pass absolute
  `$env:GITHUB_WORKSPACE\apps\desktop\Program.cs` and
  `$env:RUNNER_TEMP\ForgeCoin-NewMainnet-Prelaunch-GUI.exe` paths.
- Verified on Windows with the exact same C# compiler/options. Commit:
  `026663ea1b1310a62bb3bea7829bd8b16021add8`. GitHub workflow
  `40332366530` then passed **both** mainnet source verification and the
  Windows desktop GUI compile job.

## Wallet RPC authentication security finding and remediation

The first private `v0.1` desktop package started the native wallet RPC with
`--disable-rpc-login`, which would allow unrelated programs with local
HTTP access to invoke sensitive wallet methods including recovery-seed
queries. **Do not use v0.1 for valuable treasury funds.**

The v0.2 GUI now:
1. Generates a cryptographically random 256-bit in-memory wallet-RPC
   credential at startup via `RandomNumberGenerator`.
2. Starts the native wallet RPC bound only to `127.0.0.1:39483` using
   `--rpc-login`, not `--disable-rpc-login`.
3. Uses `.NET HttpWebRequest` with an HTTP Digest `CredentialCache`
   for calls to this wallet RPC only. Node RPC 39481 remains separate.
4. Keeps the fresh-mainnet-only wallet/LMDB/ringdb directories and
   prelaunch solo/pool mining locks.

### Real executable-level security test

On the authorized Windows PC, the already built, SHA-pinned new-mainnet
`forged.exe` was launched offline against an isolated genesis-only
directory. The matching `forge-wallet-rpc.exe` ran with a **disposable
non-secret test credential**, localhost-only port 49582, and no funded
wallet. A new C# test executable using the same framework HTTP Digest API
verified:

- Unauthenticated JSON-RPC `get_version` received **HTTP 401 Unauthorized**.
- The proper .NET Digest credentials authenticated and `get_version`
  returned a valid RPC result.
- The daemon remained at RPC **height 1**, no miners were activated, and
  both test services were stopped afterward.

The static regression suite now verifies that the source contains
`--rpc-login`, strong random generation, Digest credentials and
localhost-only wallet RPC, and never contains `--disable-rpc-login`.
Local tests: **13 mainnet/desktop tests, 19 C pool tests passed**.
The new Windows GUI compiled successfully (no irreversible wallet changes).

**Limitations:** child-process command-line arguments containing
`--rpc-login` are potentially inspectable by a privileged local user.
This is a significant improvement over unauthenticated RPC, but is not
a completed independent security audit. The owner's encrypted wallet
password and recovery phrase must remain solely on their trusted PC.

## New private owner prelaunch package

The previous private v0.1 ZIP remains superseded for any real custody.
A new matching owner-only portable Windows wallet bundle was built at:

`%USERPROFILE%\Downloads\ForgeCoin-Mainnet-20261026-Prelaunch-Wallet-v0.2.zip`

SHA-256:
`7B1B78CD55260CF8D746504CD5A26FF0F7095E22C4823E3F31D59E6EFA9737C6`

The ZIP was verified to contain 17 entries including the GUI, pinned
`forged.exe`, `forge-wallet-cli.exe`, `forge-wallet-rpc.exe`,
`mainnet.identity.json` and `TREASURY-WALLET.md`. All three native
hashes matched the manifest. The ZIP was not uploaded to GitHub or
made into a public release.

The owner's fee treasury wallet has **not** been created by the assistant.
Only its **public** new-mainnet receiving address should later be used
for `pool-fee-wallet`. Never share its seed, encrypted wallet files,
password, or spend keys with a server, GitHub or an assistant.

## Remaining blockers

This is a genesis-frozen **PRELAUNCH** wallet package, not a finished
mining application or an authorized live mainnet release.
- GUI wallet creation/backup/restore requires owner-visible testing;
  the earlier disposable wallet RPC create/address/balance/close test passed.
- Mainnet solo and pool mining are intentionally disabled; XMRig is not
  bundled. The official C pool still requires accepted native block,
  reorg-safe PPLNS and fee-wallet accounting/payout validation.
- The 11.92092895 FRG genesis coinbase output's permanent unspendability
  remains unproven. Do not claim zero spendable premine until resolved.
- Matching ARM64 mainnet daemon, new chain public explorer,
  public Stratum, owner fee-wallet address, launch authorization and
  coordinated release remain outstanding.

No test mined any block on the frozen new mainnet.
