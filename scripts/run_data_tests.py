#!/usr/bin/env python3
"""Run Prophecy project data tests."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from prophecy_api import ProphecyClient, ProphecyError  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run Prophecy project data tests.")
    p.add_argument("--fabric-id", type=int, required=True)
    p.add_argument("--project-id", required=True)
    p.add_argument(
        "--tests-file",
        required=True,
        help="Path to JSON array matching the tests schema",
    )
    p.add_argument("--branch")
    p.add_argument("--version")
    p.add_argument("--model-name", help="Set for model tests")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    with open(args.tests_file, encoding="utf-8") as f:
        tests = json.load(f)
    try:
        with ProphecyClient.from_env() as client:
            result = client.projects.run_data_tests(
                fabric_id=args.fabric_id,
                project_id=args.project_id,
                tests=tests,
                branch=args.branch,
                version=args.version,
                model_name=args.model_name,
            )
    except ProphecyError as e:
        sys.exit(f"error: {e}")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
