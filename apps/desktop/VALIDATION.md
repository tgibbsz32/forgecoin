# ForgeCoin Desktop Phase 3 validation

- GUI compiled as a Windows desktop executable and completed a startup smoke test.
- Packaged `forged.exe` generated and loaded the ForgeCoin genesis hash `a9651ecf2aec7c92443e7e7e8bfd4c6e6d5de3de8a52c04f9a98274d5031f9b9`.
- Two packaged nodes connected locally and synchronized at height 6 with tip `d096a8db42572c123adcd90898e28b91123cbe9fcafe5798e696506456aaf87f`.
- The packaged daemon accepted `start_mining`, reported RandomX, one active thread, and approximately 307 H/s during the check.
- The daemon accepted `stop_mining` and reported success.
- Offline bootstrap mode also mined with zero peers: `start_mining` returned `OK`, one RandomX thread became active at approximately 226 H/s, and `stop_mining` returned `OK`.
- The packaged wallet RPC opened a ForgeCoin wallet using 8-decimal precision, returned a ForgeCoin address beginning `GAcHPyLxjr77`, and returned its balance.
- Receive-address generation created subaddress index 1, address listing returned both wallet addresses, and saved-recipient add/list/delete completed successfully.
- Native RPC services bind only to loopback in the GUI. P2P listens on TCP 19480.
- The Pool Mining section uses official XMRig 6.26.0 for Windows x64. Its release archive matched SHA-256 `bba8097cb37d9b458a1cb1137876b27cde6740d17fe4ccbc086ba07d87d9e147`.
- XMRig's live API is bound to `127.0.0.1:19483`; its GPLv3 license and matching v6.26.0 source archive are included.
- Rendered interface previews confirmed the Node, Wallet, Addresses, Explorer, Mining, and Pool Mining actions are visible at the application's default 1040×760 window size.
- The Wallet preview confirmed Close Wallet and Recovery Seed are unobstructed. The Mining preview confirmed Node Monitor and Miner Monitor render as separate status panels.
- A compact 900×680 render confirmed that the mining thread selector, Start Mining, Stop, and status controls remain inside the window.
- Periodic node, wallet, solo-miner, and pool status requests use background workers with overlap protection so delayed RPC responses do not block the interface thread.
- The Explorer reads the local daemon only and supports recent-block listing plus block-height, block-hash, and transaction-ID lookup.
- A live local-daemon check returned chain height 1, one recent-block row, and a successful block-0 lookup.

Two inherited Phase 3 defects are corrected in this source tree:

1. The daemon checkpoint source no longer loads Monero's embedded 7,240 precomputed mainnet hashes. They prevented the ForgeCoin chain from entering synchronized state below height 7,240.
2. The wallet formatting source accepts ForgeCoin's 8-decimal monetary precision. The inherited validator previously rejected wallets after creation.

These corrections do not change the ForgeCoin genesis block, network identity, v16-from-height-1 schedule, rewards, emission parameters, or proof-of-work rules.
