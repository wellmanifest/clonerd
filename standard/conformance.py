"""Offline reference conformance. No repository, lease or network mutations."""

from __future__ import annotations

import argparse
import errno
import functools
import ipaddress
import json
import math
import os
import stat
from pathlib import Path
from typing import Any, NoReturn
from urllib.parse import SplitResult, urlsplit

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
MAX_JSON_BYTES = 1_048_576
_PRESENTATION_FIXTURE_KEYS = frozenset(
    {"authenticated", "mode", "state", "accent", "grantsAuthority"}
)


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("CLONERD-PROFILE-001: duplicate JSON key")
        result[key] = value
    return result


def _reject_nonfinite_json(token: str) -> NoReturn:
    raise ValueError(f"CLONERD-PROFILE-004: non-finite JSON constant {token!r}")


def _parse_finite_float(token: str) -> float:
    val = float(token)
    if not math.isfinite(val):
        raise ValueError(f"CLONERD-PROFILE-004: non-finite JSON float {token!r}")
    return val


def _has_surrogate(text: str) -> bool:
    return any(0xD800 <= ord(ch) <= 0xDFFF for ch in text)


def _reject_surrogates(value: Any) -> None:
    stack = [value]
    while stack:
        cur = stack.pop()
        if isinstance(cur, str):
            if _has_surrogate(cur):
                raise ValueError(
                    "CLONERD-PROFILE-005: lone UTF-16 surrogate in JSON input"
                )
        elif isinstance(cur, dict):
            for key, item in cur.items():
                if isinstance(key, str) and _has_surrogate(key):
                    raise ValueError(
                        "CLONERD-PROFILE-005: lone UTF-16 surrogate in JSON input"
                    )
                stack.append(item)
        elif isinstance(cur, list):
            stack.extend(cur)


def _check_no_symlink_path(path: str | Path) -> Path:
    raw_path = os.fspath(path)
    if not isinstance(raw_path, str) or not raw_path or "\x00" in raw_path:
        raise ValueError("CLONERD-IO-002: expected regular JSON file")
    path_obj = Path(raw_path)
    if path_obj.is_absolute():
        cur = Path(path_obj.anchor)
        walk_parts = path_obj.parts[1:]
    else:
        cwd = Path.cwd()
        if len(cwd.parts) > 2 and cwd.is_symlink():
            raise ValueError("CLONERD-IO-001: symlink JSON input rejected")
        for anc in cwd.parents:
            if len(anc.parts) > 2 and anc.is_symlink():
                raise ValueError("CLONERD-IO-001: symlink JSON input rejected")
        cur = cwd
        walk_parts = path_obj.parts
    for part in walk_parts:
        if part in ("", "."):
            continue
        if part == "..":
            cur = cur.parent
            continue
        cur = cur / part
        if len(cur.parts) > 2 and cur.is_symlink():
            raise ValueError("CLONERD-IO-001: symlink JSON input rejected")
    abs_path = Path(os.path.abspath(raw_path))
    if abs_path.is_symlink():
        raise ValueError("CLONERD-IO-001: symlink JSON input rejected")
    for anc in abs_path.parents:
        if len(anc.parts) > 2 and anc.is_symlink():
            raise ValueError("CLONERD-IO-001: symlink JSON input rejected")
    return abs_path


def read(path: str | Path) -> Any:
    target = _check_no_symlink_path(path)
    try:
        before = os.lstat(target)
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise ValueError("CLONERD-IO-001: symlink JSON input rejected") from exc
        if exc.errno == errno.EISDIR:
            raise ValueError("CLONERD-IO-002: expected regular JSON file") from exc
        raise
    if stat.S_ISLNK(before.st_mode):
        raise ValueError("CLONERD-IO-001: symlink JSON input rejected")
    if not stat.S_ISREG(before.st_mode):
        raise ValueError("CLONERD-IO-002: expected regular JSON file")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        fd = os.open(target, flags)
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise ValueError("CLONERD-IO-001: symlink JSON input rejected") from exc
        if exc.errno == errno.EISDIR:
            raise ValueError("CLONERD-IO-002: expected regular JSON file") from exc
        raise
    try:
        st = os.fstat(fd)
        if stat.S_ISLNK(st.st_mode):
            raise ValueError("CLONERD-IO-001: symlink JSON input rejected")
        if not stat.S_ISREG(st.st_mode):
            raise ValueError("CLONERD-IO-002: expected regular JSON file")
        if (before.st_dev, before.st_ino) != (st.st_dev, st.st_ino):
            raise ValueError("CLONERD-IO-002: JSON file inode changed during open")
        if st.st_size > MAX_JSON_BYTES:
            raise ValueError("CLONERD-IO-003: JSON file exceeds 1 MiB limit")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            total += len(chunk)
            if total > MAX_JSON_BYTES:
                raise ValueError("CLONERD-IO-003: JSON file exceeds 1 MiB limit")
            chunks.append(chunk)
    finally:
        os.close(fd)
    text = b"".join(chunks).decode("utf-8")
    decoded = json.loads(
        text,
        object_pairs_hook=unique_object,
        parse_constant=_reject_nonfinite_json,
        parse_float=_parse_finite_float,
    )
    _reject_surrogates(decoded)
    return decoded


@functools.lru_cache(maxsize=4)
def _validator(schema_relpath: str) -> Draft202012Validator:
    schema = read(ROOT / schema_relpath)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def validate(profile: Any) -> None:
    _validator("schemas/profile.schema.json").validate(profile)


def presentation(authenticated: bool, mode: str) -> dict[str, Any]:
    """Reference expectation only; actual session authentication belongs to backend."""
    if type(authenticated) is not bool or mode not in ("demo", "user", "auto"):
        raise ValueError("CLONERD-PROFILE-002: invalid presentation input")
    state = (
        "anonymous"
        if not authenticated
        else "demo"
        if mode == "demo"
        else "auto"
        if mode == "auto"
        else "authenticated"
    )
    accents = {
        "anonymous": "#22d3ee",
        "demo": "#22d3ee",
        "authenticated": "#21efad",
        "auto": "#facc15",
    }
    return {"state": state, "accent": accents[state], "grantsAuthority": False}


def _validate_port(parsed: SplitResult) -> None:
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError(
            "CLONERD-ENV-002: expected origin without secrets or API path"
        ) from exc
    if port is not None and not (1 <= port <= 65535):
        raise ValueError("CLONERD-ENV-002: expected origin without secrets or API path")


def _is_non_prohibited_ip(
    addr: ipaddress.IPv4Address | ipaddress.IPv6Address,
) -> bool:
    return not (
        addr.is_loopback
        or addr.is_unspecified
        or addr.is_link_local
        or addr.is_multicast
        or addr.is_reserved
    )


def _is_non_service_host(hostname: str) -> bool:
    normalized = hostname.rstrip(".").lower()
    if (
        not normalized
        or "%" in normalized
        or normalized == "localhost"
        or normalized.endswith(".localhost")
    ):
        return True
    try:
        addr = ipaddress.ip_address(normalized)
    except ValueError:
        return False
    candidates: list[ipaddress.IPv4Address | ipaddress.IPv6Address] = [addr]
    if isinstance(addr, ipaddress.IPv6Address):
        if addr.ipv4_mapped is not None:
            candidates.append(addr.ipv4_mapped)
        if addr.sixtofour is not None:
            candidates.append(addr.sixtofour)
        if addr.teredo is not None:
            candidates.extend(addr.teredo)
    return any(not _is_non_prohibited_ip(candidate) for candidate in candidates)


def _canonical_simulator_host(hostname: str) -> str | None:
    if not hostname or "%" in hostname:
        return None
    normalized = hostname.rstrip(".").lower()
    if normalized == "localhost":
        return "localhost"
    try:
        addr = ipaddress.ip_address(normalized)
    except ValueError:
        return None
    if isinstance(addr, ipaddress.IPv6Address) and (
        addr.ipv4_mapped is not None
        or addr.sixtofour is not None
        or addr.teredo is not None
    ):
        return None
    compressed = addr.compressed
    if compressed in ("127.0.0.1", "::1"):
        return compressed
    return None


def _has_disallowed_url_char(url: str) -> bool:
    for ch in url:
        code = ord(ch)
        if (
            ch.isspace()
            or code < 32
            or code == 0x7F
            or 0x80 <= code <= 0x9F
            or 0xD800 <= code <= 0xDFFF
        ):
            return True
    return False


def validate_environment(value: Any) -> None:
    _validator("schemas/environment.schema.json").validate(value)
    local = value["deployment"] == "local-simulator"
    if local and "device" not in value["endpoints"]:
        raise ValueError("CLONERD-ENV-001: simulator requires device endpoint")
    for url in value["endpoints"].values():
        if _has_disallowed_url_char(url):
            raise ValueError(
                "CLONERD-ENV-002: expected origin without secrets or API path"
            )
        parsed = urlsplit(url)
        _validate_port(parsed)
        if (
            parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
            or parsed.path not in ("", "/")
            or not parsed.hostname
        ):
            raise ValueError(
                "CLONERD-ENV-002: expected origin without secrets or API path"
            )
        if local:
            if (
                parsed.scheme not in ("http", "https")
                or _canonical_simulator_host(parsed.hostname) is None
            ):
                raise ValueError("CLONERD-ENV-003: simulator must stay on loopback")
        else:
            if parsed.scheme != "https":
                raise ValueError("CLONERD-ENV-004: service requires HTTPS")
            if _is_non_service_host(parsed.hostname):
                raise ValueError(
                    "CLONERD-ENV-006: service endpoint cannot target loopback, "
                    "unspecified or link-local host"
                )
    if local and (
        _canonical_simulator_host(
            urlsplit(value["endpoints"]["identity"]).hostname or ""
        )
        == _canonical_simulator_host(
            urlsplit(value["endpoints"]["device"]).hostname or ""
        )
    ):
        raise ValueError("CLONERD-ENV-005: separate simulator cookie hostnames")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", nargs="?", default=ROOT / "profiles/clonerd.v1.json")
    parser.add_argument("--environment", type=Path)
    args = parser.parse_args()
    if args.environment:
        validate_environment(read(args.environment))
        print("PASS: environment descriptor; network and runtime not tested")
        return
    validate(read(args.profile))
    fixtures = read(ROOT / "profiles/presentation.examples.json")
    if not isinstance(fixtures, list):
        raise TypeError("CLONERD-PROFILE-003: presentation fixture mismatch")
    for row in fixtures:
        if not isinstance(row, dict) or not _PRESENTATION_FIXTURE_KEYS <= row.keys():
            raise ValueError("CLONERD-PROFILE-003: presentation fixture mismatch")
        actual = presentation(row["authenticated"], row["mode"])
        if actual != {key: row[key] for key in actual}:
            raise ValueError("CLONERD-PROFILE-003: presentation fixture mismatch")
    print("PASS: profile and six presentation fixtures; no runtime adoption asserted")


if __name__ == "__main__":
    main()
