"""Adversarial integration checks against a real rootless Podman runtime.

This is intentionally excluded from ordinary unit discovery: it requires a Linux
host with rootless Podman, cgroup v2 and an already-pulled OCI image pinned by
digest. No submission code is executed on the host.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from vap_lab.canonical import digest_json
from vap_lab.contract import validate_task
from vap_lab.engine import run_task
from vap_lab.vap import verify_vap_document


PROXY_KEYS = (
    "HTTP_PROXY", "http_proxy",
    "HTTPS_PROXY", "https_proxy",
    "ALL_PROXY", "all_proxy",
    "NO_PROXY", "no_proxy",
)
LIMITS = {
    "timeout_seconds": 5,
    "memory_mb": 256,
    "cpus": "1.0",
    "pids_max": 32,
    "max_output_bytes": 4096,
    "max_input_bytes": 65536,
    "max_source_bytes": 1048576,
    "max_source_files": 64,
}


def run_scenario(
    *,
    image: str,
    task_id: str,
    source: str,
    stdin: str,
    expected_stdout: str,
    expected_verdict: str,
    limit_overrides: dict[str, Any] | None = None,
    proxy_sentinel: bool = False,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix=f"vap-{task_id}-") as temp:
        root = Path(temp)
        submission = root / "submission"
        submission.mkdir()
        (submission / "solution.py").write_text(source, encoding="utf-8")

        suite = {
            "schema_version": "vap.tests.v0.1",
            "cases": [{"stdin": stdin, "expected_stdout": expected_stdout}],
        }
        task = {
            "schema_version": "vap.task.v0.1",
            "task_id": task_id,
            "runtime_profile": {
                "engine": "podman-rootless",
                "image": image,
                "network": "none",
                "read_only_rootfs": True,
                "cap_drop": ["ALL"],
                "tmpfs_mb": 16,
                "limits": {**LIMITS, **(limit_overrides or {})},
                "command": ["python3", "/workspace/solution.py"],
            },
            "verification_policy": {
                "sealed_test_hash": digest_json(suite),
                "protocol": "stdin_stdout_exact_v1",
            },
        }
        validate_task(task)
        task_path = root / "task.json"
        tests_path = root / "tests.json"
        task_path.write_text(json.dumps(task, sort_keys=True), encoding="utf-8")
        tests_path.write_text(json.dumps(suite, sort_keys=True), encoding="utf-8")
        original_hash = digest_json({"content": (submission / "solution.py").read_text(encoding="utf-8")})

        previous = {key: os.environ.get(key) for key in PROXY_KEYS}
        try:
            if proxy_sentinel:
                for key in PROXY_KEYS:
                    os.environ[key] = "http://vap-proxy-sentinel.invalid:8123"
            vap = run_task(task_path, submission, tests_path)
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

        if not verify_vap_document(vap):
            raise AssertionError(f"{task_id}: emitted VAP failed its own integrity validator")
        core = vap["verdict_core"]
        actual = core["verdict"]
        if actual != expected_verdict:
            preflight = vap.get("telemetry", {}).get("runtime_preflight", {})
            raise AssertionError(
                f"{task_id}: expected {expected_verdict}, got {actual}; "
                f"reason={core.get('reason')}; preflight={preflight}; "
                f"cases={core.get('case_results')}"
            )
        current_hash = digest_json({"content": (submission / "solution.py").read_text(encoding="utf-8")})
        if current_hash != original_hash:
            raise AssertionError(f"{task_id}: original submission changed during execution")
        case = core["case_results"][0] if core["case_results"] else {}
        telemetry = vap.get("telemetry", {}).get("case_runs", [])
        return {
            "task_id": task_id,
            "expected_verdict": expected_verdict,
            "actual_verdict": actual,
            "reason": case.get("reason", core.get("reason")),
            "container_started": telemetry[0].get("container_started") if telemetry else False,
            "runtime_image": core["runtime_image"],
            "vap_valid": True,
            "original_unchanged": True,
            "vap": vap,
        }


def main() -> int:
    image = os.environ.get("VAP_TEST_IMAGE", "").strip()
    if "@sha256:" not in image:
        raise SystemExit("VAP_TEST_IMAGE must be an immutable OCI image digest")
    results = []

    # Correct and incorrect outputs establish the evaluator's end-to-end semantics.
    results.append(run_scenario(
        image=image,
        task_id="podman-correct-001",
        source="import sys\nprint(sum(int(x) for x in sys.stdin.read().split()))\n",
        stdin="1 2 3\n",
        expected_stdout="6\n",
        expected_verdict="PASS",
    ))
    results.append(run_scenario(
        image=image,
        task_id="podman-wrong-001",
        source="print('wrong')\n",
        stdin="",
        expected_stdout="right\n",
        expected_verdict="FAIL_TESTS",
    ))

    # A read-only source mount must prevent writes inside the execution container.
    results.append(run_scenario(
        image=image,
        task_id="podman-readonly-001",
        source=(
            "try:\n"
            "    with open('/workspace/solution.py', 'w', encoding='utf-8') as f:\n"
            "        f.write('print(\\\"MUTATED\\\")\\n')\n"
            "    print('WRITABLE')\n"
            "except OSError:\n"
            "    print('READ_ONLY')\n"
        ),
        stdin="",
        expected_stdout="READ_ONLY\n",
        expected_verdict="PASS",
    ))

    # Isolated network namespace must not provide outbound connectivity.
    results.append(run_scenario(
        image=image,
        task_id="podman-network-001",
        source=(
            "import socket\n"
            "s = socket.socket()\n"
            "s.settimeout(1.0)\n"
            "try:\n"
            "    s.connect(('1.1.1.1', 80))\n"
            "    print('CONNECTED')\n"
            "except OSError:\n"
            "    print('BLOCKED')\n"
            "finally:\n"
            "    s.close()\n"
        ),
        stdin="",
        expected_stdout="BLOCKED\n",
        expected_verdict="PASS",
        limit_overrides={"timeout_seconds": 4},
    ))

    # Host proxy sentinels must not be inherited by the untrusted program.
    results.append(run_scenario(
        image=image,
        task_id="podman-proxy-001",
        source=(
            "import os\n"
            "keys = ('HTTP_PROXY', 'http_proxy', 'HTTPS_PROXY', 'https_proxy', "
            "'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy')\n"
            "print('|'.join(os.environ.get(k, '') for k in keys))\n"
        ),
        stdin="",
        expected_stdout="|||||||\n",
        expected_verdict="PASS",
        proxy_sentinel=True,
    ))

    # Resource-limit states must not be mislabeled as test failures or PASS.
    results.append(run_scenario(
        image=image,
        task_id="podman-timeout-001",
        source="while True:\n    pass\n",
        stdin="",
        expected_stdout="done\n",
        expected_verdict="RESOURCE_EXHAUSTED",
        limit_overrides={"timeout_seconds": 2},
    ))
    results.append(run_scenario(
        image=image,
        task_id="podman-output-flood-001",
        source="import sys\nsys.stdout.write('X' * (8 * 1024 * 1024))\n",
        stdin="",
        expected_stdout="done\n",
        expected_verdict="RESOURCE_EXHAUSTED",
        limit_overrides={"max_output_bytes": 4096},
    ))

    report = {
        "schema_version": "vap.cross-runner-replay-report.v0.1",
        "runner_label": os.environ.get("VAP_REPLAY_LABEL", "local"),
        "results": [{"task_id": item["task_id"], "vap": item["vap"]} for item in results],
    }
    report_path = os.environ.get("VAP_REPLAY_REPORT")
    if report_path:
        Path(report_path).write_text(
            json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\\n",
            encoding="utf-8",
        )
    # Keep the console summary compact; full, verifier-checked VAPs go to the artifact.
    console_results = [{key: value for key, value in item.items() if key != "vap"} for item in results]
    print(json.dumps({"status": "PASS", "scenario_count": len(results), "runner_label": report["runner_label"], "results": console_results}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
