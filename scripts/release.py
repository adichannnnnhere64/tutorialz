#!/usr/bin/env python3
"""Build, commit, tag, and push the next Tutorialz GitHub release."""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import subprocess
import tomllib

ROOT = Path(__file__).resolve().parents[1]
VERSION_FILES = (ROOT / "apps/learner/Cargo.toml", ROOT / "apps/author/Cargo.toml")


def run(*command: str, capture: bool = False) -> str:
    result = subprocess.run(command, cwd=ROOT, check=True, text=True,
                            capture_output=capture)
    return result.stdout.strip() if capture else ""


def current_version() -> str:
    return tomllib.loads(VERSION_FILES[0].read_text())["package"]["version"]


def validate_version(value: str) -> str:
    if not re.fullmatch(r"\d+\.\d+\.\d+", value):
        raise ValueError("Version must use numeric major.minor.patch format")
    return value


def next_patch(value: str) -> str:
    major, minor, patch = map(int, value.split("."))
    return f"{major}.{minor}.{patch + 1}"


def replace_version(path: Path, value: str) -> None:
    source = path.read_text()
    updated, count = re.subn(r'(?m)^version = "[0-9]+\.[0-9]+\.[0-9]+"$',
                             f'version = "{value}"', source, count=1)
    if count != 1:
        raise ValueError(f"Could not update package version in {path.relative_to(ROOT)}")
    path.write_text(updated)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", help="Release version; defaults to the next patch version")
    args = parser.parse_args()
    if run("git", "branch", "--show-current", capture=True) != "main":
        raise SystemExit("Releases must be created from main")
    if run("git", "status", "--porcelain", capture=True):
        raise SystemExit("Commit or stash changes before running make release")
    old = current_version()
    version = validate_version(args.version) if args.version else next_patch(old)
    if tuple(map(int, version.split("."))) <= tuple(map(int, old.split("."))):
        raise SystemExit(f"Release version {version} must be newer than {old}")
    tag = f"v{version}"
    if subprocess.run(["git", "rev-parse", "--verify", "--quiet", tag], cwd=ROOT).returncode == 0:
        raise SystemExit(f"Tag already exists: {tag}")
    for path in VERSION_FILES:
        replace_version(path, version)
    # Refresh workspace package versions in Cargo.lock before locked checks.
    run("cargo", "check", "-p", "tutorialz-core")
    run("make", "release-build")
    allowed = {"Cargo.lock", "apps/learner/Cargo.toml", "apps/author/Cargo.toml"}
    changed = {
        line[3:]
        for line in run("git", "status", "--porcelain", capture=True).splitlines()
        if line
    }
    unexpected = changed - allowed
    if unexpected:
        raise SystemExit(
            "Release checks changed files that need a separate commit: "
            + ", ".join(sorted(unexpected))
        )
    run("git", "add", "apps/learner/Cargo.toml", "apps/author/Cargo.toml", "Cargo.lock")
    run("git", "commit", "-m", f"Release {tag}")
    run("git", "tag", "-a", tag, "-m", f"Tutorialz {tag}")
    run("git", "push", "origin", "main")
    run("git", "push", "origin", tag)
    print(f"Published {tag}; GitHub Actions will create the signed APK release.")


if __name__ == "__main__":
    main()
