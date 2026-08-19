#!/usr/bin/env python3
"""Deterministic project-policy linter for AI-assisted repositories.

The target repository supplies code. Policy lives in this framework repository so
ordinary target-repository changes cannot weaken the gate they are being checked
against.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

from render_policy_skill import render, replace_block

SNAKE_RE = re.compile(r"^[a-z][a-z0-9_]*$")
PASCAL_RE = re.compile(r"^[A-Z][A-Za-z0-9]*$")
CONST_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
FUNC_RE = re.compile(r"^(\s*)func\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")
CLASS_RE = re.compile(r"^\s*class_name\s+([A-Za-z_][A-Za-z0-9_]*)")
CONST_DECL_RE = re.compile(r"^\s*const\s+([A-Za-z_][A-Za-z0-9_]*)")
SIGNAL_RE = re.compile(r"^\s*signal\s+([A-Za-z_][A-Za-z0-9_]*)")
VAR_RE = re.compile(r"^\s*(?:@\w+(?:\([^)]*\))?\s+)*var\s+([A-Za-z_][A-Za-z0-9_]*)")
DECISION_RE = re.compile(r"^\s*(if|elif|for|while|match)\b")


class PolicyError(ValueError):
    pass


def git_changed_files(root: Path, base: str) -> list[str]:
    if not base:
        return []
    proc = subprocess.run(
        ["git", "-C", str(root), "diff", "--name-only", "--diff-filter=ACMR", f"{base}...HEAD"],
        check=True,
        text=True,
        capture_output=True,
    )
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def all_candidate_files(root: Path) -> list[str]:
    paths: list[str] = []
    for folder in ("src", "tests"):
        base = root / folder
        if base.exists():
            paths.extend(path.relative_to(root).as_posix() for path in base.rglob("*.gd"))
    return sorted(paths)


def function_ranges(lines: list[str]) -> list[tuple[str, int, int]]:
    starts: list[tuple[str, int, int]] = []
    for index, line in enumerate(lines):
        match = FUNC_RE.match(line)
        if match:
            starts.append((match.group(2), index, len(match.group(1).replace("\t", "    "))))

    ranges: list[tuple[str, int, int]] = []
    for name, start, indent in starts:
        end = len(lines)
        for probe in range(start + 1, len(lines)):
            stripped = lines[probe].strip()
            if not stripped or stripped.startswith("#"):
                continue
            raw_indent = len(lines[probe]) - len(lines[probe].lstrip(" \t"))
            if raw_indent <= indent and FUNC_RE.match(lines[probe]):
                end = probe
                break
        ranges.append((name, start, end))
    return ranges


def has_doc_comment(lines: list[str], func_line: int) -> bool:
    index = func_line - 1
    while index >= 0 and not lines[index].strip():
        index -= 1
    return index >= 0 and lines[index].lstrip().startswith("##")


def decision_complexity(lines: list[str], start: int, end: int) -> int:
    """Small deterministic branch-complexity metric for GDScript.

    Starts at 1, then adds one for each if/elif/for/while/match and each boolean
    short-circuit operator (&&, ||) in the function body. This is intentionally
    transparent and language-local rather than pretending Python Radon parses GDScript.
    """
    score = 1
    for line in lines[start + 1 : end]:
        stripped = line.split("#", 1)[0]
        if DECISION_RE.match(stripped):
            score += 1
        score += stripped.count("&&") + stripped.count("||")
    return score


def lint_gdscript(path: Path, rel: str, policy: dict, errors: list[str]) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    gd = policy["gdscript"]
    max_file_lines = int(gd["max_file_lines"])
    max_function_lines = int(gd["max_function_lines"])
    max_complexity = int(gd.get("max_decision_complexity", 10))
    require_public_docs = bool(gd.get("require_public_function_docs", True))

    if len(lines) > max_file_lines:
        errors.append(f"{rel}: {len(lines)} lines exceeds max_file_lines={max_file_lines}")

    stem = path.name.removesuffix(".gd")
    if not SNAKE_RE.fullmatch(stem):
        errors.append(f"{rel}: GDScript filenames must use snake_case")

    for number, line in enumerate(lines, start=1):
        class_match = CLASS_RE.match(line)
        if class_match and not PASCAL_RE.fullmatch(class_match.group(1)):
            errors.append(f"{rel}:{number}: class_name must use PascalCase")

        const_match = CONST_DECL_RE.match(line)
        if const_match and not CONST_RE.fullmatch(const_match.group(1)):
            errors.append(f"{rel}:{number}: constants must use UPPER_SNAKE_CASE")

        signal_match = SIGNAL_RE.match(line)
        if signal_match and not SNAKE_RE.fullmatch(signal_match.group(1)):
            errors.append(f"{rel}:{number}: signals must use snake_case")

        var_match = VAR_RE.match(line)
        if var_match and not SNAKE_RE.fullmatch(var_match.group(1)):
            errors.append(f"{rel}:{number}: variables must use snake_case")

    for name, start, end in function_ranges(lines):
        if not (SNAKE_RE.fullmatch(name.lstrip("_")) or name.startswith("_")):
            errors.append(f"{rel}:{start + 1}: function '{name}' must use snake_case")
        length = end - start
        if length > max_function_lines:
            errors.append(
                f"{rel}:{start + 1}: function '{name}' is {length} lines; maximum is {max_function_lines}"
            )
        complexity = decision_complexity(lines, start, end)
        if complexity > max_complexity:
            errors.append(
                f"{rel}:{start + 1}: function '{name}' decision complexity is {complexity}; maximum is {max_complexity}"
            )
        if require_public_docs and not name.startswith("_") and not has_doc_comment(lines, start):
            errors.append(f"{rel}:{start + 1}: public function '{name}' requires a preceding ## doc comment")


def lint_component_layout(root: Path, policy: dict, errors: list[str]) -> None:
    if not policy.get("components", {}).get("enabled", False):
        return
    base = root / policy["components"].get("root", "src/components")
    if not base.exists():
        return

    for manifest in base.rglob("component.jsonh"):
        folder = manifest.parent
        name = folder.name
        rel = folder.relative_to(root).as_posix()
        if not SNAKE_RE.fullmatch(name):
            errors.append(f"{rel}: component folder must use snake_case")

        scripts = sorted(folder.glob("*.gd"))
        scenes = sorted(folder.glob("*.tscn"))
        if not scripts:
            errors.append(f"{rel}: component folder requires at least one local .gd implementation")
        if not scenes:
            errors.append(f"{rel}: component folder requires at least one local .tscn scene")


def lint_skill_projection(root: Path, policy: dict, errors: list[str]) -> None:
    skill_rel = policy.get("skill_path")
    if not skill_rel:
        return
    skill_path = root / skill_rel
    if not skill_path.exists():
        errors.append(f"{skill_rel}: required policy projection file is missing")
        return
    current = skill_path.read_text(encoding="utf-8")
    try:
        expected = replace_block(current, render(policy))
    except ValueError as exc:
        errors.append(f"{skill_rel}: {exc}")
        return
    if current != expected:
        errors.append(f"{skill_rel}: generated AICI policy block is stale")


def load_policy(path: Path) -> dict:
    try:
        policy = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PolicyError(f"cannot load policy {path}: {exc}") from exc
    if "gdscript" not in policy:
        raise PolicyError("policy must define gdscript rules")
    return policy


def main() -> int:
    parser = argparse.ArgumentParser(description="AI Commit Integrity project policy linter")
    parser.add_argument("--root", required=True, help="target repository checkout")
    parser.add_argument("--policy", required=True, help="policy JSON from protected framework repository")
    parser.add_argument("--base", default="", help="git base SHA; checks changed GDScript files when supplied")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    policy = load_policy(Path(args.policy))
    errors: list[str] = []

    changed = git_changed_files(root, args.base) if args.base else []
    gd_files = [path for path in changed if path.endswith(".gd")] if args.base else all_candidate_files(root)

    for rel in gd_files:
        path = root / rel
        if path.exists() and (rel.startswith("src/") or rel.startswith("tests/")):
            lint_gdscript(path, rel, policy, errors)

    lint_component_layout(root, policy, errors)
    lint_skill_projection(root, policy, errors)

    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)

    if errors:
        print(f"PROJECT POLICY LINT FAILED: {len(errors)} violation(s)", file=sys.stderr)
        return 1

    scope = f"{len(gd_files)} changed GDScript file(s)" if args.base else f"{len(gd_files)} GDScript file(s)"
    print(f"PROJECT POLICY LINT PASSED: {scope}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
