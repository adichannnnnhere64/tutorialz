#!/usr/bin/env python3
"""Validate a Tutorialz studio ZIP and install its catalog files into a directory."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import tempfile
import zipfile

MAX_ARCHIVE_BYTES = 20 * 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 100 * 1024 * 1024


def safe_member(name: str) -> bool:
    path = PurePosixPath(name)
    return bool(name) and not path.is_absolute() and ".." not in path.parts and "\\" not in name


def install(archive: Path, destination: Path) -> list[str]:
    if not archive.is_file():
        raise ValueError(f"Author export does not exist: {archive}")
    if archive.stat().st_size > MAX_ARCHIVE_BYTES:
        raise ValueError("Author export exceeds the 20 MiB compressed limit")
    with zipfile.ZipFile(archive) as bundle:
        infos = bundle.infolist()
        if any(not safe_member(info.filename) or info.is_dir() for info in infos):
            raise ValueError("Author export contains an unsafe or unexpected path")
        if sum(info.file_size for info in infos) > MAX_UNCOMPRESSED_BYTES:
            raise ValueError("Author export exceeds the 100 MiB uncompressed limit")
        names = {info.filename for info in infos}
        if "catalog.json" not in names:
            raise ValueError("Author export is missing catalog.json")
        catalog_bytes = bundle.read("catalog.json")
        catalog = json.loads(catalog_bytes)
        if catalog.get("schema_version") != 1 or not catalog.get("collection_id"):
            raise ValueError("Author export has an unsupported catalog")
        expected = {"catalog.json"}
        for entry in catalog.get("courses", []):
            path = entry.get("path", "")
            if not safe_member(path) or path not in names:
                raise ValueError(f"Missing or unsafe course path: {path!r}")
            data = bundle.read(path)
            if hashlib.sha256(data).hexdigest() != entry.get("sha256"):
                raise ValueError(f"Course checksum mismatch: {entry.get('id', path)}")
            course = json.loads(data)
            if course.get("id") != entry.get("id"):
                raise ValueError(f"Course ID mismatch: {entry.get('id', path)}")
            expected.add(path)
        unexpected = names - expected
        if unexpected:
            raise ValueError(f"Author export contains unlisted files: {', '.join(sorted(unexpected))}")
        with tempfile.TemporaryDirectory(prefix="tutorialz-author-") as temporary:
            stage = Path(temporary)
            for name in expected:
                target = stage / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(bundle.read(name))
            destination.mkdir(parents=True, exist_ok=True)
            # Only catalog-listed JSON is replaced. Repository documentation and
            # attribution notices in destination remain untouched.
            for name in sorted(expected - {"catalog.json"}):
                target = destination / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((stage / name).read_bytes())
            (destination / "catalog.json").write_bytes((stage / "catalog.json").read_bytes())
    return sorted(expected)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("destination", type=Path, nargs="?", default=Path("content/enterprise"))
    args = parser.parse_args()
    files = install(args.archive, args.destination)
    print(f"Installed {len(files) - 1} courses and catalog into {args.destination}")
