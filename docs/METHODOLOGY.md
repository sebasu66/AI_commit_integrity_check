# AI Commit Integrity Methodology

## Problem

Long-running AI-assisted projects can drift even when individual changes compile and pass tests. An agent may work from stale context, misremember project policy, or unintentionally change direction while producing technically valid code.

This methodology adds a small deterministic context gate alongside normal engineering quality gates.

## Principles

1. **KISS.** The integrity mechanism must stay cheaper than the work it protects.
2. **Correct path first.** It is designed for cooperative developers and agents, not adversarial security.
3. **Deterministic gates.** Blocking checks have objective pass/fail results.
4. **External guardrail.** Critical validation logic is maintained outside the target repository.
5. **Project truth stays with the project.** The target repository owns its `SKILL.md` and technical tests.
6. **Stale context expires automatically.** The challenge is derived from the complete current skill content.
7. **No marker maintenance.** The skill contains normal project documentation, not hidden verification fields.
8. **AI supervision is advisory.** Conceptual/project-management review can flag drift but is not a deterministic authority.

## Project SKILL

A participating project keeps one authoritative `SKILL.md`. It should be short enough to reread before a task and complete enough to restore the operational context required to work safely.

A useful skill covers:

- project mission and success criteria;
- non-negotiable architecture boundaries;
- development and deployment policy;
- active state and next milestone;
- technology baseline and current-documentation expectations;
- completion/evidence criteria.

Task definitions should begin by telling the contributor or coding agent to review the current skill and explaining why: maintaining project quality and direction depends on operating from current context.

## Context challenge

AICI normalizes the skill text, tokenizes its words, hashes the complete normalized document, and uses that digest to select a small set of deterministic word positions.

Example:

```text
W42 W8 W119 W31 W74 W16
```

`W42` means the 42nd normalized word of the current `SKILL.md`.

The response consists of the selected words in challenge order, case-insensitively joined by `-`, and is supplied as a commit trailer:

```text
AI-Context-Key: selected-words-from-current-skill
```

The validator independently derives the same challenge and expected response. An absent, stale, or incorrect response fails the check and reports the current word-position challenge.

## Automatic invalidation

There is no marker rotation workflow.

Any meaningful `SKILL.md` edit changes the normalized document hash. The hash drives the challenge positions, so the current challenge changes automatically and a context key derived from the previous skill version becomes stale.

Line-ending differences are normalized so a Windows/Unix newline conversion alone does not invalidate context.

This deliberately avoids semantic classification. The framework never tries to decide which section an edit affects: the complete skill is the context unit.

## Quality gates

This framework complements project-specific checks such as:

- formatter;
- linter;
- compiler/parser;
- unit tests;
- integration tests;
- complexity/structure checks;
- build/export checks;
- end-to-end tests.

The target project may run these itself or expose them through a reusable workflow. AI Commit Integrity does not replace them.

## Supervisory review

An optional second AI can review integrated changes as a project supervisor. Its job is to look for conceptual drift, contradictory implementation claims, architecture erosion, unnecessary complexity, and technical debt.

That review produces findings for discussion. It should not silently rewrite policy or override deterministic checks.

## Trust boundary

The target repository should contain only a minimal caller plus its project-owned `SKILL.md`. The implementation of the integrity validator and generic supervisor instructions live in this repository.

For stronger protection, target branch rules should require the integrity status check and restrict who can change the pinned version of the external workflow or the branch-protection policy.

The mechanism is intentionally not designed to defeat a malicious contributor who writes custom automation to solve the challenge. It is a low-friction context discipline for cooperative AI-assisted development.

## Versioning

Consumers should pin a released tag or immutable commit SHA of this repository. Updates to the integrity framework are then explicit rather than silently inherited.
