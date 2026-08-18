# AI Commit Integrity Check

A lightweight, reusable methodology for keeping AI-assisted software projects aligned with their current project context, development rules, and quality gates.

The core principle is simple: **make the correct path the easiest path**.

A target repository keeps its current project knowledge in `SKILL.md`. This repository provides a reusable GitHub Actions validator that derives a deterministic challenge directly from the current skill text. There are no embedded markers, no quiz database, and no subjective blocking review.

## What it protects against

Long-running AI-assisted projects can drift even when individual changes compile and pass tests. A coding agent may start from stale context, remember an obsolete policy, or unintentionally change project direction while producing technically valid code.

AICI adds one cheap requirement before integration: the contributor must use the current `SKILL.md` to answer a small deterministic word-position challenge.

## Intended flow

```text
Target task
  1. Read/review SKILL.md before implementation
  2. Implement and test normally
        |
        v
commit / integration attempt
        |
        v
AI_commit_integrity_check
  derives challenge from current SKILL.md
  validates AI-Context-Key trailer
        |
        +---- normal project lint/tests/build gates
        |
        v
integration branch / DEV pipeline
```

If `SKILL.md` changes, its hash changes. That automatically changes the challenge and invalidates keys derived from the previous version. Nothing needs to be rotated or edited by hand.

## Context challenge

A challenge looks like:

```text
W42 W8 W119 W31 W74 W16
```

`W42` means the 42nd normalized word in the current `SKILL.md`. The response is those words, in challenge order, joined with `-` and supplied in the commit message:

```text
AI-Context-Key: word42-word8-word119-word31-word74-word16
```

The mechanism is intentionally designed for cooperative developers and agents, not adversarial security. It makes reading the current project context the obvious path and makes stale remembered context fail automatically.

## Separation of responsibilities

- **Target repository:** project `SKILL.md`, source code, tests, and project-specific quality checks.
- **This repository:** deterministic context validator, reusable workflow, methodology, and optional supervisor-review instructions.
- **Optional AI supervisor:** advisory project-management review for conceptual drift; it does not replace deterministic gates.

Consumers should pin a released tag or immutable commit SHA of this repository.

## Status

Initial framework implementation is under development. The first integration target is BGO.
