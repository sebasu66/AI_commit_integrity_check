#!/usr/bin/env python3
"""Render machine-enforced project policy into a managed SKILL.md block.

The protected policy remains the source of truth. Target repositories keep a readable
projection inside SKILL.md so cooperative contributors see the exact rules the linter
will enforce.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

START = "<!-- AICI:POLICY:START -->"
END = "<!-- AICI:POLICY:END -->"


def render(policy: dict) -> str:
    gd = policy["gdscript"]
    components = policy.get("components", {})
    lines = [
        START,
        "### Machine-enforced policy",
        "",
        "This block is generated from the protected AICI policy. Do not edit it by hand.",
        "",
        f"- maximum GDScript file length: **{gd['max_file_lines']} lines**;",
        f"- maximum function length: **{gd['max_function_lines']} lines**;",
        f"- maximum decision complexity per function: **{gd['max_decision_complexity']}**;",
        f"- public function `##` documentation required: **{'yes' if gd.get('require_public_function_docs', True) else 'no'}**;",
        f"- GDScript files/functions/variables/signals: `{gd['file_names']}` / `{gd['function_names']}` / `{gd['variable_names']}` / `{gd['signal_names']}`;",
        f"- classes: `{gd['class_names']}`; constants: `{gd['constant_names']}`.",
    ]
    if components.get("enabled", False):
        lines.extend(
            [
                f"- component root: `{components.get('root', 'src/components')}`;",
                f"- component manifest: `{components.get('manifest_name', 'component.jsonh')}`;",
                "- each component manifest folder must be snake_case and own at least one local `.gd` and `.tscn` file.",
            ]
        )
    lines.extend([END, ""])
    return "\n".join(lines)


def replace_block(skill_text: str, generated: str) -> str:
    start = skill_text.find(START)
    end = skill_text.find(END)
    if start < 0 or end < 0 or end < start:
        raise ValueError(f"SKILL.md must contain managed markers {START} and {END}")
    end += len(END)
    return skill_text[:start] + generated.rstrip() + skill_text[end:]


def main() -> int:
    parser = argparse.ArgumentParser(description="Render protected AICI policy into SKILL.md")
    parser.add_argument("--policy", required=True)
    parser.add_argument("--skill", required=True)
    parser.add_argument("--check", action="store_true", help="fail if SKILL projection is stale")
    args = parser.parse_args()

    policy = json.loads(Path(args.policy).read_text(encoding="utf-8"))
    skill_path = Path(args.skill)
    current = skill_path.read_text(encoding="utf-8")
    expected = replace_block(current, render(policy))

    if args.check:
        if current != expected:
            print("SKILL POLICY PROJECTION STALE: regenerate from protected policy", file=sys.stderr)
            return 1
        print("SKILL POLICY PROJECTION CURRENT")
        return 0

    if current != expected:
        skill_path.write_text(expected, encoding="utf-8")
        print(f"UPDATED {skill_path}")
    else:
        print(f"UNCHANGED {skill_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
