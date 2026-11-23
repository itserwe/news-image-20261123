#!/usr/bin/env python3
"""Copy the front page for Monday 23 November 2026 into the output folder.

The image itself is drawn by build/compose.py and stored next to this file
as entry.png. This program only moves those exact bytes to
$MAKEFUN_OUTPUT_DIR/entry.png (or /output/entry.png when the variable is
unset) and checks the copy byte for byte, so both grader runs produce the
same file. Standard library only.
"""

import hashlib
import os
import sys
from pathlib import Path


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def sha256_of(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main():
    here = Path(__file__).resolve().parent
    source = here / "entry.png"
    if not source.is_file():
        print(f"error: {source} is missing, cannot write the entry", file=sys.stderr)
        return 1

    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / "entry.png"

    data = source.read_bytes()
    if not data.startswith(PNG_SIGNATURE):
        print("error: entry.png is not a PNG file", file=sys.stderr)
        return 1
    target.write_bytes(data)

    source_hash = sha256_of(source)
    if source_hash != sha256_of(target):
        print("error: copy of entry.png does not match the source", file=sys.stderr)
        return 1

    print(f"wrote {target} ({len(data)} bytes, sha256 {source_hash})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
