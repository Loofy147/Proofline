"""Strict cross-runner comparison for VAP v0.1 evidence.

This compares full verdict cores, not timestamps or descriptive telemetry.
The VAP remains unsigned; this is reproducibility evidence, not attestation.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .canonical import digest_json, load_json_strict
from .vap import verify_vap_document

REPORT_SCHEMA = "vap.cross-runner-replay-report.v0.1"
COMPARISON_SCHEMA = "vap.cross-runner-replay-comparison.v0.1"


def _index_report(report: Any) -> tuple[str, dict[str, dict[str, Any]]]:
    if not isinstance(report, dict) or set(report) != {"schema_version", "runner_label", "results"}:
        raise ValueError("replay report must contain schema_version, runner_label, results only")
    if report.get("schema_version") != REPORT_SCHEMA:
        raise ValueError("unsupported replay report schema")
    label = report.get("runner_label")
    if not isinstance(label, str) or not label.strip():
        raise ValueError("runner_label must be a non-empty string")
    rows = report.get("results")
    if not isinstance(rows, list) or not rows:
        raise ValueError("replay results must be a non-empty list")

    indexed: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"task_id", "vap"}:
            raise ValueError("each replay result must contain task_id and vap only")
        task_id, vap = row.get("task_id"), row.get("vap")
        if not isinstance(task_id, str) or not task_id:
            raise ValueError("replay task_id must be a non-empty string")
        if task_id in indexed:
            raise ValueError(f"duplicate task_id in replay report: {task_id}")
        if not isinstance(vap, dict) or not verify_vap_document(vap):
            raise ValueError(f"invalid or unverifiable VAP for task_id: {task_id}")
        core = vap["verdict_core"]
        if core.get("task_id") != task_id:
            raise ValueError(f"report/VAP task_id mismatch: {task_id}")
        indexed[task_id] = core
    return label, indexed


def compare_replay_reports(left_report: Any, right_report: Any) -> dict[str, Any]:
    """Compare two reports and name every differing verdict-core field."""
    left_label, left = _index_report(left_report)
    right_label, right = _index_report(right_report)
    if left_label == right_label:
        raise ValueError("replay reports must identify distinct runner labels")

    mismatches: list[dict[str, Any]] = []
    matched = 0
    for task_id in sorted(set(left) | set(right)):
        if task_id not in left:
            mismatches.append({"task_id": task_id, "differences": ["missing_from_left"]})
            continue
        if task_id not in right:
            mismatches.append({"task_id": task_id, "differences": ["missing_from_right"]})
            continue

        left_core, right_core = left[task_id], right[task_id]
        different_fields = sorted(
            key for key in (set(left_core) | set(right_core))
            if left_core.get(key) != right_core.get(key)
        )
        if different_fields:
            mismatches.append({
                "task_id": task_id,
                "differences": different_fields,
                "left_core_digest": digest_json({"domain": "vap-verdict-core-v0.1", "core": left_core}),
                "right_core_digest": digest_json({"domain": "vap-verdict-core-v0.1", "core": right_core}),
            })
        else:
            matched += 1

    return {
        "schema_version": COMPARISON_SCHEMA,
        "status": "PASS" if not mismatches else "MISMATCH",
        "runner_labels": [left_label, right_label],
        "left_case_count": len(left),
        "right_case_count": len(right),
        "matched_case_count": matched,
        "mismatches": mismatches,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="vap-replay-compare")
    parser.add_argument("--left", required=True, help="JSON report from the first runner")
    parser.add_argument("--right", required=True, help="JSON report from the second runner")
    args = parser.parse_args(argv)
    try:
        left_report = load_json_strict(Path(args.left).read_bytes())
        right_report = load_json_strict(Path(args.right).read_bytes())
        result = compare_replay_reports(left_report, right_report)
    except (OSError, ValueError, TypeError) as exc:
        print(json.dumps({"status": "INVALID_EVIDENCE", "error": str(exc)}, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
