import unittest

import aici


SKILL = """# Example Project Skill

Read this entire document before changing the project. The goal is to keep the
project direction stable, the implementation understandable, and the quality
checks reliable for every contributor and coding agent.

## Mission

Build the requested product in small coherent steps. Preserve the current
architecture unless a deliberate project decision changes it. Prefer simple,
readable and testable code over clever shortcuts or duplicated abstractions.

## Architecture

Domain behavior stays independent from rendering and persistence. External
content uses stable contracts. Networking adapters consume domain results and
do not decide whether a game action is legal.

## Workflow

Work on a feature branch. Read the current roadmap before starting. Add focused
tests for public behavior. Keep development deployment separate from production
promotion. Never weaken a quality rule merely to make a change pass.

## Completion

A feature is not complete merely because code exists. Relevant automated tests,
build checks and integration evidence must agree with the documented project
state before the work is considered complete.
"""


class AiciTests(unittest.TestCase):
    def test_challenge_is_deterministic(self):
        self.assertEqual(aici.challenge(SKILL), aici.challenge(SKILL))
        self.assertEqual(len(aici.challenge_positions(SKILL)), aici.CHALLENGE_SIZE)

    def test_context_key_comes_from_challenged_words(self):
        words = aici.skill_words(SKILL)
        expected = "-".join(
            words[position].casefold() for position in aici.challenge_positions(SKILL)
        )
        self.assertEqual(aici.context_key(SKILL), expected)

    def test_validate_accepts_current_key(self):
        message = f"feat: example\n\nAI-Context-Key: {aici.context_key(SKILL)}\n"
        aici.validate(SKILL, message)

    def test_validate_rejects_stale_key_and_reports_challenge(self):
        with self.assertRaises(aici.IntegrityError) as error:
            aici.validate(SKILL, "feat: example\n\nAI-Context-Key: old-key\n")
        self.assertIn(aici.challenge(SKILL), str(error.exception))

    def test_skill_edit_changes_challenge_or_response(self):
        changed = SKILL.replace("small coherent steps", "small verified coherent steps")
        self.assertNotEqual(
            (aici.challenge(SKILL), aici.context_key(SKILL)),
            (aici.challenge(changed), aici.context_key(changed)),
        )

    def test_line_ending_changes_do_not_invalidate_context(self):
        windows = SKILL.replace("\n", "\r\n")
        self.assertEqual(aici.challenge(SKILL), aici.challenge(windows))
        self.assertEqual(aici.context_key(SKILL), aici.context_key(windows))

    def test_missing_trailer_is_rejected(self):
        with self.assertRaises(aici.IntegrityError):
            aici.validate(SKILL, "feat: example")

    def test_tiny_skill_is_rejected(self):
        with self.assertRaises(aici.IntegrityError):
            aici.challenge("too short")


if __name__ == "__main__":
    unittest.main()
