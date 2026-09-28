"""Module entry for the public Mint CLI."""

from __future__ import annotations

import sys

from opsdevcode_specmint.cli import main

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
