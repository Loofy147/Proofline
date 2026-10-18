"""Read Linux cgroup v2 resource counters without inventing missing values."""
from __future__ import annotations

import re
import threading
from dataclasses import dataclass
from pathlib import Path

_MAX_SAFE_INTEGER = (1 << 63) - 1
_COUNTER = re.compile(r"[0-9]+\Z")


@dataclass(frozen=True)
class CgroupV2Metrics:
    cpu_time_ns: int | None
    peak_memory_bytes: int | None

    @property
    def status(self) -> str:
        if self.cpu_time_ns is not None and self.peak_memory_bytes is not None:
            return "CGROUP_V2_MEASURED"
        if self.cpu_time_ns is not None or self.peak_memory_bytes is not None:
            return "CGROUP_V2_PARTIAL"
        return "UNAVAILABLE"


def _parse_counter(value: str) -> int | None:
    candidate = value.strip()
    if not _COUNTER.fullmatch(candidate):
        return None
    parsed = int(candidate, 10)
    if parsed > _MAX_SAFE_INTEGER:
        return None
    return parsed


def cgroup_v2_path_for_pid(
    pid: int,
    *,
    cgroups_root: str | Path = "/sys/fs/cgroup",
    proc_root: str | Path = "/proc",
) -> Path:
    """Resolve the process's unified cgroup beneath the supplied cgroup mount.

    Reject malformed/non-unified entries, traversal, absent processes, symlinks
    that resolve outside the mount, and non-positive/non-integer PIDs.
    """
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        raise ValueError("pid must be a positive integer")
    try:
        raw = (Path(proc_root) / str(pid) / "cgroup").read_text(encoding="utf-8")
        root = Path(cgroups_root).resolve(strict=True)
    except (OSError, UnicodeError, RuntimeError) as exc:
        raise ValueError("could not resolve process cgroup") from exc

    unified_paths = []
    for line in raw.splitlines():
        parts = line.split(":", 2)
        if len(parts) != 3:
            continue
        hierarchy, controllers, path = parts
        if hierarchy == "0" and controllers == "":
            unified_paths.append(path)
    if len(unified_paths) != 1:
        raise ValueError("process does not have exactly one unified cgroup v2 entry")

    virtual_path = unified_paths[0]
    if not virtual_path.startswith("/") or virtual_path.startswith("//"):
        raise ValueError("cgroup v2 path must be absolute")
    segments = virtual_path[1:].split("/") if virtual_path != "/" else []
    if any(segment in {"", ".", ".."} for segment in segments):
        raise ValueError("unsafe cgroup v2 path segment")
    try:
        candidate = root.joinpath(*segments).resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise ValueError("cgroup v2 directory does not exist") from exc
    if not candidate.is_dir() or not candidate.is_relative_to(root):
        raise ValueError("cgroup v2 path resolves outside the cgroup mount")
    return candidate


def read_cgroup_v2_metrics(cgroup_path: str | Path) -> CgroupV2Metrics:
    """Read cgroup v2's cumulative CPU usage and high-water memory counter.

    cpu.stat exposes usage_usec; it is converted to nanoseconds.
    memory.peak is already expressed in bytes. Unreadable or malformed
    counters remain None, never zero.
    """
    directory = Path(cgroup_path)
    cpu_time_ns = None
    peak_memory_bytes = None

    try:
        lines = (directory / "cpu.stat").read_text(encoding="ascii").splitlines()
        values: list[str] = []
        for line in lines:
            fields = line.split()
            if fields and fields[0] == "usage_usec":
                values.extend(fields[1:])
        if len(values) == 1:
            usage_usec = _parse_counter(values[0])
            if usage_usec is not None and usage_usec <= _MAX_SAFE_INTEGER // 1000:
                cpu_time_ns = usage_usec * 1000
    except (OSError, UnicodeError):
        pass

    try:
        raw_peak = (directory / "memory.peak").read_text(encoding="ascii")
        peak_memory_bytes = _parse_counter(raw_peak)
    except (OSError, UnicodeError):
        pass

    return CgroupV2Metrics(cpu_time_ns, peak_memory_bytes)


class CgroupV2Sampler:
    """Thread-safe best-effort sampler for a live container's cgroup v2."""

    def __init__(
        self,
        *,
        cgroups_root: str | Path = "/sys/fs/cgroup",
        proc_root: str | Path = "/proc",
    ) -> None:
        self.cgroups_root = Path(cgroups_root)
        self.proc_root = Path(proc_root)
        self._path: Path | None = None
        self._cpu_time_ns: int | None = None
        self._peak_memory_bytes: int | None = None
        self._lock = threading.Lock()

    @property
    def cgroup_path(self) -> Path | None:
        with self._lock:
            return self._path

    def discover(self, pid: int) -> bool:
        try:
            path = cgroup_v2_path_for_pid(
                pid, cgroups_root=self.cgroups_root, proc_root=self.proc_root
            )
        except ValueError:
            return False
        with self._lock:
            self._path = path
        self.sample()
        return True

    def sample(self) -> CgroupV2Metrics:
        with self._lock:
            path = self._path
        if path is None:
            with self._lock:
                return CgroupV2Metrics(self._cpu_time_ns, self._peak_memory_bytes)
        current = read_cgroup_v2_metrics(path)
        with self._lock:
            # CPU use and peak memory are cumulative/high-water counters.
            if current.cpu_time_ns is not None:
                self._cpu_time_ns = max(self._cpu_time_ns or 0, current.cpu_time_ns)
            if current.peak_memory_bytes is not None:
                self._peak_memory_bytes = max(self._peak_memory_bytes or 0, current.peak_memory_bytes)
            return CgroupV2Metrics(self._cpu_time_ns, self._peak_memory_bytes)

    @property
    def metrics(self) -> CgroupV2Metrics:
        with self._lock:
            return CgroupV2Metrics(self._cpu_time_ns, self._peak_memory_bytes)
