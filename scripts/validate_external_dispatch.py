#!/usr/bin/env python3
"""Validate the payload of a CambonOS external-package repository_dispatch."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from cambonos_lib.common import CambonosError
from cambonos_lib.external_dispatch import validate_external_dispatch


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--package", required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--commit", required=True)
    args = parser.parse_args(argv)
    try:
        channel = validate_external_dispatch(
            args.repository, args.package, args.branch, args.commit
        )
    except CambonosError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"channel": channel, "package": args.package}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
