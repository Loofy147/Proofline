"""Strict v0.1 task profile validation."""
from __future__ import annotations

import re
from typing import Any

_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
_IMAGE = re.compile(r"^[A-Za-z0-9._/:+-]+@sha256:[0-9a-f]{64}$")
_TASK_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,127}$")
_CPU = re.compile(r"^(?:[0-9]+)(?:\.[0-9]{1,3})?$")
_SHELLS = {"sh", "bash", "dash", "zsh", "fish", "ash", "powershell", "pwsh", "cmd", "cmd.exe"}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_task(task: Any) -> None:
    _require(isinstance(task, dict), "task must be a JSON object")
    _require(set(task) == {"schema_version", "task_id", "runtime_profile", "verification_policy"},
             "task contains missing or unknown top-level fields")
    _require(task["schema_version"] == "vap.task.v0.1", "unsupported task schema_version")
    _require(isinstance(task["task_id"], str) and _TASK_ID.fullmatch(task["task_id"]), "invalid task_id")

    runtime = task["runtime_profile"]
    _require(isinstance(runtime, dict), "runtime_profile must be an object")
    _require(set(runtime) == {"engine", "image", "network", "read_only_rootfs", "cap_drop", "tmpfs_mb", "limits", "command"},
             "runtime_profile contains missing or unknown fields")
    _require(runtime["engine"] == "podman-rootless", "only podman-rootless is supported in v0.1")
    image = runtime["image"]
    _require(isinstance(image, str) and _IMAGE.fullmatch(image),
             "image must be a fully qualified OCI image reference pinned by sha256 digest")
    registry = image.split("/", 1)[0]
    _require("." in registry or ":" in registry or registry == "localhost",
             "image reference must include an explicit registry host")
    _require(runtime["network"] == "none", "network must be 'none'")
    _require(runtime["read_only_rootfs"] is True, "read_only_rootfs must be true")
    _require(runtime["cap_drop"] == ["ALL"], "cap_drop must equal ['ALL']")
    _require(isinstance(runtime["tmpfs_mb"], int) and not isinstance(runtime["tmpfs_mb"], bool) and 1 <= runtime["tmpfs_mb"] <= 128,
             "tmpfs_mb must be an integer in [1, 128]")

    limits = runtime["limits"]
    expected_limits = {"timeout_seconds", "memory_mb", "cpus", "pids_max", "max_output_bytes", "max_input_bytes", "max_source_bytes", "max_source_files"}
    _require(isinstance(limits, dict) and set(limits) == expected_limits, "limits contains missing or unknown fields")
    ranges = {
        "timeout_seconds": (1, 600),
        "memory_mb": (64, 8192),
        "pids_max": (16, 1024),
        "max_output_bytes": (1024, 16 * 1024 * 1024),
        "max_input_bytes": (1, 1024 * 1024),
        "max_source_bytes": (1024, 512 * 1024 * 1024),
        "max_source_files": (1, 50000),
    }
    for key, (minimum, maximum) in ranges.items():
        value = limits[key]
        _require(isinstance(value, int) and not isinstance(value, bool) and minimum <= value <= maximum,
                 f"limits.{key} must be an integer in [{minimum}, {maximum}]")
    _require(isinstance(limits["cpus"], str) and _CPU.fullmatch(limits["cpus"]), "limits.cpus must be a decimal string")
    cpu_value = float(limits["cpus"])
    _require(0 < cpu_value <= 16, "limits.cpus must be >0 and <=16")

    command = runtime["command"]
    _require(isinstance(command, list) and 1 <= len(command) <= 16, "command must be an argv array of 1..16 elements")
    _require(all(isinstance(arg, str) and 0 < len(arg) <= 4096 and "\x00" not in arg for arg in command),
             "command arguments must be nonempty strings without NUL")
    executable = command[0].rsplit("/", 1)[-1].lower()
    _require(executable not in _SHELLS, "shell entrypoints are forbidden; use direct argv execution")
    wrapper_names = {"env", "busybox", "toybox"}
    if executable in wrapper_names:
        argument_basenames = {arg.rsplit("/", 1)[-1].lower() for arg in command[1:]}
        _require(not argument_basenames.intersection(_SHELLS),
                 "shell applets launched through command wrappers are forbidden")
        _require(not any(arg == "-S" or arg == "--split-string" or arg.startswith("--split-string=") for arg in command[1:]),
                 "command-wrapper split-string launch is forbidden")
    _require(not (executable in {"python", "python3", "node", "ruby", "perl"} and any(arg in {"-c", "-e", "--eval"} for arg in command[1:])),
             "inline-code command flags are forbidden; execute a staged file instead")

    policy = task["verification_policy"]
    _require(isinstance(policy, dict) and set(policy) == {"sealed_test_hash", "protocol"},
             "verification_policy contains missing or unknown fields")
    _require(isinstance(policy["sealed_test_hash"], str) and _DIGEST.fullmatch(policy["sealed_test_hash"]),
             "sealed_test_hash must be a lowercase SHA-256 digest")
    _require(policy["protocol"] == "stdin_stdout_exact_v1", "unsupported verification protocol")


def policy_digest(task: dict[str, Any]) -> str:
    from .canonical import digest_json
    return digest_json({"runtime_profile": task["runtime_profile"], "verification_policy": task["verification_policy"]})
