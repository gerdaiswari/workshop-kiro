#!/usr/bin/env python3
"""Cache a pinned external dependency locally before private S3 upload."""
from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import tempfile
import urllib.request
from pathlib import Path


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_file(
    path: Path,
    minimum_bytes: int,
    expected_magic: bytes,
    expected_sha256: str,
) -> None:
    if not path.is_file():
        raise ValueError(f"file does not exist: {path}")
    size = path.stat().st_size
    if size < minimum_bytes:
        raise ValueError(f"file is too small: {size} bytes; expected at least {minimum_bytes}")
    with path.open("rb") as handle:
        actual_magic = handle.read(len(expected_magic))
    if actual_magic != expected_magic:
        raise ValueError(f"file magic {actual_magic!r} does not match {expected_magic!r}")
    actual_sha256 = file_sha256(path)
    if actual_sha256.lower() != expected_sha256.lower():
        raise ValueError(f"SHA-256 {actual_sha256} does not match {expected_sha256}")


def download(urls: list[str], output: Path, minimum_bytes: int, magic: bytes, sha256: str) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        try:
            validate_file(output, minimum_bytes, magic, sha256)
            print(f"Reusing validated dependency: {output}")
            return
        except ValueError:
            output.unlink()

    failures: list[str] = []
    for url in urls:
        temporary_name = ""
        try:
            print(f"Downloading dependency: {url}")
            request = urllib.request.Request(url, headers={"User-Agent": "kiro-ws2025-workshop/1.0"})
            with urllib.request.urlopen(request, timeout=120) as source:
                with tempfile.NamedTemporaryFile(delete=False, dir=output.parent) as temporary:
                    temporary_name = temporary.name
                    shutil.copyfileobj(source, temporary, length=1024 * 1024)
            temporary_path = Path(temporary_name)
            validate_file(temporary_path, minimum_bytes, magic, sha256)
            os.replace(temporary_path, output)
            print(f"Validated dependency: {output} ({output.stat().st_size} bytes, SHA-256 {sha256})")
            return
        except Exception as exc:
            failures.append(f"{url}: {exc}")
            if temporary_name:
                Path(temporary_name).unlink(missing_ok=True)
    raise RuntimeError("all dependency sources failed:\n- " + "\n- ".join(failures))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", action="append", required=True, dest="urls")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--minimum-bytes", required=True, type=int)
    parser.add_argument("--magic", required=True)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    download(args.urls, args.output, args.minimum_bytes, args.magic.encode("ascii"), args.sha256)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
