#!/usr/bin/env python3
"""Trigger a Prophecy pipeline run.

Reads PROPHECY_BASE_URL and PROPHECY_TOKEN from the environment.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from prophecy_client import ProphecyClient, ProphecyError  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Trigger a Prophecy pipeline run.")
    p.add_argument("--fabric-id", type=int, required=True)
    p.add_argument("--pipeline", required=True, help="Pipeline name")
    p.add_argument("--project-id", required=True)
    p.add_argument("--param", action="append", help="KEY=VALUE (repeatable)")
    p.add_argument("--branch")
    p.add_argument("--version")
    p.add_argument("--process-name")
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
            result = client.pipelines.trigger(
                fabric_id=args.fabric_id,
                pipeline_name=args.pipeline,
                project_id=args.project_id,
                parameters=parameters or None,
                branch=args.branch,
                version=args.version,
                process_name=args.process_name,
            )
    except ProphecyError as e:
        sys.exit(f"error: {e}")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
