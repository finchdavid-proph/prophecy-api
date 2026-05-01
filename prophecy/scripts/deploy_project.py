#!/usr/bin/env python3
"""Deploy a Prophecy project to a fabric."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from prophecy_client import ProphecyClient, ProphecyError  # noqa: E402


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Deploy a Prophecy project to a fabric.")
    p.add_argument("--project", required=True, help="Project name")
    p.add_argument("--fabric", required=True, help="Fabric name")
    p.add_argument("--git-tag", required=True, help="{projectName}/{version}")
    p.add_argument("--pipeline-configs", help="Path to JSON file with pipelineConfigurations")
    p.add_argument("--project-config", help="Path to JSON file with projectConfiguration")
    return p.parse_args()


def _load(path: str | None) -> dict | None:
    if not path:
        return None
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def main() -> None:
    args = parse_args()
    try:
        with ProphecyClient.from_env() as client:
            result = client.projects.deploy(
                project_name=args.project,
                fabric_name=args.fabric,
                git_tag=args.git_tag,
                pipeline_configurations=_load(args.pipeline_configs),
                project_configuration=_load(args.project_config),
            )
    except ProphecyError as e:
        sys.exit(f"error: {e}")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
