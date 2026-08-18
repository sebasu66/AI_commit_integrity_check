# AI Commit Integrity Check

A lightweight, reusable methodology for keeping AI-assisted software projects aligned with their current project context, development rules, and quality gates.

The core principle is simple: make the correct path the easiest path.

This repository provides a central, reusable integrity layer that target repositories can call from GitHub Actions. Target repositories keep their own project knowledge in a structured `SKILL.md`; this framework provides deterministic context checks, marker rotation, protected validation logic, and optional supervisory review instructions.

## Goals

- Reduce context drift in long-running AI-assisted projects.
- Make stale project knowledge easy to detect.
- Keep critical validation logic outside the repository being validated.
- Avoid subjective or bureaucratic commit gates.
- Complement, not replace, linters, tests, build checks, and code review.
- Keep the integration in target repositories minimal.

## Intended flow

```text
Target repository
  SKILL.md + code + tests
        |
        v
small GitHub Actions caller
        |
        v
AI_commit_integrity_check
  context challenge
  marker validation
  protected policy checks
  optional supervisor instructions
        |
        v
GitHub status check / advisory review
```

## Status

Initial framework implementation is being developed. The first real integration target is BGO.
