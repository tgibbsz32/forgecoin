# Growing the ForgeCoin Network Without Paid Hosting

ForgeCoin can distribute software and organize a community without operating a conventional website. A public GitHub repository can act as the canonical source for code, releases, documentation, checksums, issues, and announcements.

## Recommended free foundation

1. Publish this repository under a dedicated ForgeCoin organization or maintainer account.
2. Attach portable wallets and checksum files to tagged GitHub Releases rather than committing binaries. GitHub describes Releases as the place to package software, release notes, and downloadable assets: <https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases>.
3. Enable GitHub Discussions for help, mining coordination, proposals, and announcements: <https://docs.github.com/en/discussions/quickstart>.
4. Add repository topics such as `cryptocurrency`, `privacy`, `randomx`, `proof-of-work`, `p2p`, `monero-fork`, and `cpu-mining`: <https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics>.
5. Enable GitHub Pages from the `docs` directory for a free static project site on a `github.io` address. GitHub Pages is available for public repositories on GitHub Free: <https://docs.github.com/en/pages/quickstart>.

This gives the project a repository, download page, support forum, issue tracker, and optional website without paying for a server or domain.

## Community channels

Use one durable, searchable channel and one real-time channel rather than opening many empty communities.

- **GitHub Discussions** should remain the official record for releases, upgrade notices, node lists, and proposals.
- **Matrix** is a strong real-time option because rooms can federate across independent homeservers: <https://matrix.org/docs/communities/getting-started/>.
- **Discord** is easier for many new users and servers are free, but it is centrally hosted: <https://support.discord.com/hc/en-us/articles/33023827550359-Discord-Server-Setup-Guide>.
- **Reddit** can provide a public discussion and discovery channel: <https://support.reddithelp.com/hc/en-us/articles/360043044012-How-do-I-create-a-community>.

Avoid repetitive promotions across unrelated communities. Publish useful technical material: reproducible release checksums, mining guides, node uptime reports, development updates, and clear risk disclosures.

## Peer discovery without a website

A website is not involved in normal P2P operation. Nodes need one initial contact and then exchange peer information. During bootstrap:

- publish several volunteer `host:19480` addresses in a pinned GitHub Discussion;
- include two or more stable seed addresses in a future release only after their operators agree;
- encourage users to run listening nodes and forward TCP 19480;
- maintain seed nodes with different operators and hosting providers;
- retain manual `--seed-node` and `--add-peer` support so the network can recover if defaults disappear.

Seed nodes help newcomers discover peers. They do not decide which blocks are valid and cannot change consensus rules.

## First 90 days

### Weeks 1 and 2

- Publish source, whitepaper, checksums, and the first signed or clearly labeled unsigned release.
- Recruit three to five independent node operators.
- Recruit at least three miners on different internet connections.
- Publish current total hash rate, peer count, and known limitations weekly.

### Weeks 3 through 6

- Add a second independently operated pool or prioritize solo mining.
- Run a public transaction and recovery test with small amounts.
- Invite code review focused on network identity, emission, seed configuration, wallet safety, and build reproducibility.
- Document issues and fixes in public release notes unless disclosure would expose an unpatched vulnerability.

### Weeks 7 through 12

- Add stable seed nodes from at least two operators.
- Publish reproducible build instructions and signed checksums.
- Test upgrade coordination at a future height before proposing economic changes.
- Approach directories, mining communities, or exchanges only after the network has independent hash power and a reliable release process.

## Content that attracts useful participants

- A two-minute video showing node startup, wallet recovery, local explorer use, and solo mining.
- A weekly network report with height, observed hash rate, node count, pool distribution, release version, and open risks.
- A CPU mining comparison that reports hardware, threads, power draw, and hash rate without exaggerated earnings claims.
- A technical article explaining why every wallet can use its own block explorer.
- Contributor tasks labeled for documentation, Windows packaging, Linux builds, seed operation, pool integration, and security review.

## Release safety

Each release should include the version tag and source commit, SHA-256 checksums, supported operating systems, upgrade urgency and activation height if applicable, known limitations, and a link to the security-reporting policy.

GitHub blocks normal Git objects above 100 MiB and recommends distributing large generated binaries outside source history: <https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github>.
