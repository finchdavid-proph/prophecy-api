#!/usr/bin/env python3
"""Get the status of a Prophecy pipeline run."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from prophecy_api import ProphecyClient, ProphecyError  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Get a Prophecy pipeline run status.")
    p.add_argument("run_id")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    try:
        with ProphecyClient.from_env() as client:
            result = client.pipelines.get_run_status(args.run_id)
    except ProphecyError as e:
        sys.exit(f"error: {e}")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
