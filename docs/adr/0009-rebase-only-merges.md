# ADR-0009: Merge pull requests by rebase only

- **Status:** Accepted (amends [ADR-0003](0003-ci-and-release-strategy.md))
- **Date:** 2026-11-22

## Context

ADR-0003 allowed pull requests to be merged with **rebase** or **squash with a conventional PR title**, and the repository also allowed GitHub's default *merge commit*. The first PRs were merged with merge commits.

GitHub writes the PR title into the body of every merge commit. Because PR titles here are Conventional Commits, release-please parsed each merge commit as one more change, and the 0.1.0 and 0.1.1 changelogs listed several changes twice (the duplicates were removed by hand).

## Decision

- The repository allows **rebase merging only**; merge commits and squash merging are disabled in the repository settings.
- Every commit on a PR branch lands on `main` unchanged, so each commit must stand on its own as a Conventional Commit. This is already how branches are written (one small, buildable step per commit).
- Head branches are deleted automatically after merging, which also makes GitHub retarget the next PR of a stack to `main`.

## Alternatives considered

- **Squash merging only**: also yields one changelog entry per PR, but collapses the small, reviewable commits this project is organised around into one, and the PR title becomes the only record of the change.
- **Keep merge commits and filter them out**: release-please has no option to ignore merge commits, so the duplicates would have to be removed by hand on every release.

## Consequences

- `main` has a linear history from this point on; the merge commits from before this decision stay where they are.
- A branch that is behind `main` must be rebased before merging, which GitHub does as part of the rebase merge when there are no conflicts.
