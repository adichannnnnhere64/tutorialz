#!/usr/bin/env python3
"""Check a release tag and set Dioxus's generated Android version code."""
import argparse
import pathlib
import re
import tomllib

ROOT = pathlib.Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("tag")
parser.add_argument("--patch-gradle", action="store_true")
args = parser.parse_args()

version = tomllib.loads((ROOT / "apps/learner/Cargo.toml").read_text())["package"]["version"]
if args.tag != f"v{version}":
    parser.error(f"tag {args.tag!r} must match learner version v{version}")
parts = version.split(".")
if len(parts) != 3 or any(not p.isdigit() for p in parts):
    parser.error("learner version must be numeric major.minor.patch")
major, minor, patch = map(int, parts)
if minor >= 1000 or patch >= 1000:
    parser.error("minor and patch must be below 1000")
code = major * 1_000_000 + minor * 1000 + patch
if not 1 <= code <= 2_100_000_000:
    parser.error("version code is outside the Android range")

if args.patch_gradle:
    gradle = ROOT / "target/dx/tutorialz-learner/release/android/app/app/build.gradle.kts"
    source = gradle.read_text()
    updated, count = re.subn(r"(?m)^\s*versionCode = \d+\s*$", f"        versionCode = {code}", source)
    if count != 1:
        parser.error(f"expected exactly one versionCode in {gradle}")
    gradle.write_text(updated)
print(f"{args.tag}: Android versionCode {code}")
