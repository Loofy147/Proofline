from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .canonical import load_json_strict
from .contract import validate_task
from .engine import run_task
from .runner import PodmanRootlessRunner
from .vap import verify_vap_document


def _write_json(path: str | None, value: object) -> None:
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if path:
        Path(path).write_text(data, encoding="utf-8")
    else:
        sys.stdout.write(data)


def main() -> int:
    parser = argparse.ArgumentParser(prog="vap-lab", description="Reproducibility Lab v0.1")
    sub = parser.add_subparsers(dest="command", required=True)

    preflight_cmd = sub.add_parser("preflight", help="validate a task and check the rootless Podman runtime")
    preflight_cmd.add_argument("--task", required=True)

    run_cmd = sub.add_parser("run", help="run a submission in a digest-pinned rootless Podman sandbox")
    run_cmd.add_argument("--task", required=True)
    run_cmd.add_argument("--submission", required=True)
    run_cmd.add_argument("--tests", required=True)
    run_cmd.add_argument("--out", required=True)

    check_cmd = sub.add_parser("verify-vap", help="recompute a VAP verdict digest")
    check_cmd.add_argument("--vap", required=True)

    args = parser.parse_args()
    try:
        if args.command == "preflight":
            task = load_json_strict(Path(args.task).read_bytes())
            validate_task(task)
            result = PodmanRootlessRunner(task).preflight()
            _write_json(None, {
                "available": result.available,
                "message": result.message,
                "podman_path": result.podman_path,
                "rootless": result.rootless,
                "runtime_identity": result.runtime_identity,
            })
            return 0 if result.available else 2
        if args.command == "run":
            vap = run_task(args.task, args.submission, args.tests)
            _write_json(args.out, vap)
            print(f"VAP written to {args.out}; verdict={vap['verdict_core']['verdict']}; digest={vap['verdict_digest']}")
            return 0 if vap["verdict_core"]["verdict"] == "PASS" else 2
        if args.command == "verify-vap":
            vap = load_json_strict(Path(args.vap).read_bytes())
            valid = verify_vap_document(vap)
            _write_json(None, {"valid": valid, "settlement_authorized": False, "reason": "VAP v0.1 prototype is unsigned and cannot authorize payment"})
            return 0 if valid else 2
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
