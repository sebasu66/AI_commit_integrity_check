# Target Repository Integration

The target repository keeps its own project knowledge. This repository supplies the reusable integrity mechanism.

## 1. Add a structured SKILL.md

Start from `templates/SKILL.template.md` and replace the example content with the project's actual working context.

Every managed section must keep its `AICI:BEGIN` / `AICI:END` wrapper. Markers are generated values, not policy content.

## 2. Rotate markers when SKILL changes

Install a small caller based on `templates/caller-rotate-skill.yml`.

When non-marker SKILL content changes, the reusable workflow regenerates every marker and commits the rotated file back to the same branch. A marker-only bot commit is detected and does not rotate again.

The caller must grant `contents: write`. Repository branch rules must allow the GitHub Actions token to make that marker-refresh commit on branches where SKILL changes are accepted.

## 3. Require the context key on integration commits

Install a caller based on `templates/caller-integrity.yml` on the branch/event where the project considers work integrated (for example a push to `develop`).

The author or agent reads the current `SKILL.md` and appends one trailer to the commit message:

```text
AI-Context-Key: MARKER1-MARKER2-MARKER3
```

The key is simply the current markers in SKILL section order.

## 4. Pin the framework

Replace `<PINNED_SHA_OR_RELEASE_TAG>` with an explicit release tag or immutable commit SHA. Do not consume the framework from an unpinned moving branch in protected projects.

## 5. Protect the integration branch

Configure the target repository so the integrity check and the project's normal quality gate are required before protected work is accepted.

The target repository should not contain a second copy of the validator. Keeping the validator here prevents a normal feature change from weakening the rule it is being checked against.

## 6. Optional supervisor

`supervisor/REVIEWER_INSTRUCTIONS.md` defines the generic advisory reviewer role. A project can invoke an AI reviewer after its deterministic checks and provide the reviewer with the current SKILL, relevant project documents, and the diff.

This reviewer is intentionally separate from the blocking context key mechanism.
