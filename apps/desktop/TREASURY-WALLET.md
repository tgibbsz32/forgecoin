# ForgeCoin official pool fee treasury — owner setup

**New-mainnet wallet kit, prelaunch only.** This desktop build targets the
replacement chain with genesis nonce `20261026` and native mainnet address
prefix `190`. The previous development chain and nonce-20261020 candidate
are archived. Their addresses, balances and chain data are **not migrated**.

## What you own and control

Create a **dedicated pool operator fee wallet**, different from the pool's
operational block-reward wallet and different from your personal wallet.
The operator fee is **1% of eligible pool mining rewards** after verified
allocation and maturity. It is not a premined allocation.

**You alone retain the seed phrase, encrypted wallet files, wallet password,
and private spend key.** Do not send them to ChatGPT, GitHub, Oracle, the
pool statistics site, remote SSH terminals, or anyone else. The official
pool needs only your **public FRG receiving address** as
`pool-fee-wallet`. No server needs your seed to send FRG to it.

## Once the signed/verified new-mainnet wallet package is provided

1. Extract the entire `ForgeCoin-Desktop` folder on your trusted Windows
   PC. Verify its published SHA-256 checksums and the embedded manifest's
   **genesis hash** against the official new-mainnet release announcement.
   Do not use binaries from the old development chain or candidate.
2. Create a new wallet **in the desktop app** with a distinctive name such
   as `pool-operator-fees-mainnet-20261026`. Use a new, strong wallet
   encryption password. This is a separate wallet from pool block rewards.
3. In the Receive tab, copy the **public wallet address** and check its
   beginning/end character groups against the original wallet display.
   The new-mainnet prefix is `190` in native Base58 decoding; the
   visible first characters of a Base58 address are not the integer 190.
4. Display the wallet's mnemonic recovery phrase **locally**, write it on
   offline media, and make an independently protected backup. Do not
   photograph or synchronize it to cloud notes. Back up the encrypted
   wallet files separately.
5. Restore the wallet in an independent new, non-overwriting directory
   on the same trusted PC and verify that the recovered public address
   exactly matches the original before depositing funds.
6. Supply **only the public receiving address** for operator-fee
   configuration. The private wallet remains on your computer. Inspect
   credited fee receipts with the owner wallet, rather than giving the
   mining pool permission to spend them.

An additional `bin/forge-wallet-cli.exe` is included with the verified
desktop package, so a GUI problem does not strand your funds. The CLI is
interactive and must only be used from a trusted local session. **Never**
pass a seed phrase or password as a command-line argument.

## Prelaunch restrictions

- The wallet kit deliberately disables **solo and pool mining** until a
  reviewed new-mainnet genesis hash and launch authorization are published.
- If no new-mainnet daemon is available, the wallet may show connectivity
  warnings. No balance or incoming-payment verification is possible
  until the official chain is launched.
- Do not transfer valuable FRG until your wallet's chain identity is verified
  and the pool has completed maturity/payout/reorganization testing.
- The mainnet genesis currently includes **11.92092895 FRG** in a
  coinbase output whose permanent unspendability has **not been proven**.
  This is a launch blocker, not a spendable founder allocation.
- The mining-pool C backend must reject an empty, invalid, wrong-network
  or same-as-operational operator fee wallet at startup. Payouts are still
  disabled and the pool has **not earned or transferred any FRG fees**.

## Where the wallet lives

The Windows Forms desktop stores its new-mainnet wallet, chain and ring
data in directories suffixed `-mainnet-20261026` under
`%LOCALAPPDATA%\ForgeCoin`. Old wallet files under
`%LOCALAPPDATA%\ForgeCoin\wallets` are not moved or deleted.

A wallet created for you *by someone else*, including an AI assistant,
would expose its secret to that party. Always generate the final treasury
wallet yourself.
