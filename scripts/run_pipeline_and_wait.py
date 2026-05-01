#!/usr/bin/env python3
"""Trigger a Prophecy pipeline and poll until it reaches a terminal state.

Exits non-zero if the run ends in ERROR or the timeout elapses.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from prophecy_api import ProphecyClient, ProphecyError  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Trigger a Prophecy pipeline and wait for it to finish.",
    )
    p.add_argument("--fabric-id", type=int, required=True)
    p.add_argument("--pipeline", required=True)
    p.add_argument("--project-id", required=True)
    p.add_argument("--param", action="append", help="KEY=VALUE (repeatable)")
    p.add_argument("--branch")
    p.add_argument("--version")
    p.add_argument("--process-name")
    p.add_argument("--poll-interval", type=float, default=10.0)
    p.add_argument("--timeout-seconds", type=float, default=1800.0)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    parameters: dict[str, str] = {}
    for kv in args.param or []:
        if "=" not in kv:
            sys.exit(f"--param expects KEY=VALUE, got: {kv!r}")
        k, _, v = kv.partition("=")
        parameters[k] = v

    try:
        with ProphecyClient.from_env() as client:
            result = client.pipelines.run_and_wait(
                fabric_id=args.fabric_id,
                pipeline_name=args.pipeline,
                project_id=args.project_id,
                parameters=parameters or None,
                branch=args.branch,
                version=args.version,
                process_name=args.process_name,
                poll_interval=args.poll_interval,
                timeout=args.timeout_seconds,
            )
    except ProphecyError as e:
        sys.exit(f"error: {e}")
    print(json.dumps(result, indent=2))
    if result.get("runStatus") == "ERROR":
        sys.exit(1)


if __name__ == "__main__":
    main()
