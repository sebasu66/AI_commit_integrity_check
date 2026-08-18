#!/usr/bin/env python3
"""AI Commit Integrity Check.

Dependency-free CLI that derives a small deterministic challenge from the
current SKILL.md content and validates an AI-Context-Key commit trailer.

There are no visible markers to maintain. Any meaningful SKILL.md edit changes
the document hash, which changes the challenge and therefore invalidates stale
context keys.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import re
import sys
import unicodedata
from pathlib import Path

KEY_RE = re.compile(r"^AI-Context-Key:\s*(\S+)\s*$", re.MULTILINE)
WORD_RE = re.compile(r"[^\W_]+", re.UNICODE)
CHALLENGE_SIZE = 6
MIN_WORDS = 24
PROTOCOL = b"AICI-content-challenge-v1\0"


class IntegrityError(ValueError):
    pass


def normalize_text(text: str) -> str:
    """Normalize line endings and Unicode without changing document meaning."""
    return unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n"))


def skill_words(text: str) -> list[str]:
    words = WORD_RE.findall(normalize_text(text))
    if len(words) < MIN_WORDS:
        raise IntegrityError(f"SKILL.md must contain at least {MIN_WORDS} words")
    return words


def skill_digest(text: str) -> bytes:
    return hashlib.sha256(normalize_text(text).encode("utf-8")).digest()


def challenge_positions(text: str, count: int = CHALLENGE_SIZE) -> list[int]:
    """Return deterministic, unique zero-based word positions for this SKILL."""
    words = skill_words(text)
    if count < 1 or count > len(words):
        raise IntegrityError("invalid challenge size")

    digest = skill_digest(text)
    positions: list[int] = []
    counter = 0

    while len(positions) < count:
        block = hashlib.sha256(PROTOCOL + digest + counter.to_bytes(4, "big")).digest()
        counter += 1
        for offset in range(0, len(block), 4):
            candidate = int.from_bytes(block[offset : offset + 4], "big") % len(words)
            if candidate not in positions:
                positions.append(candidate)
                if len(positions) == count:
                    break

    return positions


def challenge(text: str) -> str:
    """Human-readable challenge. W17 means the 17th normalized word."""
    return " ".join(f"W{position + 1}" for position in challenge_positions(text))


def context_key(text: str) -> str:
    """Expected response formed from the words referenced by the challenge."""
    words = skill_words(text)
    selected = [words[position].casefold() for position in challenge_positions(text)]
    return "-".join(selected)


def extract_supplied_key(commit_message: str) -> str:
    matches = KEY_RE.findall(commit_message)
    if len(matches) != 1:
        raise IntegrityError("commit message must contain exactly one AI-Context-Key trailer")
    return matches[0].casefold()


def validate(skill_text: str, commit_message: str) -> None:
    expected = context_key(skill_text)
    supplied = extract_supplied_key(commit_message)
    if not hmac.compare_digest(expected, supplied):
        raise IntegrityError(
            "AI-Context-Key is stale or incorrect. Read the current SKILL.md and "
            f"answer this challenge: {challenge(skill_text)}"
        )


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def cmd_challenge(args: argparse.Namespace) -> int:
    print(challenge(read(args.skill)))
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    validate(read(args.skill), read(args.message_file))
    print("AI context integrity check passed")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI Commit Integrity Check")
    sub = parser.add_subparsers(dest="command", required=True)

    challenge_cmd = sub.add_parser(
        "challenge",
        help="print the word-position challenge for the current SKILL.md",
    )
    challenge_cmd.add_argument("--skill", default="SKILL.md")
    challenge_cmd.set_defaults(func=cmd_challenge)

    validate_cmd = sub.add_parser(
        "validate",
        help="validate the AI-Context-Key trailer against current SKILL.md",
    )
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
