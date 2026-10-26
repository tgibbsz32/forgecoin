FORGECOIN DESKTOP - PRIVATE NEW-MAINNET PRELAUNCH WALLET
======================================================

Network: ForgeCoin FRG candidate (genesis nonce 20261026)
Genesis: 4bf18252cc83e0b0482b19b751e4409d415a4d8e281b13f32d0b153d77d2e02c
Mainnet status: GENESIS ONLY / NOT APPROVED FOR PUBLIC MINING.

Open "ForgeCoin Desktop.exe" in this extracted folder, with its bin folder
beside it. This test package uses newly compiled native ForgeCoin binaries.
No existing development-chain wallet data or balance is migrated.

WALLET
------
Select Wallet, enter a new filename (for example treasury-test) and a strong
password (at least 12 characters), then click Create. The app shows a 25-word
recovery phrase for offline recording. Close and reopen the wallet, or click
Restore with a NEW filename to verify the same public receiving address.

Click "Copy address" to copy the public address only. NEVER send the recovery
seed, wallet password, wallet files, spend keys or authenticated wallet RPC
credentials to ChatGPT, GitHub, a mining pool, cloud storage or an explorer.
The app intentionally does not offer a recovery-seed clipboard button.

The wallet service is protected by local HTTP Digest credentials on
127.0.0.1:39483. A privileged process on this computer may still inspect
credentials in the child process command line. Treat the PC as sensitive.

Wallet files: %LOCALAPPDATA%\ForgeCoin\wallets-mainnet-20261026
Blockchain:   %LOCALAPPDATA%\ForgeCoin\blockchain-mainnet-20261026
RingDB:       %LOCALAPPDATA%\ForgeCoin\ringdb-mainnet-20261026

NODE
----
The offline node may be started only for genesis inspection and wallet
testing. It uses RPC 127.0.0.1:39481 and, when offline, loopback P2P 39480.
No working public mainnet peers have been advertised yet.
Do NOT run the old development-chain daemon or import its blockchain LMDB.

MINING AND FUNDS
----------------
Solo and pool mining are deliberately disabled until the mainnet has
passed independent genesis/output-spendability, wallet/mining/pool and
cross-platform consensus acceptance tests and explicit launch authorization.
A public Stratum pool and actual payout service do not yet operate.
XMRig is NOT included in this private prelaunch package.
No FRG is being earned or paid through this setup.

The Genesis coinbase contains 11.92092895 FRG; permanent unspendability
remains unresolved. Do not advertise guaranteed zero spendable premine.
The 1% operator fee address is PUBLIC and controlled by the owner, not
by this application or an assistant.

See INSTALL.md, VALIDATION.md, TREASURY-WALLET.md and mainnet.identity.json.
Avoid funding an untested wallet before verifying recovery independently.
