"""Canonical JSON subset used by VAP v0.1.

This is intentionally a restricted profile, not a claim of full RFC 8785 JCS
compatibility. Keys must be ASCII, floats are forbidden, strings are NFC, and
integers must fit signed 64-bit range.
"""
from __future__ import annotations

import hashlib
import json
import unicodedata
from typing import Any


def _normalize(value: Any) -> Any:
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int):
        if not -(2**63) <= value <= 2**63 - 1:
            raise ValueError("integers must fit signed 64-bit range")
        return value
    if isinstance(value, float):
        raise ValueError("floating-point values are forbidden in VAP canonical JSON")
    if isinstance(value, str):
        normalized = unicodedata.normalize("NFC", value)
        try:
            normalized.encode("utf-8", "strict")
        except UnicodeEncodeError as exc:
            raise ValueError("strings must contain valid Unicode scalar values") from exc
        return normalized
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str) or not key.isascii():
                raise ValueError("object keys must be ASCII strings")
            normalized_key = unicodedata.normalize("NFC", key)
            if normalized_key in normalized:
                raise ValueError("duplicate keys after normalization")
            normalized[normalized_key] = _normalize(item)
        return normalized
    raise ValueError(f"unsupported canonical JSON type: {type(value).__name__}")


def canonical_bytes(value: Any) -> bytes:
    normalized = _normalize(value)
    encoded = json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return encoded.encode("utf-8")


def digest_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def digest_json(value: Any) -> str:
    return digest_bytes(canonical_bytes(value))


def _reject_constant(token: str) -> None:
    raise ValueError(f"non-standard JSON number forbidden: {token}")


def _parse_int(token: str) -> int:
    if token == "-0":
        raise ValueError("negative zero is forbidden")
    value = int(token)
    if not -(2**63) <= value <= 2**63 - 1:
        raise ValueError("integers must fit signed 64-bit range")
    return value


def _parse_float(token: str) -> None:
    raise ValueError(f"floating-point values are forbidden: {token}")


def _object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def load_json_strict(data: str | bytes) -> Any:
    """Load JSON while rejecting duplicate keys, floats, -0, and invalid numbers."""
    try:
        value = json.loads(
            data,
            object_pairs_hook=_object_pairs,
            parse_int=_parse_int,
            parse_float=_parse_float,
            parse_constant=_reject_constant,
        )
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(f"invalid JSON: {exc}") from exc
    # Run the same recursive checks and normalization at the trust boundary.
    return _normalize(value)
