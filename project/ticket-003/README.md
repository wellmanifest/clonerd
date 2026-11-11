# Ticket 003: Unwrap IPv4-mapped IPv6 addresses in non-service host checks

- **ID**: ticket-003
- **Owner**: agent:antigravity
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-11-11

## Goal and scope

Resolve the Validator advisory from `ticket-002` in `standard/conformance.py` and `tests/test_conformance.py` while keeping all owned Python files strictly under 500 lines:
- Unwrap `ipv4_mapped`, `sixtofour`, and `teredo` embedded IPv4 addresses (and reject IPv6 scope/zone identifiers `%...`) in `_is_non_service_host()` so `https://[::ffff:127.0.0.1]`, `https://[::ffff:0.0.0.0]`, `https://[::ffff:169.254.169.254]`, and `https://[::ffff:224.0.0.1]` cannot bypass non-simulator loopback/unspecified/link-local/multicast checks.
- Add negative test coverage for IPv4-mapped loopback, unspecified, link-local, and multicast IPv6 service origins.

## Acceptance criteria

- [x] AC-01: `_is_non_service_host()` normalizes and classifies embedded IPv4 addresses (`ipv4_mapped`, `sixtofour`, `teredo`) and rejects IPv6 zone IDs.
- [x] AC-02: Unit tests cover mapped loopback, unspecified, link-local, and multicast IPv6 origins, while mapped private intranet IPv4 (`[::ffff:10.20.30.40]`) remains consistent with `self-hosted` LAN behavior.
- [x] AC-03: `ruff`, `unittest`, `./project/governance-check.sh`, and `wellman check` pass with all owned Python files under 500 lines.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
