# ADR-0003: GitHub Actions for CI and release-please for releases

- **Status:** Accepted
- **Date:** 2026-11-22

## Context

The project is developed through small pull requests against `main`. Every PR must prove it does not break the build, and `main` must be releasable at any time.
We also want versioning and a changelog without anyone hand-editing version numbers.

## Decision

**Tests workflow** (`.github/workflows/tests.yml`), triggered by pull requests targeting `main` and by pushes to `main`:

- `lint` job: `ruff check`, `ruff format --check`, `mypy`.
- `test` job: `pytest` with coverage on a Python 3.12 / 3.13 matrix.
- Installs with `uv sync --locked`, so an outdated lockfile fails the build.
- In-progress runs for the same ref are cancelled when a new commit is pushed.

**Release workflow** (`.github/workflows/release.yml`), triggered by pushes to `main`:

- [release-please](https://github.com/googleapis/release-please) reads [Conventional Commits](https://www.conventionalcommits.org/) on `main` and keeps a *release PR* open with the next version and the generated `CHANGELOG.md`.
- Merging that release PR tags `vX.Y.Z`, creates the GitHub Release and bumps `version` in `pyproject.toml`.
- When a release is created, a follow-up job builds the sdist and wheel with `uv build` and attaches them to the release. Later features add more release artifacts (for example the Docker image).
- While the project is pre-1.0, `feat:` bumps the minor version and `fix:` bumps the patch version.

**Branching and commit conventions**:

- One branch and one PR per feature, named `feat/<nn>-<topic>`; housekeeping uses `chore/`, `ci/`, `docs/`.
- Commits are small and follow Conventional Commits (`feat:`, `fix:`, `test:`, `docs:`, `ci:`, `build:`, `chore:`, `refactor:`).
- PRs are merged with **rebase** or **squash with a conventional PR title**, so every commit that lands on `main` is a conventional commit that release-please can parse.
- Features that depend on each other are opened as *stacked* PRs. When the lower PR is merged and its branch deleted, GitHub retargets the next one to `main` and the tests workflow runs on it.

## Alternatives considered

- **Tag-triggered releases (`on: push: tags`)**: simple, but someone has to choose the version and write the changelog by hand.
- **semantic-release**: comparable automation, but it releases on every merge to `main` and pulls in a Node.js toolchain. release-please's release PR gives a human checkpoint that fits a PR-oriented workflow.
- **Running tests again inside the release workflow**: duplicates the run already triggered by the same push; branch protection on `main` (required status checks) is the right place to enforce green builds.

## Consequences

- The repository setting *Settings → Actions → General → Allow GitHub Actions to create and approve pull requests* must be enabled for release-please to open its PR.
- Branch protection on `main` should require the `Lint and type-check` and `Tests` checks.
- Pull requests opened with the default `GITHUB_TOKEN` do not trigger other workflows, so release-please's PR would never get those required checks. The release workflow therefore uses a `RELEASE_PLEASE_TOKEN` secret when it exists: a fine-grained personal access token (or GitHub App token) scoped to this repository with *Contents* and *Pull requests* read/write. Without the secret it falls back to `GITHUB_TOKEN`, and the release PR's checks have to be started by hand (for example by closing and reopening it).
- Commit message discipline matters: a non-conventional commit on `main` is ignored by the changelog.
