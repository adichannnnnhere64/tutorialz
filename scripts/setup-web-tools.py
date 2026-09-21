#!/usr/bin/env python3
"""Install the CLI matching the locked wasm-bindgen crate into ignored tools/."""
from pathlib import Path
import subprocess
import tomllib

root = Path(__file__).resolve().parents[1]
lock = tomllib.loads((root / "Cargo.lock").read_text())
version = next(p["version"] for p in lock["package"] if p["name"] == "wasm-bindgen")
subprocess.run([
    "cargo", "install", "wasm-bindgen-cli", "--version", f"={version}",
    "--locked", "--force", "--root", str(root / "tools"),
], cwd=root, check=True)
