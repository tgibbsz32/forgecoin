# miniFORGE atomic USDC-for-mFRG exchange (Solana devnet prototype)

**Status: passed real on-chain local-validator acceptance. Public devnet deployment NOT performed. No live checkout, token sale or buyer payment authorization.**

This module does not alter the native FRG blockchain, miner, pool, Oracle explorer or mainnet release freeze.

## Program semantics

A dedicated Anchor 0.31.1 standard SPL Token escrow program exchanges exactly priced USDC for miniFORGE (mFRG). All token amounts are represented in integer atomic units (6 decimals).

- Hard-coded sale maximum: **5,000,000 mFRG**, i.e. **5,000,000,000,000 atomic units**. The other 5M future liquidity and 40M later-distribution reserves are not sale inventory.
- Sale PDA is derived from the mFRG mint. Its own program-controlled associated token account holds inventory.
- Initialization fixes the administrator, mFRG mint, USDC mint, USDC treasury token account, buyer cap, price and sale window. A sale starts PAUSED and requires the administrator to unpause after funding.
- A buyer signs a purchase specifying requested mFRG atomic units and the maximum USDC debit permitted. The on-chain price is calculated with u128 checked multiplication and rounds fractional micro-USDC charges **up**.
- The purchase transfers buyer-authorized USDC to the preconfigured treasury, then escrowed mFRG to the buyer **in one Solana transaction**. If delivery fails, the USDC transfer and program state also roll back.
- On-chain per-wallet cumulative purchases, sale-wide 5M limit, verified token program/mint/owner/vault and exact treasury account are enforced.
- Administrators can pause the sale; price changes require a pause and can happen only **before** scheduled start. Escrow withdrawal is only available **after** the sale ends and when paused.

This is a fixed-price prototype, not a full token distribution, quote-oracle service, legal offering, ID verification, refund service, or smart contract security audit. A per-wallet limit does not prevent Sybil purchases across wallets.

## Separate builds

**Local mock build:** feature local-mock-mints permits fresh fake 6-decimal mFRG and fake USDC mints on a private loopback-only Solana test validator. Never deploy that build to a public network.

**Devnet-pinned build:** default features require the existing development-only Solana devnet mFRG mint address 9HuHPHPeWZBtRJmhsne17pVzUkFYMf9Rg1ZwdH45ebkw. Its supply was 0 at last verification. Build feature devnet-only is **not** a cryptographic cluster restriction: the program must never be deployed on mainnet from this prototype.

Test program public ID: 5NrwtM49RAn5iQicbod539qxhqYRkV3ZpiBudoUCUGNY. Program private keypair and disposable faucet wallet exist only in ignored .secrets/ on the connected desktop, not the repository.

## Actual testing (October 27, 2026)

**5/5** Rust contract unit tests passed using Anchor 0.31.1. Native SBF build succeeded with platform-tools v1.58, including separately compiled devnet-mint-pinned and local-mock binaries. Anchor IDL generation passed.

**22/22 actual on-chain checks** passed on an isolated Solana 2.1 local validator bound to 127.0.0.1:18899. Two new mock SPL mints, a sale administrator, buyer, merchant and attacker were generated just for the test.

- The administrator initialized an initially paused sale PDA and deposited 5M test mFRG into its escrow vault.
- The buyer purchased 2 mock mFRG for exactly 0.100000 mock USDC, verified independently in both SPL token accounts and the contract state.
- A subsequent 1 mFRG purchase delivered exactly 1 mFRG and collected 0.050000 mock USDC. Cumulative balances: buyer 3 mFRG, merchant 0.150000 mock USDC, escrow 4,999,997 mFRG.
- A critical adversarial test **froze the buyer's mFRG account**. This deliberately made the *second* token-transfer instruction fail after the USDC debit was attempted. The entire transaction rolled back: buyer USDC, merchant USDC, buyer mFRG and vault balances were unchanged.
- Rejected unauthorized admin unpause, paused purchases, underpayment/slippage, treasury substitution, premature escrow withdrawal, cumulative per-wallet cap and absolute 5M sale-cap overflow.
- Program remained on local validator only; test validator subsequently shut down. No real USDC moved, no public blockchain transactions or minted mainnet mFRG were created.

Compiler warnings about the older sbfv2 processor label and Anchor macros were emitted, but compilation passed. The first build from a Windows-mounted WSL directory stalled; copying the sources into native WSL ext4 resolved it. The first SBF attempt failed due an older platform-tools Cargo edition mismatch; v1.58 succeeded. A later WSL service timeout occurred during recompilation while the local validator was running, but targeted validator shutdown restored WSL access and the separate devnet-pinned SBF build passed.

Program binary hashes:
- Local mock integration .so: f85fe59c441f7801f1e28adc5ec2603a3e0a18fb602570241c8231e742b0173e
- Devnet-mFRG-pinned .so: 588a73bbc7e477ac2cdcba04c76663b25cbb1daa591aedf5db53e2581d858445

Generated Anchor IDL and dependency Cargo.lock are preserved. The local program binaries, validator data, npm dependencies, and all private keypairs are excluded from Git.

## Reproducing safely

Use Ubuntu WSL with Cargo, Solana CLI 2.1 and Anchor CLI 0.31.1. Build in a *Linux filesystem*, not /mnt/c:

    cd /home/tgibb/miniforge-atomic-20261027
    cargo test -p miniforge_swap --lib --offline
    cargo build-sbf --tools-version v1.58 --arch sbfv2 --features local-mock-mints
    anchor idl build --out target/idl/miniforge_swap.json --program-name miniforge_swap

Start ONLY the isolated loopback test validator with the local mock binary (use a separate shell):

    solana-test-validator --ledger ./test-ledger --reset \
      --bind-address 127.0.0.1 --rpc-port 18899 --faucet-port 18909 \
      --bpf-program 5NrwtM49RAn5iQicbod539qxhqYRkV3ZpiBudoUCUGNY \
      target/deploy/miniforge_swap.so --quiet

Then from the Windows atomic-swap folder, with Node.js dependencies installed:

    npm ci --ignore-scripts --no-audit
    node tests/atomic-local.cjs
    node tests/guardrails.cjs

Stop the local validator after testing. The JS harness explicitly connects only to loopback and creates disposable local mint/token accounts.

## Public devnet deployment blocked

A new **disposable** devnet deployer (public address 6RHKWxfXnYkjJLsPmYiv7QUuhRLNHXvQAe9eMj3Xsc7d) has **0 devnet SOL**. The Solana CLI quoted approximately **1.52465024 devnet SOL** in rent for a 300 KB program account, excluding deployment overhead. A single request for 2 devnet SOL from the faucet was **rate-limited and failed**. We did not transfer from the user's existing devnet wallet, did not circumvent the rate limit, and did not deploy the contract.

The real mFRG Solana mainnet mint and 5M/5M/40M treasuries remain **unissued**. Devnet program compilation and local tests are not proof of a live devnet or mainnet token sale.

## Required before live selling

- Actually create and independently verify the mainnet mFRG mint, exactly 50M supply and separate 5M sale / 5M liquidity / 40M distribution accounts and custody. Review fixed-cap mint authority policy and token metadata.
- Pin production mFRG and actual Circle Solana USDC mint, exact price and signed sale terms, custodial/multisig authority and buyer restrictions. The devnet-mock mint feature must not be in production builds.
- Independently audit the Anchor on-chain program, PDAs, escrow authority, buyer accounting, mint/owner constraints, upgrades, time windows, fee computation and all refund/error paths. The program needs a full formal adversarial security review.
- Execute the same end-to-end swap on *public devnet* using the devnet-mFRG token and disposable token accounts after sufficient devnet test funding, plus integration with a Solana wallet adapter.
- Build independently checked customer receipts, sale activity ledger, emergency halt, USDC treasury security, anti-abuse safeguards, consumer disclosures, eligibility restrictions and legal compliance review.
- Integrate wallet transaction requests into the website only in a separately approved production release. The public GitHub Pages checkout and WSGI API **remain hard-disabled**.

**Do not ask users to send funds to this test program, program ID or disposable deployer.**
