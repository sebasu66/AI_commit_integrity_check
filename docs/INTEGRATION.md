# Target Repository Integration

The target repository keeps its own project knowledge. This repository supplies the reusable integrity mechanism.

## 1. Add SKILL.md

Start from `templates/SKILL.template.md` and replace the example content with the project's actual operational context.

Keep the skill readable. It needs no AICI markers or verification metadata. The challenge is derived directly from the complete current text.

Task definitions for contributors and coding agents should begin with an explicit instruction similar to:

> Read/review the complete current `SKILL.md` before implementation. It contains the current project protocol, direction and constraints. Integration requires a context challenge derived from that exact version of the skill.

This makes the reason for the mechanism clear instead of treating it as a secret exam.

## 2. Generate the challenge

The framework derives a deterministic challenge from the complete current skill. For example:

```text
W42 W8 W119 W31 W74 W16
```

Each reference means the numbered normalized word in `SKILL.md`.

For local/manual use with a checked-out copy of this framework:

```bash
python aici.py challenge --skill /path/to/target/SKILL.md
```

The challenge command prints positions only; it does not print the response.

## 3. Supply the context response

Read the current skill, take the words at the requested positions in challenge order, join them with `-`, and append one trailer to the integration commit message:

```text
AI-Context-Key: selected-word-selected-word-selected-word
```

Matching is case-insensitive.

If the skill changes, its document hash changes automatically, so the challenge changes and a key derived from the previous skill becomes stale. There is no marker rotation step.

## 4. Add the reusable integrity caller

Install a caller based on `templates/caller-integrity.yml` on the branch/event where the project considers work integrated, for example the validated path into `develop`.

The external reusable workflow checks out the target repository and validates the commit trailer against the target's current `SKILL.md`.

## 5. Pin the framework

Replace `<PINNED_SHA_OR_RELEASE_TAG>` with an explicit release tag or immutable commit SHA. Do not consume the framework from an unpinned moving branch in protected projects.

## 6. Protect the integration branch

Configure the target repository so the integrity check and the project's normal quality gate are required before protected work is accepted.

The target repository should not contain a second copy of the validator. Keeping the validator here prevents an ordinary feature change from weakening the rule it is being checked against.

## 7. Optional supervisor

`supervisor/REVIEWER_INSTRUCTIONS.md` defines the generic advisory reviewer role. A project can invoke an AI reviewer after its deterministic checks and provide the reviewer with the current skill, relevant project documents, and the diff.

The reviewer acts like a project-level supervisor: it can flag conceptual drift, contradictory implementation claims, architecture erosion and technical debt for discussion. It remains separate from the blocking deterministic context and technical gates.
