# ForgeCoin member registration preview

This implementation adds `docs/member-registration.html`, a public **disabled preview** and a local development-only registration form. It is **not production-ready**; no binding votes or staking deposits are available.

From the repository root (Windows PowerShell):

```powershell
$env:FORGECOIN_GOVERNANCE_DB = 'governance-dev.sqlite3'
python -m uvicorn services.governance_api.app:app --host 127.0.0.1 --port 8765
```

Open **http://127.0.0.1:8765/member/registration** on the same PC. It requires an installed, compatible Phantom browser wallet with `signMessage` support. Use a **disposable test wallet**. The page obtains a challenge from `POST /auth/challenge`, requests an Ed25519 wallet signature, verifies via `POST /auth/verify`, and holds the resulting development bearer token **in memory only**. It can submit miner, developer, and community applications with `POST /applications` and read your status through `GET /applications/mine`.

The matching GitHub Pages page is **read-only**. Remote registration is disabled. The local page and assets are served only for loopback clients with a localhost/127.0.0.1 host. No CORS is enabled. The API must not be opened to the internet or reverse-proxied. Login does **not** prove unique human identity, authorize a ballot, or prove stake or mining activity.

Known limitations: login sessions are lost when the API restarts, signing-wallet compatibility has not been verified in an actual wallet browser, production SIWS domain/origin binding and deployment CSRF/security controls remain outstanding, private evidence storage is not provided, reviewers are not fully authenticated, and raw proof documents must **never** be uploaded here. There is no Solana devnet contract or staking connection.

Tests: `python -m unittest services.governance_api.test_app`. SQLite context manager connections are now closed on exit so temporary Windows test databases can be removed.
