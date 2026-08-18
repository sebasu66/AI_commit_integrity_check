import unittest

import aici


SKILL = """# Example\n\n<!-- AICI:BEGIN id=mission marker=A1B2 -->\n## Mission\nKeep direction clear.\n<!-- AICI:END id=mission -->\n\n<!-- AICI:BEGIN id=workflow marker=C3D4 -->\n## Workflow\nKeep the process simple.\n<!-- AICI:END id=workflow -->\n"""


class AiciTests(unittest.TestCase):
    def test_context_key_uses_section_order(self):
        self.assertEqual(aici.context_key(SKILL), "A1B2-C3D4")

    def test_validate_accepts_current_key(self):
        aici.validate(SKILL, "feat: example\n\nAI-Context-Key: A1B2-C3D4\n")

    def test_validate_rejects_stale_key(self):
        with self.assertRaises(aici.IntegrityError):
            aici.validate(SKILL, "feat: example\n\nAI-Context-Key: OLD-KEY\n")

    def test_rotate_changes_every_marker(self):
        rotated = aici.rotate_markers(SKILL)
        before = aici.parse_sections(SKILL)
        after = aici.parse_sections(rotated)
        self.assertEqual([section for section, _ in before], [section for section, _ in after])
        self.assertTrue(all(old != new for (_, old), (_, new) in zip(before, after)))

    def test_duplicate_sections_are_rejected(self):
        duplicate = SKILL + "\n<!-- AICI:BEGIN id=mission marker=ZZZZ -->\nx\n<!-- AICI:END id=mission -->\n"
        with self.assertRaises(aici.IntegrityError):
            aici.parse_sections(duplicate)

    def test_missing_trailer_is_rejected(self):
        with self.assertRaises(aici.IntegrityError):
            aici.validate(SKILL, "feat: example")


if __name__ == "__main__":
    unittest.main()
