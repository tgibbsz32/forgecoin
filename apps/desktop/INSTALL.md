# ForgeCoin Desktop Phase 3

## Install and start

1. Extract the entire `ForgeCoin-Desktop-phase3` folder. Keep the `bin` folder beside `ForgeCoin Desktop.exe`.
2. Double-click `ForgeCoin Desktop.exe`.
3. If Windows SmartScreen appears, choose **More info**, then **Run anyway**. This test build is unsigned.
4. On the **Node** tab, optionally enter a known ForgeCoin peer as `host:19480`, then choose **Start Node**.
5. Allow ForgeCoin on private networks if Windows Firewall prompts. The node's P2P port is TCP `19480`. RPC ports `19481` and `19482` stay on `127.0.0.1` and must never be forwarded through the router.

If this is the only running ForgeCoin node, enable **Offline bootstrap mining** before starting it. This allows the first PC to mine without a synchronized peer. The node does not accept P2P connections while offline. Stop it, turn the option off, and restart when another ForgeCoin node is available.

## Create or open a wallet

1. Start the node and wait for **Synchronized**.
2. Open the **Wallet** tab.
3. Enter a simple wallet filename and password, then choose **Create** or **Open**.
4. When creating a wallet, write down the recovery seed and store it offline. Anyone with the seed can spend the wallet's funds.

Wallets, blockchain data, logs, and the shared ring database are stored under `%LOCALAPPDATA%\ForgeCoin`.

## Mine ForgeCoin

1. Keep the node running and synchronized with at least one ForgeCoin peer.
2. Open a wallet, or paste a ForgeCoin payout address on the **Mining** tab.
3. Select the CPU thread count and choose **Start Mining**.
4. Use **Stop** before shutting down or when you want to release the CPU.

Solo mode uses the RandomX CPU miner already compiled into `forged.exe`. XMRig is bundled for pool mode and is not required for solo mining.

## Mine with a pool

The **Pool Mining** tab includes XMRig 6.26.0 for future ForgeCoin-compatible RandomX pools. Enter the pool URL and port, wallet address or pool username, worker name, pool password, and thread count. Choose **Start Pool** to see live hash rate, accepted and rejected shares, share difficulty, ping, uptime, and miner output.

## Local blockchain explorer

The **Explorer** tab uses only the ForgeCoin daemon on `127.0.0.1`. Choose **Refresh** to list recent blocks. Search by block height, block hash, or transaction ID. Each full-node wallet therefore has an independent explorer and does not need a hosted explorer website.

The pool must explicitly support ForgeCoin's network and `rx/0` RandomX jobs. A Monero pool will not mine ForgeCoin. XMRig's license and corresponding source archive are included under `bin\xmrig`.

## Back up or remove

Back up `%LOCALAPPDATA%\ForgeCoin\wallets` and the recovery seed. To remove the application, close it and delete the extracted program folder. Delete `%LOCALAPPDATA%\ForgeCoin` only if the wallet and blockchain data are no longer needed.
