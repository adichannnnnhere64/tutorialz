#!/usr/bin/env python3
"""Install Tutorialz's Android activity into a generated Dioxus project."""

import argparse
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("profile", choices=("debug", "release"))
args = parser.parse_args()

source = ROOT / "scripts/android/MainActivity.kt"
target = (
    ROOT
    / "target/dx/tutorialz-learner"
    / args.profile
    / "android/app/app/src/main/kotlin/dev/dioxus/main/MainActivity.kt"
)
if not target.is_file():
    parser.error(f"generated Android project missing: {target}; run dx build --android first")
shutil.copyfile(source, target)
print(f"Installed Android system-bar insets in {target}")
