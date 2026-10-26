> [Current mainnet specification, tokenomics and release status](docs/CURRENT_MAINNET.md) — October 26, 2026; prelaunch.

# ForgeCoin Governance




ForgeCoin consensus is enforced by software run independently by node operators. Repository maintainers can propose and publish changes but cannot remotely force independent nodes to accept them.

## Ordinary changes

Documentation, interface, packaging, logging, performance, seed-list, and compatible RPC changes can ship in normal releases when they do not change block or transaction validity.

## Consensus changes

A proposal that changes rewards, supply, proof of work, difficulty, block timing, transaction validity, or privacy rules must include:

1. a public written specification and rationale;
2. implementation and tests;
3. security and economic impact analysis;
4. an activation height far enough in the future for review and upgrades;
5. release binaries and checksums before activation;
6. explicit communication to node operators, miners, pools, wallets, and exchanges.

Nodes adopt a consensus change only by running compatible software. If incompatible rules retain independent support, a chain split is possible.

## Emergency changes

Privately reported vulnerabilities may require limited disclosure before a fix is available. Maintainers should publish the technical explanation and affected versions after users have a reasonable opportunity to upgrade.

## Network health

The project should publish observed pool concentration and encourage miners to move before one operator approaches majority hash power. No identity-based pool cap is enforced because miners can divide one operation across multiple identities.
