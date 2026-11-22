# ADR-0001: Record architecture decisions

- **Status:** Accepted
- **Date:** 2026-11-22

## Context

This project is reviewed through pull requests and evaluated, among other things, on code quality and on how clearly the repository is documented.
A reviewer reading a diff sees *what* changed, but not *why* a library, a schema shape or a workflow was chosen over the alternatives.
That reasoning is otherwise lost in chat threads or in the author's head.

## Decision

We keep lightweight Architecture Decision Records (Michael Nygard's format, with an extra "Alternatives considered" section) in `docs/adr/`.

- Any decision that is costly to reverse or that a reviewer would reasonably question gets an ADR.
- The ADR is committed in the same pull request as the change it justifies, so the reviewer reads the reasoning next to the code.
- ADRs are immutable once accepted; a change of direction is a new ADR that supersedes the old one.

## Alternatives considered

- **Only README "Design decisions" section**: fine for a summary, but it grows into an unstructured list and loses the alternatives and trade-offs. The README links to the ADRs instead.
- **PR descriptions only**: they disappear from the working tree and are tied to the hosting platform.

## Consequences

- Each feature PR carries one or more short Markdown files in addition to code.
- Newcomers can read `docs/adr/` in order to understand how the project got to its current shape.
