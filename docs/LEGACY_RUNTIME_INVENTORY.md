# Legacy implementation inventory — October 26, 2026

The [selected mainnet specification](CURRENT_MAINNET.md) is frozen and unlaunched. Main still includes the retired development-chain runtime, fixtures and configuration. This docs-only publication does not replace executable constants or activate new consensus. Do not deploy or retarget these files by changing only their ports. The complete identity, database isolation, difficulty, wallet, pool, explorer and packaging changes remain under review in draft PR #111; draft #114 covers Tauri audit alignment.

The repository scan found legacy parameter references in the following implementation/configuration/test files. These are explicitly **legacy-source references**, not current connection guidance. Historical protocol fixtures can retain their original values. Review replacements together with the complete implementation and matching tests before any release.

- `src/cryptonote_config.h`
- `services/official_pool/jtgrassie/pool.conf`
- `services/official_pool/tests/test_source_guards.py`
- `services/official_pool/jtgrassie/src/pool.c`
- `apps/desktop/Program.cs`
- `apps/explorer/app.py`
- `apps/desktop-tauri/src/App.tsx`
- `apps/desktop-tauri/src-tauri/src/engine.rs`

No production configuration, consensus constant, wallet path, keys or server service was changed by this documentation publication.
