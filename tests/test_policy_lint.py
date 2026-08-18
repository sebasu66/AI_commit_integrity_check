import json
import tempfile
import unittest
from pathlib import Path

import policy_lint


POLICY = {
    "gdscript": {
        "max_file_lines": 100,
        "max_function_lines": 8,
        "require_public_function_docs": True,
    },
    "components": {"enabled": True, "root": "src/components"},
}


class PolicyLintTests(unittest.TestCase):
    def test_valid_gdscript_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "src/example_service.gd"
            path.parent.mkdir(parents=True)
            path.write_text(
                "class_name ExampleService\n\nconst MAX_ITEMS = 4\nvar item_count = 0\nsignal item_changed\n\n## Returns the current count.\nfunc get_item_count():\n\treturn item_count\n",
                encoding="utf-8",
            )
            errors = []
            policy_lint.lint_gdscript(path, "src/example_service.gd", POLICY, errors)
            self.assertEqual(errors, [])

    def test_public_function_requires_docs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "src/example.gd"
            path.parent.mkdir(parents=True)
            path.write_text("func exposed_action():\n\treturn true\n", encoding="utf-8")
            errors = []
            policy_lint.lint_gdscript(path, "src/example.gd", POLICY, errors)
            self.assertTrue(any("requires a preceding ## doc comment" in error for error in errors))

    def test_long_function_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / "src/example.gd"
            path.parent.mkdir(parents=True)
            body = "\n".join("\tvar value_%d = %d" % (i, i) for i in range(10))
            path.write_text(f"func _too_long():\n{body}\n", encoding="utf-8")
            errors = []
            policy_lint.lint_gdscript(path, "src/example.gd", POLICY, errors)
            self.assertTrue(any("maximum is 8" in error for error in errors))

    def test_component_layout_requires_matching_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            folder = root / "src/components/cards/basic_card"
            folder.mkdir(parents=True)
            (folder / "component.jsonh").write_text("{}", encoding="utf-8")
            errors = []
            policy_lint.lint_component_layout(root, POLICY, errors)
            self.assertEqual(len(errors), 2)


if __name__ == "__main__":
    unittest.main()
