#!/usr/bin/env python3
"""AI Commit Integrity Check.

Dependency-free CLI for parsing/rotating SKILL markers and validating the
AI-Context-Key trailer in a commit message.
"""

from __future__ import annotations

import argparse
import hmac
import re
import secrets
import string
import sys
from pathlib import Path

BEGIN_RE = re.compile(r"<!--\s*AICI:BEGIN\s+id=([A-Za-z0-9_.-]+)\s+marker=([A-Z0-9]+)\s*-->")
END_RE = re.compile(r"<!--\s*AICI:END\s+id=([A-Za-z0-9_.-]+)\s*-->")
KEY_RE = re.compile(r"^AI-Context-Key:\s*(\S+)\s*$", re.MULTILINE)
ALPHABET = string.ascii_uppercase + string.digits


class IntegrityError(ValueError):
    pass


def parse_sections(text: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    open_id: str | None = None
    seen: set[str] = set()

    for line in text.splitlines():
        begin = BEGIN_RE.fullmatch(line.strip())
        if begin:
            if open_id is not None:
                raise IntegrityError(f"nested AICI section inside {open_id}")
            section_id, marker = begin.groups()
            if section_id in seen:
                raise IntegrityError(f"duplicate AICI section id: {section_id}")
            seen.add(section_id)
            open_id = section_id
            sections.append((section_id, marker))
            continue

        end = END_RE.fullmatch(line.strip())
        if end:
            section_id = end.group(1)
            if open_id is None:
                raise IntegrityError(f"unexpected AICI end marker: {section_id}")
            if section_id != open_id:
                raise IntegrityError(f"AICI end marker {section_id} does not match {open_id}")
            open_id = None

    if open_id is not None:
        raise IntegrityError(f"unclosed AICI section: {open_id}")
    if not sections:
        raise IntegrityError("no AICI sections found")
    return sections


def context_key(text: str) -> str:
    return "-".join(marker for _, marker in parse_sections(text))


def new_marker(length: int) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(length))


def rotate_markers(text: str, marker_length: int = 4) -> str:
    if marker_length < 3:
        raise IntegrityError("marker length must be at least 3")
    parse_sections(text)

    used: set[str] = set()

    def replace(match: re.Match[str]) -> str:
        section_id = match.group(1)
        marker = new_marker(marker_length)
        while marker in used:
            marker = new_marker(marker_length)
        used.add(marker)
        return f"<!-- AICI:BEGIN id={section_id} marker={marker} -->"

    return BEGIN_RE.sub(replace, text)


def extract_supplied_key(commit_message: str) -> str:
    matches = KEY_RE.findall(commit_message)
    if len(matches) != 1:
        raise IntegrityError("commit message must contain exactly one AI-Context-Key trailer")
    return matches[0]


def validate(skill_text: str, commit_message: str) -> None:
    expected = context_key(skill_text)
    supplied = extract_supplied_key(commit_message)
    if not hmac.compare_digest(expected, supplied):
        raise IntegrityError("AI-Context-Key is stale or incorrect; read the current SKILL.md")


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def cmd_key(args: argparse.Namespace) -> int:
    print(context_key(read(args.skill)))
    return 0


def cmd_rotate(args: argparse.Namespace) -> int:
    path = Path(args.skill)
    rotated = rotate_markers(path.read_text(encoding="utf-8"), args.length)
    path.write_text(rotated, encoding="utf-8")
    print(context_key(rotated))
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    validate(read(args.skill), read(args.message_file))
    print("AI context integrity check passed")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI Commit Integrity Check")
    sub = parser.add_subparsers(dest="command", required=True)

    key = sub.add_parser("key", help="print the current context key")
    key.add_argument("--skill", default="SKILL.md")
    key.set_defaults(func=cmd_key)

    rotate = sub.add_parser("rotate", help="regenerate every context marker in SKILL.md")
    rotate.add_argument("--skill", default="SKILL.md")
    rotate.add_argument("--length", type=int, default=4)
    rotate.set_defaults(func=cmd_rotate)

    validate_cmd = sub.add_parser("validate", help="validate commit message context key")
    validate_cmd.add_argument("--skill", default="SKILL.md")
    validate_cmd.add_argument("--message-file", required=True)
    validate_cmd.set_defaults(func=cmd_validate)

    return parser


def main() -> int:
    try:
        args = build_parser().parse_args()
        return args.func(args)
    except (IntegrityError, OSError) as exc:
        print(f"AICI failure: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
