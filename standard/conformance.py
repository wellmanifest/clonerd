"""Offline reference conformance. No repository, lease or network mutations."""
from __future__ import annotations

import argparse
import errno
import functools
import ipaddress
import json
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


def read(path: str | Path) -> Any:
    target = Path(path)
    flags = (
        os.O_RDONLY
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
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
    return json.loads(
        text,
        object_pairs_hook=unique_object,
        parse_constant=_reject_nonfinite_json,
    )


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


def _is_non_service_host(hostname: str) -> bool:
    normalized = hostname.rstrip(".").lower()
    if not normalized or normalized == "localhost" or normalized.endswith(".localhost"):
        return True
    try:
        addr = ipaddress.ip_address(normalized)
    except ValueError:
        return False
    return bool(
        addr.is_loopback
        or addr.is_unspecified
        or addr.is_link_local
        or addr.is_multicast
    )


def validate_environment(value: Any) -> None:
    _validator("schemas/environment.schema.json").validate(value)
    local = value["deployment"] == "local-simulator"
    if local and "device" not in value["endpoints"]:
        raise ValueError("CLONERD-ENV-001: simulator requires device endpoint")
    for url in value["endpoints"].values():
        if any(ch.isspace() or ord(ch) < 32 for ch in url):
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
            if parsed.scheme not in ("http", "https") or parsed.hostname not in (
                "localhost",
                "127.0.0.1",
                "::1",
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
    if (
        local
        and urlsplit(value["endpoints"]["identity"]).hostname
        == urlsplit(value["endpoints"]["device"]).hostname
    ):
        raise ValueError("CLONERD-ENV-005: separate simulator cookie hostnames")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "profile", nargs="?", default=ROOT / "profiles/clonerd.v1.json"
    )
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
