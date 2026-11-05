# Windows release provenance gate — 2026-11-05

This is a verification record, not authorization to publish a public miner/wallet.

## Official XMRig archive

- Upstream release: https://github.com/xmrig/xmrig/releases/tag/v6.26.0
- Asset: `xmrig-6.26.0-windows-x64.zip`
- Official and independently re-downloaded SHA-256: `bba8097cb37d9b458a1cb1137876b27cde6740d17fe4ccbc086ba07d87d9e147`
- Previously downloaded local archive SHA-256: `99fe357f055577123c395b323d585b4e8a326210b75fc73a47b88cc919e524` — rejected.
- Verified archive remains separate in the Windows Downloads folder. No unreviewed miner binary is included in current release candidate.
- Before redistribution: inspect executable hash, upstream licensing/source obligations, included WinRing0 driver, Defender findings, and clean-machine behavior. Do not suppress antivirus protections to ship.

## Genesis output

- Selected genesis transaction has 1,192,092,895 atomic FRG output; unlock height 60 is not a burn.
- Native consensus source `src/cryptonote_basic/forgecoin_prelaunch.h` contains a **permanent** mainnet ring-member policy: `output_allowed(true, 0) == false`.
- `Blockchain::scan_outputkeys_for_indexes` calls that predicate after resolving output creation heights; `tests/mainnet/genesis_ring_policy.cpp` tests exclusion at multiple ring positions.
- This is stronger than a mere documentation statement but **not** an end-to-end signed genesis-spend rejection proof. The required native adversarial transaction test must exercise validation after height 60 and assert rejection without modifying the frozen genesis identity.

## Public release gating

The source-only Windows CI build does not contain `forged.exe`, `forge-wallet-rpc.exe`, or `xmrig.exe`. Its success does not establish a functioning full miner/wallet installer. Do not remove the compiled mainnet lock or publish a public binary until native signed genesis-spend rejection, complete package provenance, clean-machine installation, and required release security checks have passed. Owner authorization alone is not evidence that these checks passed.
