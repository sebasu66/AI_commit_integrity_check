# AI Commit Integrity Methodology

## Problem

Long-running AI-assisted projects can drift even when individual changes compile and pass tests. An agent may work from stale context, misremember project policy, or unintentionally change direction while producing technically valid code.

This methodology adds a small deterministic context gate alongside normal engineering quality gates.

## Principles

1. **KISS.** The integrity mechanism must stay cheaper than the work it protects.
2. **Correct path first.** It is designed for cooperative developers and agents, not adversarial security.
3. **Deterministic gates.** Blocking checks must have objective pass/fail results.
4. **External guardrail.** Critical validation logic is maintained outside the target repository.
5. **Project truth stays with the project.** The target repository owns its `SKILL.md` and technical tests.
6. **Stale context expires.** Any meaningful update to `SKILL.md` rotates every context marker.
7. **AI supervision is advisory.** Conceptual/project-management review can flag drift but is not a deterministic authority.

## Structured SKILL

A participating project keeps one authoritative `SKILL.md`. Each required section has a marker managed by this framework.

Example:

```markdown
# Project Skill

<!-- AICI:BEGIN id=mission marker=7K2M -->
## Mission
...
<!-- AICI:END id=mission -->

<!-- AICI:BEGIN id=architecture marker=P4XR -->
## Architecture
...
<!-- AICI:END id=architecture -->
```

The marker is not secret. Its purpose is to make current context mechanically distinguishable from stale context.

## Context key

The context key is the ordered concatenation of all current section markers:

```text
7K2M-P4XR-...
```

Before integrating work, the author/agent reads the current `SKILL.md` and supplies the current key as a commit trailer:

```text
AI-Context-Key: 7K2M-P4XR-...
```

The validator calculates the expected key independently and rejects a stale or incorrect value.

## Marker rotation

If `SKILL.md` changes, all markers are regenerated. No attempt is made to decide which sections are semantically affected.

This is deliberate: any skill update invalidates previous context and requires the next agent to read the current file again.

Marker rotation is mechanical, not subjective.

## Quality gates

This framework complements project-specific checks such as:

- formatter
- linter
- compiler/parser
- unit tests
- integration tests
- complexity/structure checks
- build/export checks
- end-to-end tests

The target project may run these itself or expose them through a reusable workflow. AI Commit Integrity does not replace them.

## Supervisory review

An optional second AI can review accepted changes as a project supervisor. Its job is to look for conceptual drift, contradictory implementation claims, architecture erosion, unnecessary complexity, and technical debt.

That review should produce findings for discussion. It should not silently rewrite policy or override deterministic checks.

## Trust boundary

The target repository should contain only a minimal caller. The implementation of the integrity validator and supervisor instructions live in this repository.

For stronger protection, target branch rules should require the external integrity status check and restrict who can change the pinned version of the external workflow.

## Versioning

Consumers should pin a released tag or immutable commit SHA of this repository. Updates to the integrity framework are then explicit rather than silently inherited.
