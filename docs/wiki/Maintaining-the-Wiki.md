> **Current specification — 2026-10-26:** [Frozen mainnet parameters, tokenomics and release status](../CURRENT_MAINNET.md). Public launch is not authorized. Main-branch executables still implement legacy rules; these instructions are not proof of new-mainnet compatibility.

# Maintaining the ForgeCoin documentation hub

This `docs/wiki/` directory is the **reviewable documentation source** for a future optional GitHub Wiki mirror. Pages are written in portable Markdown with relative links and no embedded keys, addresses from disposable test wallets, mining block blobs or private infrastructure credentials.

## Canonical hierarchy

1. **Actual exact-build source and reproducible tests** establish implemented technical behavior.
2. **Reviewed release evidence and owner policy** establish acceptance and approved launch decisions.
3. `docs/wiki/Current-Status.md` summarizes known evidence and blockers **as of a date**.
4. `docs/wiki/Roadmap.md` summarizes intended phases and release gates.
5. Existing historical project docs, issue comments and PR bodies supply detail but may refer to superseded implementation or describe planned work.

Do **not** silently promote a research/fixture pass into “live,” “released,” “mineable,” “audited,” or “secure.” Update both status and underlying evidence whenever implementation changes.

## Change process

- Open a documentation PR with links to code commits, issue/PR references, release runs or operator reports.
- Use explicit dates for evidence snapshots; avoid undated “currently live” statements.
- State whether new work changes consensus, network identity, emission, genesis, wallet RPC, privacy, binaries or deployed services.
- Run the repository wiki-link checker (where available); check portable Markdown navigation under `docs/wiki/`.
- Cite and preserve original evidence; annotate stale docs rather than pretending they were always current.
- Never include secrets, spend/view keys, wallet mnemonics, real-wallet addresses or private chain templates in Markdown/test logs.
- Preserve separate old-chain, synthetic research and new candidate vocabulary.
- A GitHub Wiki tab is a **separate Git repository** (`forgecoin.wiki.git`). Until it is initialized/enabled, `docs/wiki/` is accessible via the repository and future mirroring requires an explicit publication step. Do not claim a mirror happened until its URL is verified.

## Documentation owner checklist

On each major checkpoint, review:
- [ ] [Current status](Current-Status.md) and issue counts
- [ ] [Roadmap](Roadmap.md), acceptance dates and economic parameters
- [ ] [Architecture](Architecture.md), deployed endpoints and safety boundaries
- [ ] [Software guide](Software-Guide.md), exact supported command/build prerequisites
- [ ] [Release verification](Testing-and-Release.md), independently reproduced evidence
- [ ] [FAQ](FAQ.md) and links from top-level [README](../../README.md)

The top-level `PROJECT_STATUS.md`, `ROADMAP.md`, `BUILDING.md` and component READMEs may retain older text. This hub identifies dated constraints; projects should reconcile those source documents instead of treating them as automatically current.
