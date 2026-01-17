#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable


def iter_conflict_files(root: Path) -> Iterable[Path]:
    markers = ("<<<<<<<", "=======", ">>>>>>>")
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        if any(line.startswith(markers) for line in text.splitlines()):
            yield path


def keep_theirs(text: str) -> str:
    out: list[str] = []
    state = "normal"  # normal | ours | theirs
    for line in text.splitlines(keepends=True):
        if line.startswith("<<<<<<<"):
            state = "ours"
            continue
        if line.startswith("======="):
            # handle files missing the <<<<<<< marker
            state = "theirs"
            continue
        if line.startswith(">>>>>>>"):
            state = "normal"
            continue
        if state in {"normal", "theirs"}:
            out.append(line)
    return "".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Resolve merge conflicts by keeping the 'theirs' side."
    )
    parser.add_argument(
        "root",
        nargs="?",
        default="/Users/narayanpowderly/projects/packages/packages",
        help="Root directory to scan for conflict markers.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List files that would be modified without writing changes.",
    )
    args = parser.parse_args()

    root = Path(args.root)
    if not root.exists():
        raise SystemExit(f"Root does not exist: {root}")

    files = list(iter_conflict_files(root))
    if args.dry_run:
        for f in files:
            print(f)
        print(f"{len(files)} files with conflict markers.")
        return 0

    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except Exception:
            continue
        resolved = keep_theirs(text)
        if resolved != text:
            path.write_text(resolved, encoding="utf-8")
            print(f"resolved {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
