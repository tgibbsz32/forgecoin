ForgeCoin Desktop — Phase 3
===========================

Run "ForgeCoin Desktop.exe". The program stores all blockchain, wallet, and log
files under %LOCALAPPDATA%\ForgeCoin.

Node
----
Choose Start Node. Leave Exclusive peer blank for normal peer discovery, or enter
a known ForgeCoin peer such as host:19480 before starting. The node listens for
ForgeCoin P2P traffic on TCP 19480. Its control port is bound to 127.0.0.1:19481.

For the first node on a network, enable Offline bootstrap mining before choosing
Start Node. This marks the local chain ready for mining without a second PC, but
disables P2P while the mode is active. Stop the node and turn the option off when
you want it to connect to other ForgeCoin nodes.

Wallet
------
Start the node, then enter a wallet filename and password. Choose Create for a new
wallet or Open for an existing wallet. The wallet service binds only to
127.0.0.1:19482. Keep the wallet password and seed phrase private. Back up the
wallet files from %LOCALAPPDATA%\ForgeCoin\wallets. A newly created wallet shows
its recovery seed once, and Recovery seed displays it again while the wallet is
open.

Explorer
--------
The Explorer tab reads the blockchain directly from the ForgeCoin node running
on this computer. It shows current chain statistics, recent blocks, and block or
transaction lookup without depending on a hosted block-explorer website. Every
full-node wallet can run its own copy. ForgeCoin privacy prevents the explorer
from revealing private sender, recipient, or transferred amount information.

Mining
------
Start the node, open a wallet (or paste another ForgeCoin address), choose a CPU
thread count, and choose Start Mining. The GUI uses the RandomX miner built into
forged.exe. Mining stops when the node is stopped. This first package does not
use XMRig for solo mode; the built-in miner is sufficient for compatibility
testing and small-network solo mining. The daemon must have synchronized with at least one
ForgeCoin peer before it will accept mining work.

Pool Mining
-----------
The Pool Mining tab uses the bundled official XMRig 6.26.0 Windows x64 backend.
Enter the future ForgeCoin pool's host and Stratum port, your wallet address or
pool username, worker name, password, and thread count. It shows live hash rate,
accepted and rejected shares, share difficulty, pool connection, ping, uptime,
algorithm, and XMRig output. A ForgeCoin-compatible RandomX pool must exist before
this mode can submit useful shares.

This package is based on ForgeCoin tag forgecoin-phase3 and is an unsigned test
build. Windows may show a SmartScreen warning because it does not have a commercial
code-signing certificate.

Periodic node, wallet, solo-miner, and pool status requests run outside the
window thread so a slow daemon response does not freeze or stutter the interface.

The packaged daemon disables the 7,240 precomputed Monero block hashes that were
still embedded in the Phase 3 executable. Those hashes do not belong to ForgeCoin
and prevented a new ForgeCoin chain from reaching the daemon's synchronized state.
No consensus constants or ForgeCoin checkpoints are changed.

The packaged wallet service also enables the 8-decimal display precision selected
by Phase 3. The original binary's inherited formatting validator rejected that
precision even though ForgeCoin's monetary constants require it.
