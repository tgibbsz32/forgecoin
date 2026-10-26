> [Current mainnet specification, tokenomics and release status](../../docs/CURRENT_MAINNET.md) — October 26, 2026; prelaunch.

> **V1 scope:** Native FRG only. Solana wallet authentication and `staking` weights below are legacy, local practice fixtures, not authorized V1 assets or governance rights. Mining-linked secondary token issuance and Solana staking are deferred; the former chamber is withdrawn. Native miner governance bonds require a reviewed enforceable lock and independently verified mining; neither is implemented by this service. See [the current charter](../../governance-charter.md).

# ForgeCoin governance API — development-only foundation

This service is **not deployed**, does not register real voters, and cannot accept binding election ballots. It is intended to run locally or in an isolated test environment. GitHub Pages cannot enforce voter eligibility.

## Requirements and start

Python 3.11+; install in a virtual environment:

```bash
pip install -r services/governance_api/requirements.txt
uvicorn services.governance_api.app:app --reload --host 127.0.0.1 --port 8765
```

The Python import-friendly directory is `services/governance_api` (underscore), not a production service. From the repository root, run tests with `python -m unittest services.governance_api.test_app`.

## API

- `GET /health`: dev status.
- `POST /auth/challenge` with `{"address":"<base58 Solana public key>"}`: creates a one-time nonce and a signed-message challenge (server-side generated).
- `POST /auth/verify` with `{"address":"...","nonce":"...","signature":"<base58 ed25519 signature>"}`: verifies the exact challenge with Ed25519, consumes nonce and returns an opaque session token.
- `GET /me` with `Authorization: Bearer <token>`: returns verified wallet and assigned demo roles.
- `GET /elections/{election_id}/eligibility` with bearer token: evaluates role at the server, not in browser JavaScript.

Member registration and reviewed role decisions now persist in SQLite. Set `FORGECOIN_GOVERNANCE_DB` to an isolated writable path (default: `governance-dev.sqlite3` in working directory). **Never commit the database or identity evidence.** `review_cli.py` provides a local-only administrator workflow; it is not an HTTP route. For example from repository root: `python -m services.governance_api.review_cli approve WALLET miner --reviewer reviewer-id --reason 'test evidence reviewed'`, or `python -m services.governance_api.review_cli revoke WALLET miner --reviewer reviewer-id --reason 'eligibility expired'`. Inspect decisions with `python -m services.governance_api.review_cli history WALLET`. CLI possession is a trust boundary: do not let untrusted users access the host, database, or its process. This prototype does not validate reviewer identity, attestations or reviewer quorum.

All new accounts start with **zero verified roles**. There is deliberately no public endpoint for self-awarding 'miner', 'developer', 'community', 'staking' or 'chamber' roles. Admin provisioning, uniqueness verification, mining proofs, stake snapshots, audited ballots, signed credentials and long-term persistence must be built and reviewed separately.

Security limitations: nonces and sessions are in **process memory** (lost on restart), while role decisions persist in SQLite. The CLI administrator can change roles directly without independent approval; this is not safe for production. SQLite here has no identity-verification workflow, review quorum, tamper-evident external audit anchoring or election credential issuance; it is not scalable or production-ready. No CORS origins are enabled. Sessions expire, challenges expire and are single-use, and payload sizes are bounded. Use HTTPS, CSRF-resistant authenticated sessions where appropriate, rate limits, durable atomic nonce storage, distributed abuse defense, admin audit logs and independently reviewed election logic before public operation. Do not bind to 0.0.0.0 on an internet-facing Oracle VM.

## Eligibility model

The sample elections are:
- `staking`: staking role (later require validated on-chain stake snapshot and election weight).
- `miner`: miner role (verified FRG mining contribution).
- `developer`: contributor role.
- `community`: verified unique community person.
- `chamber`: seated delegate credential.

A category credential may authorize access to an election **only after election-specific snapshots and anti-duplicate checks are introduced**. Endpoint results at this phase must not be used to cast or count ballots.

## Member eligibility application workflow (experimental)

Authenticated wallets may send `POST /applications` containing `role` (`miner`, `developer`, or `community`), `evidence_reference` (an opaque `ref:` reference or public HTTPS URL), and a short `statement`. The service records a **pending** application in SQLite and returns its ID; this grants **no** voting role. `GET /applications/mine` returns only the authenticated wallet's application IDs, roles, statuses and timestamps, and deliberately omits evidence and reviewer notes.

No HTTP route can approve an application. Authorized local administrators can *experimentally* review a pending application from the repository root with:

```bash
python -m services.governance_api.review_applications approve 1 --reviewer independent-reviewer --reason "Independently checked mining evidence"
python -m services.governance_api.review_applications reject 2 --reviewer independent-reviewer --reason "Inadequate documentary evidence"
python -m services.governance_api.review_applications audit 1
```

Reviewer CLI access is **not itself authenticated or independently approved**; do not deploy it to an untrusted host. Reviewer identity is a text claim. Review approval creates an audited role decision, but does not enable election ballots. The system prevents the applicant wallet string from being used as its own reviewer identifier; this alone is **not robust reviewer identity verification**. A production service requires managed reviewers, multiple-approval rules, secure private evidence storage, tamper-evident logs, retention/deletion policy, appeals, spam prevention and stronger uniqueness checks.

Only one pending application per wallet and constituency is accepted. Rejected/approved requests are retained in the audit database; follow-up resubmissions need a documented policy. **Do not upload passports, selfies, private keys, recovery phrases or sensitive identity documents to this API.** Prefer opaque evidence references that do not themselves reveal private evidence; references and statements are still stored in SQLite and must be treated as potentially sensitive.

The legacy staking and chamber categories cannot be requested using this application endpoint. They do not define future eligibility: Solana staking is outside V1 and any replacement chamber requires a separately reviewed specification.

Run the local test suite from repository root:
```bash
python -m unittest services.governance_api.test_app
```
No public deployment or tests in CI have been verified as part of this change.

## Frozen practice elections (not binding)

A local administrator can create a *practice* election by calling `elections.create(category,title,weights=...)` in a trusted local Python process. It snapshots the current approved wallets for the selected category into `practice_electors`; changes to roles **after** creation do not add voters retroactively. Staking-weight simulations require explicit per-wallet integer weights from the administrator; these numbers are **not** validated against Solana balances and cannot be used for legitimate financial governance.

Authenticated wallets can submit `POST /practice-elections/{id}/ballots` with `{"choice":"yes"}`, `{"choice":"no"}`, or `{"choice":"abstain"}`. Every accepted submission is marked `binding: false`. SQLite's unique composite key on election ID and wallet rejects duplicate ballots atomically. `GET /practice-elections/{id}` returns nonsensitive counts and turnout weights; it does not identify voter preferences. The `elections.close(id)` operation is local-administrator-only.

**Outstanding limitations:** There is no approved administrator authentication, person-level uniqueness, proof of miner ownership, staked-token attestation, delegated stake handling, ballot anonymity, election scheduling, formal election tally rules, dispute handling, or multi-reviewer reconciliation. A single person who controls multiple verified wallets may have multiple ballots. SQLite administrators can alter the records. Do not deploy this feature publicly or represent its voting output as binding decisions. Browser-only GitHub Pages practice simulations remain separate.

Test with `python -m unittest services.governance_api.test_app` after installing dependencies.

## Local practice-election operations

Use these commands from the repository root **only on a trusted development machine**:

```bash
python -m services.governance_api.election_admin list
python -m services.governance_api.election_admin create community "Sample community proposal"
python -m services.governance_api.election_admin close 1
python -m services.governance_api.election_admin tally 1
```

For staking simulations, create a local JSON file mapping eligible registered Solana wallets to **demo integer weights** and add `--weights-json path/to/weights.json`. Never publish the mapping if it may reveal identities or sensitive user finances. The code does not validate live stake ownership.

The operator can create a frozen eligibility snapshot, inspect turnout without seeing ballots, close a practice election, and tally aggregate votes **only after closure**. There are no public HTTP administrative routes. A local operator with machine/database access is currently fully trusted; this is **not** an authenticated, multi-reviewer admin dashboard. The existing `docs/practice-governance.html` is a static visual simulator and does not communicate with the API.

**Do not use the aggregate results for binding monetary decisions.** The system lacks verified person-level identity, secure audit anchoring, anonymous ballots, independent election administration, election scheduling, eligibility appeals and anti-coercion protections.

## Development-only administrator dashboard

The dashboard is a **separate service**, never mounted in `app.py` and never
served from `docs/` or GitHub Pages. The ordinary API still has no administrative
HTTP routes. Do not reverse-proxy, tunnel, deploy, or bind this dashboard publicly.

From the repository root, after installing the requirements, use PowerShell:

```powershell
$env:FORGECOIN_ENV = 'development'
$env:FORGECOIN_ADMIN_ENABLED = '1'
$env:FORGECOIN_ADMIN_TOKEN = python -c "import secrets; print(secrets.token_urlsafe(32))"
$env:FORGECOIN_ADMIN_REVIEWER = 'local-reviewer-name'
$env:FORGECOIN_GOVERNANCE_DB = 'governance-dev.sqlite3'
python -m services.governance_api.admin
```

Open `http://127.0.0.1:8766` and enter the generated token. Retrieve it from the
local shell with `$env:FORGECOIN_ADMIN_TOKEN`; do not share it, put it in a URL,
or save it in source control. Use the same explicit development database path
for the wallet API if running both. Stop the service and clear the token environment
variable when finished. Restart with a new token to revoke the old credential.

The launcher binds only to loopback and disables proxy-header trust. Startup
requires the exact development opt-ins, a token of at least 43 ASCII characters,
and a configured reviewer identifier. Generate a random token as above: length
validation alone does not guarantee entropy. Every administrative API request
requires the separate bearer credential; wallet login tokens confer no admin
rights. Host and browser-origin checks reject cross-origin access and DNS rebinding.
All responses are non-cacheable, framing is blocked, and a strict content security
policy permits only local scripts/styles. The token is kept in browser memory;
Lock & clear removes it, displayed review data, and draft election inputs (including
staking weights). It cancels outstanding requests and ignores late responses from
previous sessions. Cancellation cannot undo an operation already accepted by the
server; sign in and refresh to check its outcome. Reloading also requires login.
Do not install untrusted browser extensions on this machine.

The dashboard lists the oldest 100 pending applications, supports reasoned
approval/rejection under the configured reviewer identity, and creates frozen
practice elections for all five constituencies. Staking requires a JSON mapping
of demo weights (at most 500 entries, integer values from zero to one trillion).
Evidence and statements are rendered as plain text, without fetching external
references. Turnout includes wallet and weight counts; aggregate yes/no/abstain
tallies are available only after closure. No individual choices are exposed.

Reviews and ballot writes now acquire SQLite write transactions before checking
state, preventing concurrent double decisions and ballots slipping past closure.
Election eligibility is read from the same transaction that creates the snapshot.

This is still a single trusted local operator with a shared credential, not
production administrator identity, reviewer quorum, anonymous voting, or a
tamper-evident audit system. Application decisions retain the existing local
audit history. Election operations retain election records but do not yet have
an independent operator audit log. All results remain non-binding, and the
public API's binding-vote restrictions are unchanged.

Run the complete governance tests:

```bash
python -m unittest services.governance_api.test_app services.governance_api.test_admin
node --check services/governance_api/admin_static/admin.js
node --test services/governance_api/test_admin_ui.cjs
```
