"""Offline reference conformance. No repository, lease or network mutations."""
import argparse
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("CLONERD-PROFILE-001: duplicate JSON key")
        result[key] = value
    return result


def read(path):
    return json.loads(Path(path).read_text(), object_pairs_hook=unique_object)


def validate(profile):
    schema = read(ROOT / "schemas/profile.schema.json")
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(profile)


def presentation(authenticated, mode):
    """Reference expectation only; actual session authentication belongs to backend."""
    if type(authenticated) is not bool or mode not in ("demo", "user", "auto"):
        raise ValueError("CLONERD-PROFILE-002: invalid presentation input")
    state = ("anonymous" if not authenticated else "demo" if mode == "demo"
             else "auto" if mode == "auto" else "authenticated")
    accents = {"anonymous": "#22d3ee", "demo": "#22d3ee",
               "authenticated": "#21efad", "auto": "#facc15"}
    return {"state": state, "accent": accents[state], "grantsAuthority": False}


def validate_environment(value):
    schema = read(ROOT / "schemas/environment.schema.json")
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(value)
    local = value["deployment"] == "local-simulator"
    if local and "device" not in value["endpoints"]:
        raise ValueError("CLONERD-ENV-001: simulator requires device endpoint")
    for url in value["endpoints"].values():
        parsed = urlsplit(url)
        if (parsed.username or parsed.password or parsed.query or parsed.fragment
                or parsed.path not in ("", "/") or not parsed.hostname):
            raise ValueError("CLONERD-ENV-002: expected origin without secrets or API path")
        if local:
            if parsed.scheme not in ("http", "https") or parsed.hostname not in ("localhost", "127.0.0.1", "::1"):
                raise ValueError("CLONERD-ENV-003: simulator must stay on loopback")
        elif parsed.scheme != "https":
            raise ValueError("CLONERD-ENV-004: service requires HTTPS")
    if local and urlsplit(value["endpoints"]["identity"]).hostname == urlsplit(value["endpoints"]["device"]).hostname:
        raise ValueError("CLONERD-ENV-005: separate simulator cookie hostnames")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", nargs="?", default=ROOT / "profiles/clonerd.v1.json")
    parser.add_argument("--environment", type=Path)
    args = parser.parse_args()
    if args.environment:
        validate_environment(read(args.environment))
        print("PASS: environment descriptor; network and runtime not tested")
        return
    validate(read(args.profile))
    for row in read(ROOT / "profiles/presentation.examples.json"):
        actual = presentation(row["authenticated"], row["mode"])
        if actual != {key: row[key] for key in actual}:
            raise ValueError("CLONERD-PROFILE-003: presentation fixture mismatch")
    print("PASS: profile and six presentation fixtures; no runtime adoption asserted")


if __name__ == "__main__":
    main()
