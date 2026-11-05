# Windows release provenance gate — 2026-11-05

This is a verification record, not authorization to publish a public miner/wallet.

## Official XMRig archive

- Upstream release: https://github.com/xmrig/xmrig/releases/tag/v6.26.0
- Asset: `xmrig-6.26.0-windows-x64.zip`
- Official and independently re-downloaded SHA-256: `bba8097cb37d9b458a1cb1137876b27cde6740d17fe4ccbc086ba07d87d9e147`
- Previously downloaded local archive SHA-256: `99fe357f055577123c395b323d585b4e8a326210b75fc73a47b88cc919e524` — rejected.
- Verified archive extracted separately in Windows Downloads. The bundled `SHA256SUMS` manifest and independently calculated hashes agree: `xmrig.exe` = `6fa80698d7268f6e88aa88c06fb27ee99e1bcee747c2e76911e6206a5b1aeeb3`; `WinRing0x64.sys` = `11bd2c9f9e2397c9a16e0990e4ed2cf0679498fe0fd418a3dfdac60b5c160ee5`. These checks establish upstream file integrity, not driver trust or runtime safety. No miner binary is included in the current private release candidate.
- Before redistribution: inspect executable hash, upstream licensing/source obligations, included WinRing0 driver, Defender findings, and clean-machine behavior. Do not suppress antivirus protections to ship.

## Genesis output

- Selected genesis transaction has 1,192,092,895 atomic FRG output; unlock height 60 is not a burn.
- Native consensus source `src/cryptonote_basic/forgecoin_prelaunch.h` contains a **permanent** mainnet ring-member policy: `output_allowed(true, 0) == false`.
- `Blockchain::scan_outputkeys_for_indexes` calls that predicate after resolving output creation heights; `tests/mainnet/genesis_ring_policy.cpp` tests exclusion at multiple ring positions.
- This is stronger than a mere documentation statement but **not** an end-to-end signed genesis-spend rejection proof. The required native adversarial transaction test must exercise validation after height 60 and assert rejection without modifying the frozen genesis identity.

## Public release gating

The source-only Windows CI build does not contain `forged.exe`, `forge-wallet-rpc.exe`, or `xmrig.exe`. Its success does not establish a functioning full miner/wallet installer. Do not remove the compiled mainnet lock or publish a public binary until native signed genesis-spend rejection, complete package provenance, clean-machine installation, and required release security checks have passed. Owner authorization alone is not evidence that these checks passed.

## CI verification — 2026-11-05

- [Windows source QA run 41961848263](https://github.com/tgibbsz32/forgecoin/actions/runs/41961848263) completed successfully after the workflow began downloading and checking the official XMRig archive and both native component hashes on the Windows runner.
- [Frozen endpoint safety run 41961848325](https://github.com/tgibbsz32/forgecoin/actions/runs/41961848325) also completed successfully.
- The existing native genesis policy is enforced in `Blockchain::scan_outputkeys_for_indexes` before `vis.handle_output`, and `Blockchain::check_tx_input` returns false if the scanner fails. Both cached and direct database-output resolution paths converge on this check. This is a source-path audit, **not** an executed signed spend attack.
- Public binary packaging remains blocked until a signed native adversarial transaction exercises the rejection after height 60 on a disposable test chain, with no consensus identity changes.
