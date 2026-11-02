# ForgeCoin (FRG) Governance Charter — Proposed Framework

**Draft adopted as a project design direction: November 1, 2026. Not ratified, not binding, and not an active voting system.**

## 1. Priority, purpose, and jurisdiction

Native **ForgeCoin (FRG)** is the primary network: a RandomX proof-of-work cryptocurrency with a 50 million FRG primary-emission reference (**not** a hard cap), perpetual 0.20 FRG per-block tail emission, and a planned 1% fee for eligible rewards in the project-operated pool. The network's launch, independent miners, nodes, wallets, explorer, pool and reliability take priority over any auxiliary token.

This charter defines a future **FRG stakeholder advisory assembly**. It cannot alter blockchain consensus, transfer funds, control private repositories or infrastructure, impose fees, create legal rights, or authorize expenditures by itself. Consensus upgrades still require implementation, security review, compatible releases and voluntary independent node adoption.

**miniFORGE (mFRG)** is a **future development proposal only**. There is no live sale, deployed mint, bridge, guaranteed exchange, staking entitlement, mFRG vote, or automatic approval of prior tokenomics. Any mFRG plan must be proposed anew to the mature FRG community and separately approved under governance procedures subsequently ratified. No mFRG participation confers FRG governance power.

## 2. Advisory assembly and chamber weights

The four stakeholder chambers have the following **proposed** shares of aggregate advisory vote weight, totaling 100%:

| Chamber | Share | Participation basis |
| --- | ---: | --- |
| Verified FRG miners | **35%** | Demonstrated proof-of-work contribution over a rolling 90-day eligibility period |
| FRG holders | **25%** | Privacy-preserving wallet-control and eligibility proofs; no transfer of custody |
| Recognized contributors and collaborators | **20%** | Independently reviewed technical, security, documentation, localization or ecosystem contributions over the preceding six months |
| Independent full-node operators | **20%** | At least 60 days of verifiable operation and independent network validation |

The percentages distribute **advisory influence**, not mining rewards, FRG ownership, treasury allocations or consensus authority. Participants may qualify for multiple chambers, subject to anti-duplication and conflict disclosures. No fixed number of council seats is implied.

### Eligibility and privacy

A public wallet address is not proof of unique identity, holder balance or miner ownership. Pool accounting, split hashrate, rented infrastructure, multiple nodes and wallet splitting are susceptible to Sybil manipulation. Eligibility mechanisms, privacy-preserving holder proofs, pool attestations, challenge-response, nullifiers, independent review, appeal procedures and affiliation controls **must be designed and audited** before weighted results are described as representative.

Initial proposed weighting: capped diminishing-return weight for verified mining contribution; capped square-root weighting for holder eligibility; one verified vote per recognized contributor; and one verified vote per independently controlled node operator. Target a maximum **5% of any chamber's weight per verified participant or affiliated group** where affiliation can be established. These are research targets, not implemented rules; privacy and identity limits may require changes.

## 3. Timing of the first governance round

The **first advisory governance round is targeted for no earlier than six months after independently verified public FRG mainnet launch**, and **only if readiness checks pass**. No calendar date is set. A missed readiness gate delays the round; there is no automatic activation.

Proposed minimum readiness checks:

- At least six months of stable public FRG operation with no unresolved critical consensus security defect.
- Verified independent mining, full-node operation, wallet and pool functionality, and a documented incident-response process.
- Evidence of broad participation, with provisional targets of 100 independently verified full-node operators, 50 independent qualifying miners, 20 recognized contributors, and 200 eligible holder voters. These are targets for assessment, not proof of decentralization.
- Published mining-pool concentration, infrastructure-provider concentration and geographic distribution assessments where privacy and data permit.
- Publicly reviewed voter eligibility rules, privacy and Sybil-resistance testing, independent security review, challenge and appeals process, and accessible voting interface.
- Published notice and public discussion of the first round's scope and ballots.

If these conditions cannot be met safely, conduct an **open, unweighted, nonbinding consultation** instead of claiming a representative four-chamber election.

## 4. Advisory process

Anyone may submit an FRG Governance Proposal (FGP) through the public repository or designated public forum. Each FGP should include motivation, scope, affected stakeholders, technical dependencies, risks, costs, alternatives, security/privacy implications and an implementation plan.

Proposed normal cycle: **14 days** open discussion, **7 days** formal review, a published eligibility snapshot, then **7 days** voting. Material protocol or charter proposals receive **at least 30 days** public review. Publish anonymized or privacy-preserving vote totals per chamber, turnout, methodology, disputes, and a clear **NONBINDING ADVISORY** designation.

Suggested advisory decision thresholds (not ratified):

| Advisory proposal | Approval target |
| --- | --- |
| Routine community priorities | 55% of valid weighted votes |
| Proposed voluntary treasury grants or spending policies | 60% |
| Charter amendment recommendation | 70%, with majority support in at least three chambers |
| Consensus or hard-fork recommendation | 75%, with majority support in all four chambers |

For ordinary advisory ballots, target at least 20% aggregate eligible voting weight participating and meaningful turnout from at least three chambers. For charter and consensus recommendations, target at least 30% aggregate participation and representation from every chamber. Failure to reach quorum means **no advisory endorsement**, not automatic rejection or authorization.

## 5. Limits on authority and future ratification

**All governance remains advisory until separately ratified.** Even a unanimous advisory ballot does not create binding authority. A future binding charter must be separately drafted, publicly reviewed, independently security-assessed, and explicitly ratified through a defined transition process. That future instrument must state the effective date, electorate, powers, limits, legal/custody arrangements, recall procedures, emergency response, dispute resolution and amendment rules.

No founder veto, automatic holder plutocracy, compulsory staking or fixed council seats are authorized by this draft. Initial project coordination remains responsible for its own infrastructure and assets, subject to existing legal and operational rights.

## 6. Treasury, miners and protocol safeguards

No native FRG founder/team/ICO/governance premine is authorized. The project-operated mining pool's proposed 1% operator fee is **not automatically a community treasury tax**. Any future voluntary treasury or dedicated fee contribution requires explicit disclosure, custody arrangements, accounting and applicable approvals. No unimplemented multisignature, payout, bonding or staking feature should be presented as live.

A governance vote cannot change RandomX rules, block rewards, tail emission, wallet privacy or node consensus by decree. Protocol proposals require technical specifications, adversarial testing, independent review, coordinated release engineering and actual voluntary adoption.

## 7. Future mFRG decision gate

mFRG and any Solana integration, sale, treasury distribution, game payments, FRG bridge or conversion mechanism remain **unapproved future proposals**. After FRG governance matures, the community may evaluate them through a dedicated FGP with transparent economics, technical feasibility, security audit, legal review, conflicts disclosure, treasury custody and explicit scope of authority. Historical mFRG plans are not binding commitments or an automatic roadmap mandate.

## 8. Publication and revision

Publish this document as a **proposed FRG governance framework**, not as an enacted constitution. Record changes through reviewed pull requests, preserve historical context in Git history, and maintain a public decision log. The first six-month advisory round and any later binding-governance transition are contingent on demonstrated network maturity.

Related: [FRG mainnet specification](docs/CURRENT_MAINNET.md), [technical roadmap](ROADMAP.md), [current project status](docs/project-status.html), [future mFRG proposal](docs/MFRG_50M_CITY_TOKENOMICS.md).
