# Ticket 002: Harden conformance JSON reads, schema caching, and endpoint origin checks

- **ID**: ticket-002
- **Owner**: agent:antigravity
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-11-11

## Goal and scope

Harden `standard/conformance.py` and expand `tests/test_conformance.py` while keeping all owned Python modules strictly under 500 lines:
- Enforce `O_NOFOLLOW | O_NONBLOCK`, `S_ISREG` regular-file verification, 1 MiB byte bounds, duplicate-key rejection, and non-finite JSON number (`NaN`, `Infinity`, `-Infinity`) rejection in `read()`.
- Cache compiled `Draft202012Validator` instances with `FormatChecker()` via `functools.lru_cache`.
- Harden `validate_environment()` to reject invalid or zero TCP ports, whitespace/control characters in endpoint URLs, and loopback, unspecified, link-local, or multicast origins in non-simulator (`self-hosted` / `existing-service`) deployments.

## Acceptance criteria

- [x] AC-01: `read()` rejects symlinks, non-regular files, files exceeding 1 MiB, duplicate JSON keys, and non-finite JSON constants.
- [x] AC-02: Schema validators are cached with `FormatChecker()` and `validate_environment()` rejects invalid ports and loopback/unspecified/link-local service endpoints outside `local-simulator`.
- [x] AC-03: Unit tests, `ruff`, `./project/governance-check.sh`, and `wellman check` pass with all owned Python files under 500 lines.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
