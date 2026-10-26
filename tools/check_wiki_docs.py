#!/usr/bin/env python3
"""Offline validator of local Markdown links in ForgeCoin's versioned wiki.

Reads Markdown; never downloads content, imports project binaries, accesses a
wallet, invokes a miner or modifies tracked files.
"""
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
WIKI = ROOT / "docs" / "wiki"
LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
FENCE = re.compile(r"^\s*([\x60]{3}|~{3})")


def local_link_errors(markdown: str, source: Path, root: Path) -> list[str]:
    errors = []
    fenced = False
    fence_kind = ""
    for line_no, line in enumerate(markdown.splitlines(), start=1):
        fence = FENCE.match(line)
        if fence:
            marker = fence.group(1)[:3]
            if not fenced:
                fenced, fence_kind = True, marker
            elif marker == fence_kind:
                fenced = False
            continue
        if fenced:
            continue
        for match in LINK.finditer(line):
            url = match.group(1).strip("<>")
            parts = urlsplit(url)
            if parts.scheme or parts.netloc or url.startswith(("#", "//")):
                continue
            path = unquote(parts.path)
            if not path:
                continue
            if path.startswith("/") or "\\" in path:
                errors.append(f"{source}:{line_no}: nonportable local link {url}")
                continue
            target = (source.parent / path).resolve()
            if not target.is_relative_to(root.resolve()):
                errors.append(f"{source}:{line_no}: link escapes repository: {url}")
            elif not target.is_file():
                errors.append(f"{source}:{line_no}: missing file {url}")
    return errors


def check_wiki(root: Path = ROOT) -> list[str]:
    wiki = root / "docs" / "wiki"
    errors = []
    if not (wiki / "Home.md").is_file():
        return ["Wiki Home.md is missing"]
    for file in sorted(wiki.glob("*.md")):
        errors += local_link_errors(file.read_text(encoding="utf-8"), file, root)
    return errors


def main() -> int:
    errors = check_wiki()
    if errors:
        for error in errors:
            print(f"FAIL {error}")
        return 1
    print("PASS: all local links in docs/wiki/*.md resolve within the repository")
    print("Scope: local file links only; external URLs and anchors are not verified")
    return 0


if __name__ == "__main__":
    sys.exit(main())
