#!/usr/bin/env python3
"""Build the Windows bootstrap payload without external dependencies."""
from __future__ import annotations

import argparse
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

INCLUDED = ("bootstrap", "apps")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(args.output, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for top in INCLUDED:
            for path in sorted((root / top).rglob("*")):
                if path.is_file() and not any(part in {"node_modules", "target"} for part in path.parts):
                    archive.write(path, path.relative_to(root).as_posix())
    print(f"Created {args.output} ({args.output.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
