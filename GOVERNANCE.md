# PyiTOL Project Governance

This document describes the governance structure and decision-making process for the PyiTOL project.

## Roles and Responsibilities

### Project Lead

The Project Lead has overall responsibility for the direction, health, and sustainability of PyiTOL. Responsibilities include:

- Setting the project roadmap and release schedule
- Making final decisions when consensus cannot be reached
- Appointing and removing maintainers
- Ensuring adherence to the Code of Conduct
- Managing release publishing

### Maintainers

Maintainers are trusted contributors who have write access to the repository. Responsibilities include:

- Reviewing and merging pull requests
- Triaging issues and responding to community questions
- Ensuring code quality and test coverage standards are met
- Mentoring new contributors
- Participating in design discussions for significant changes

Maintainers are expected to remain active. A maintainer who has been inactive for six months may be asked to step down or transition to emeritus status.

### Contributors

Anyone who submits a pull request, reports an issue, improves documentation, or participates in discussions is a contributor. All contributions are valued and welcomed.

## Contribution Tiers

Contributors progress through the following tiers:

1. **Contributor** -- Anyone who has had at least one pull request merged.
2. **Committer** -- A contributor who has demonstrated sustained, high-quality contributions across multiple areas of the project and is granted triage access.
3. **Maintainer** -- A committer who has been nominated by an existing maintainer and approved by the Project Lead, granted write access to the repository.

## Decision-Making Process

The project follows a **lazy consensus** model:

- For routine changes (bug fixes, documentation, minor enhancements), a single maintainer approval is sufficient.
- For significant changes (new features, API changes, architectural decisions), at least two maintainer approvals are required, and the proposal should remain open for comment for at least 72 hours.
- If consensus cannot be reached, the Project Lead makes the final decision.

### Proposing Changes

Significant changes should be proposed via a GitHub Issue before implementation begins. The proposal should include:

- A description of the problem or motivation
- The proposed solution
- Alternatives considered
- Impact on existing users

## Code of Conduct

All participants are expected to follow the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). Reports of unacceptable behavior should be directed to the Project Lead.

## Amendments

This governance document can be amended by a pull request with approval from the Project Lead and at least one maintainer.
