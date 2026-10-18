"""Safe, content-addressed source snapshotting."""
from __future__ import annotations

import hashlib
import os
import stat
import unicodedata
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from .canonical import digest_json


@dataclass(frozen=True)
class SourceSnapshot:
    digest: str
    file_count: int
    total_bytes: int
    entries: tuple[dict[str, Any], ...]


def _safe_relative_path(relative: str) -> str:
    path = PurePosixPath(relative.replace(os.sep, "/"))
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("unsafe source path")
    if ".git" in path.parts:
        raise ValueError(".git metadata is not accepted in a submission snapshot")
    if any(unicodedata.normalize("NFC", part) != part for part in path.parts):
        raise ValueError("source path components must already be Unicode NFC")
    if len(relative) > 240 or len(path.parts) > 32:
        raise ValueError("source path exceeds v0.1 limits")
    return path.as_posix()


def snapshot_source(root: str | Path, *, max_bytes: int, max_files: int) -> SourceSnapshot:
    base = Path(root)
    if not base.is_dir() or base.is_symlink():
        raise ValueError("submission root must be a real directory")
    entries: list[dict[str, Any]] = []
    total_bytes = 0
    count = 0

    for current, directories, filenames in os.walk(base, topdown=True, followlinks=False):
        current_path = Path(current)
        for directory in list(directories):
            directory_path = current_path / directory
            if directory_path.is_symlink():
                raise ValueError(f"symbolic link directory rejected: {directory_path.relative_to(base)}")
            _safe_relative_path(directory_path.relative_to(base).as_posix())
        for filename in filenames:
            file_path = current_path / filename
            relative = _safe_relative_path(file_path.relative_to(base).as_posix())
            info = file_path.lstat()
            if not stat.S_ISREG(info.st_mode):
                raise ValueError(f"only regular files are accepted: {relative}")
            count += 1
            if count > max_files:
                raise ValueError("source file-count limit exceeded")
            if info.st_size > max_bytes - total_bytes:
                raise ValueError("source byte limit exceeded")
            content = file_path.read_bytes()
            # Detect a file changed during snapshotting rather than digesting a torn view.
            after = file_path.lstat()
            if (info.st_ino, info.st_size, info.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
                raise ValueError(f"source changed while snapshotting: {relative}")
            total_bytes += len(content)
            entries.append({"path": relative, "size": len(content), "sha256": "sha256:" + hashlib.sha256(content).hexdigest()})

    if count == 0:
        raise ValueError("submission must contain at least one regular file")
    entries.sort(key=lambda item: item["path"])
    digest = digest_json({"domain": "vap-directory-v1", "entries": entries})
    return SourceSnapshot(digest=digest, file_count=count, total_bytes=total_bytes, entries=tuple(entries))


def stage_readonly_source(root: str | Path, destination: str | Path, *, max_bytes: int, max_files: int) -> SourceSnapshot:
    """Copy a checked source snapshot into a fresh read-only staging tree."""
    source = Path(root)
    target = Path(destination)
    snapshot = snapshot_source(source, max_bytes=max_bytes, max_files=max_files)
    target.mkdir(mode=0o700, parents=False, exist_ok=False)
    for entry in snapshot.entries:
        relative = PurePosixPath(entry["path"])
        out_path = target.joinpath(*relative.parts)
        out_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        in_path = source.joinpath(*relative.parts)
        # Copy bytes into a new inode: do not bind the submitter's original tree.
        data = in_path.read_bytes()
        out_path.write_bytes(data)
        os.chmod(out_path, 0o444)
    for current, dirs, _ in os.walk(target, topdown=False):
        for directory in dirs:
            os.chmod(Path(current) / directory, 0o555)
        os.chmod(current, 0o555)
    staged = snapshot_source(target, max_bytes=max_bytes, max_files=max_files)
    if staged.digest != snapshot.digest:
        raise ValueError("staged source digest mismatch")
    return snapshot
