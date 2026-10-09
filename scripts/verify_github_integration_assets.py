#!/usr/bin/env python3
"""Verify downloaded GitHub Release assets against catalog coordinates.

Does not publish, retag, or talk to PyPI. Language-core stays offline;
this script only checks files the caller already placed under --assets-dir.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from opsdevcode_specmint.mint.github_distribution import verify_recorded_assets  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--assets-dir",
        type=Path,
        required=True,
        help="Directory with <repo-name>/{SHA256SUMS, wheel, mint-integration.json}",
    )
    args = parser.parse_args()
    matches = verify_recorded_assets(args.assets_dir)
    failed = False
    for item in matches:
        print(item.message)
        failed = failed or not item.ok
    if not matches:
        parser.exit(1, "catalog has no github origin records to verify\n")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
