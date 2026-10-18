"""Fail-closed Podman rootless runner for untrusted source submissions.

This module never falls back to executing submission code on the host.
"""
from __future__ import annotations

import json
import os
import signal
import shutil
import subprocess
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .canonical import load_json_strict
from .evaluator import CaseResult, classify_case
from .source import stage_readonly_source


@dataclass(frozen=True)
class RuntimePreflight:
    available: bool
    message: str
    podman_path: str | None = None
    rootless: bool | None = None
    runtime_identity: dict[str, Any] | None = None


@dataclass(frozen=True)
class RunnerTelemetry:
    wall_clock_ms: int
    stdout_bytes: int
    stderr_bytes: int
    total_observed_output_bytes: int
    container_started: bool
    oom_killed: bool | None
    container_exit_code: int | None
    cpu_time_ns: int | None = None
    peak_memory_bytes: int | None = None
    cpu_memory_measurement: str = "NOT_COLLECTED_IN_V0.1"


@dataclass(frozen=True)
class ContainerExecution:
    case_result: CaseResult
    telemetry: RunnerTelemetry


class _BoundedOutput:
    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.lock = threading.Lock()
        self.total_seen = 0
        self.stdout = bytearray()
        self.stderr = bytearray()
        self.exceeded = threading.Event()

    def reader(self, stream: Any, target: bytearray) -> None:
        try:
            while True:
                chunk = stream.read1(8192)
                if not chunk:
                    return
                with self.lock:
                    remaining = max(0, self.limit - self.total_seen)
                    keep = min(remaining, len(chunk))
                    target.extend(chunk[:keep])
                    self.total_seen += len(chunk)
                    if self.total_seen > self.limit:
                        self.exceeded.set()
        except (OSError, ValueError):
            return


class PodmanRootlessRunner:
    def __init__(self, task: dict[str, Any], *, podman_binary: str = "podman") -> None:
        self.task = task
        self.runtime = task["runtime_profile"]
        self.limits = self.runtime["limits"]
        self.podman_binary = shutil.which(podman_binary) or (podman_binary if Path(podman_binary).is_file() else None)
        self._preflight_cache: RuntimePreflight | None = None

    def preflight(self) -> RuntimePreflight:
        if self._preflight_cache is not None:
            return self._preflight_cache
        result = self._perform_preflight()
        self._preflight_cache = result
        return result

    def _perform_preflight(self) -> RuntimePreflight:
        if os.name != "posix" or not Path("/proc").exists():
            return RuntimePreflight(False, "Linux/POSIX runtime required")
        if not self.podman_binary:
            return RuntimePreflight(False, "Podman executable not found; host execution fallback is disabled")
        try:
            info = subprocess.run(
                [self.podman_binary, "info", "--format", "json"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                check=False,
                close_fds=True,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return RuntimePreflight(False, f"Podman preflight failed: {type(exc).__name__}", self.podman_binary)
        if info.returncode != 0:
            return RuntimePreflight(False, "podman info failed; cannot establish runner state", self.podman_binary)
        try:
            payload = json.loads(info.stdout)
            host = payload.get("host", {})
            security = host.get("security", {}) if isinstance(host, dict) else {}
            rootless = security.get("rootless")
            cgroup_version = host.get("cgroupVersion") if isinstance(host, dict) else None
        except (json.JSONDecodeError, AttributeError):
            return RuntimePreflight(False, "Podman info response was not understood", self.podman_binary)
        if rootless is not True:
            return RuntimePreflight(False, "Podman rootless mode was not positively confirmed", self.podman_binary, rootless)
        if cgroup_version != "v2":
            return RuntimePreflight(False, "cgroup v2 was not positively confirmed; resource-limit enforcement cannot be assumed", self.podman_binary, True)
        try:
            version_result = subprocess.run(
                [self.podman_binary, "version", "--format", "json"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                check=False,
                close_fds=True,
            )
            if version_result.returncode != 0:
                return RuntimePreflight(False, "Podman version identity could not be captured", self.podman_binary, True)
            version_payload = json.loads(version_result.stdout)
            client = version_payload.get("Client", {})
            host_version = version_payload.get("Host", {})
            oci = host_version.get("OCIRuntime", {}) if isinstance(host_version, dict) else {}
            conmon = host_version.get("Conmon", {}) if isinstance(host_version, dict) else {}
            runtime_identity = {
                "podman_version": client.get("Version") if isinstance(client, dict) else None,
                "podman_api_version": client.get("APIVersion") if isinstance(client, dict) else None,
                "oci_runtime_name": oci.get("Name") if isinstance(oci, dict) else None,
                "oci_runtime_version": oci.get("Version") if isinstance(oci, dict) else None,
                "conmon_version": (conmon.get("Version") or conmon.get("package")) if isinstance(conmon, dict) else None,
                "cgroup_version": cgroup_version,
                "rootless": True,
            }
            if not runtime_identity["podman_version"]:
                return RuntimePreflight(False, "Podman version response lacked a version identifier", self.podman_binary, True)
        except (OSError, subprocess.SubprocessError, json.JSONDecodeError, AttributeError):
            return RuntimePreflight(False, "Podman version response could not be validated", self.podman_binary, True)
        try:
            exists = subprocess.run(
                [self.podman_binary, "image", "exists", self.runtime["image"]],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                timeout=10,
                check=False,
                close_fds=True,
            )
        except (OSError, subprocess.TimeoutExpired):
            return RuntimePreflight(False, "Podman could not verify the digest-pinned local image", self.podman_binary, True)
        if exists.returncode != 0:
            return RuntimePreflight(False, "digest-pinned image is not available locally; automatic image pulling is disabled", self.podman_binary, True, runtime_identity)
        return RuntimePreflight(True, "Podman rootless mode, cgroup v2, runtime identity, and digest-pinned local image confirmed", self.podman_binary, True, runtime_identity)

    def _inspect(self, name: str) -> dict[str, Any] | None:
        assert self.podman_binary
        try:
            result = subprocess.run(
                [self.podman_binary, "inspect", "--format", "json", name],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5,
                check=False,
                close_fds=True,
            )
            if result.returncode != 0:
                return None
            data = json.loads(result.stdout)
            if isinstance(data, list) and data and isinstance(data[0], dict):
                return data[0]
            if isinstance(data, dict):
                return data
        except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
            return None
        return None

    @staticmethod
    def _started(state: dict[str, Any] | None) -> bool:
        if not state:
            return False
        state_data = state.get("State", {})
        if not isinstance(state_data, dict):
            return False
        value = state_data.get("StartedAt")
        return isinstance(value, str) and value not in {"", "0001-01-01T00:00:00Z", "0001-01-01T00:00:00.000000000Z"}

    def _command(self, stage_dir: Path, name: str) -> list[str]:
        lim = self.limits
        return [
            self.podman_binary or "podman",
            "run",
            "--pull=never",
            "--name", name,
            "--label", f"vap.run_id={name}",
            "--network=none",
            "--no-hosts",
            "--read-only",
            "--read-only-tmpfs=false",
            "--cap-drop=ALL",
            "--security-opt=no-new-privileges",
            "--pids-limit", str(lim["pids_max"]),
            "--memory", f"{lim['memory_mb']}m",
            "--memory-swap", f"{lim['memory_mb']}m",
            "--cpus", lim["cpus"],
            "--user=65532:65532",
            "--tmpfs", f"/tmp:rw,nosuid,nodev,noexec,size={self.runtime['tmpfs_mb']}m,mode=1777",
            "--volume", f"{str(stage_dir)}:/workspace:ro,Z",
            "--workdir=/workspace",
            "--env=LANG=C.UTF-8",
            "--env=LC_ALL=C.UTF-8",
            "--env=TZ=UTC",
            "--env=HOME=/tmp",
            "--entrypoint", self.runtime["command"][0],
            self.runtime["image"],
            *self.runtime["command"][1:],
        ]

    def _remove(self, name: str) -> None:
        if not self.podman_binary:
            return
        try:
            subprocess.run(
                [self.podman_binary, "rm", "--force", name],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
                check=False,
                close_fds=True,
            )
        except (OSError, subprocess.TimeoutExpired):
            pass

    def run_case(self, stage_dir: Path, stdin: bytes, expected: bytes) -> ContainerExecution:
        preflight = self.preflight()
        start_ns = time.monotonic_ns()
        if not preflight.available:
            case = classify_case(return_code=None, stdout=b"", stderr=b"", expected=expected, termination="infrastructure")
            telemetry = RunnerTelemetry(0, 0, 0, 0, False, None, None)
            return ContainerExecution(case, telemetry)
        if len(stdin) > self.limits["max_input_bytes"]:
            case = classify_case(return_code=None, stdout=b"", stderr=b"", expected=expected, termination="resource_limit")
            return ContainerExecution(case, RunnerTelemetry(0, 0, 0, 0, False, None, None))

        name = "vap-" + uuid.uuid4().hex[:20]
        collector = _BoundedOutput(self.limits["max_output_bytes"])
        process: subprocess.Popen[bytes] | None = None
        stdout_thread: threading.Thread | None = None
        stderr_thread: threading.Thread | None = None
        termination = "normal"
        process_return_code: int | None = None
        try:
            command = self._command(stage_dir, name)
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                close_fds=True,
                start_new_session=True,
            )
            assert process.stdout is not None and process.stderr is not None and process.stdin is not None
            stdout_thread = threading.Thread(target=collector.reader, args=(process.stdout, collector.stdout), daemon=True)
            stderr_thread = threading.Thread(target=collector.reader, args=(process.stderr, collector.stderr), daemon=True)
            stdout_thread.start()
            stderr_thread.start()
            def feed_stdin() -> None:
                try:
                    process.stdin.write(stdin)
                    process.stdin.flush()
                except (BrokenPipeError, OSError):
                    pass
                finally:
                    try:
                        process.stdin.close()
                    except OSError:
                        pass

            stdin_thread = threading.Thread(target=feed_stdin, daemon=True)
            stdin_thread.start()
            deadline = time.monotonic() + self.limits["timeout_seconds"]
            while process.poll() is None:
                if collector.exceeded.is_set():
                    termination = "output_limit"
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except (ProcessLookupError, PermissionError, OSError):
                        process.kill()
                    break
                if time.monotonic() >= deadline:
                    termination = "timeout"
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except (ProcessLookupError, PermissionError, OSError):
                        process.kill()
                    break
                time.sleep(0.005)
            try:
                process_return_code = process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except (ProcessLookupError, PermissionError, OSError):
                    process.kill()
                process_return_code = process.wait(timeout=2)
                termination = "infrastructure"
            if 'stdin_thread' in locals():
                stdin_thread.join(timeout=1)
            if stdout_thread:
                stdout_thread.join(timeout=2)
            if stderr_thread:
                stderr_thread.join(timeout=2)

            inspect_data = self._inspect(name)
            started = self._started(inspect_data)
            state = inspect_data.get("State", {}) if isinstance(inspect_data, dict) else {}
            oom_killed = state.get("OOMKilled") if isinstance(state, dict) and isinstance(state.get("OOMKilled"), bool) else None
            container_exit_code = state.get("ExitCode") if isinstance(state, dict) and isinstance(state.get("ExitCode"), int) else None
            if termination == "normal" and not started:
                termination = "infrastructure"
            if oom_killed is True:
                termination = "oom_confirmed"
            if termination in {"timeout", "output_limit"} and not started:
                termination = "infrastructure"

            if termination != "normal":
                case = classify_case(return_code=container_exit_code, stdout=bytes(collector.stdout), stderr=bytes(collector.stderr), expected=expected, termination=termination)
            elif container_exit_code is None:
                case = classify_case(return_code=None, stdout=bytes(collector.stdout), stderr=bytes(collector.stderr), expected=expected, termination="infrastructure")
            else:
                case = classify_case(return_code=container_exit_code, stdout=bytes(collector.stdout), stderr=bytes(collector.stderr), expected=expected, termination="normal")
            elapsed_ms = (time.monotonic_ns() - start_ns) // 1_000_000
            telemetry = RunnerTelemetry(
                wall_clock_ms=int(elapsed_ms),
                stdout_bytes=len(collector.stdout),
                stderr_bytes=len(collector.stderr),
                total_observed_output_bytes=collector.total_seen,
                container_started=started,
                oom_killed=oom_killed,
                container_exit_code=container_exit_code,
            )
            return ContainerExecution(case, telemetry)
        except (OSError, subprocess.SubprocessError) as exc:
            elapsed_ms = (time.monotonic_ns() - start_ns) // 1_000_000
            case = classify_case(return_code=None, stdout=bytes(collector.stdout), stderr=bytes(collector.stderr), expected=expected, termination="infrastructure")
            telemetry = RunnerTelemetry(int(elapsed_ms), len(collector.stdout), len(collector.stderr), collector.total_seen, False, None, None)
            return ContainerExecution(case, telemetry)
        finally:
            if process and process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except (ProcessLookupError, PermissionError, OSError):
                    process.kill()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    pass
            self._remove(name)


def load_test_suite(path: str | Path) -> tuple[dict[str, Any], str]:
    raw = Path(path).read_bytes()
    suite = load_json_strict(raw)
    if not isinstance(suite, dict) or set(suite) != {"schema_version", "cases"}:
        raise ValueError("test suite must have schema_version and cases")
    if suite["schema_version"] != "vap.tests.v0.1":
        raise ValueError("unsupported test suite schema_version")
    cases = suite["cases"]
    if not isinstance(cases, list) or not cases or len(cases) > 10000:
        raise ValueError("test suite cases must contain 1..10000 cases")
    for index, case in enumerate(cases):
        if not isinstance(case, dict) or set(case) != {"stdin", "expected_stdout"}:
            raise ValueError(f"test case {index} must contain stdin and expected_stdout only")
        if not isinstance(case["stdin"], str) or not isinstance(case["expected_stdout"], str):
            raise ValueError(f"test case {index} stdin/expected_stdout must be strings")
    from .canonical import digest_json
    return suite, digest_json(suite)
