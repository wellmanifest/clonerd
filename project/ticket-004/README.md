# Ticket 004: Harden conformance symlink-parent traversal, non-finite floats, surrogates, and simulator cookie-host canonicalization

- **ID**: ticket-004
- **Owner**: agent:antigravity
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT
- **Created**: 2026-11-12

## Session authorization

- `SESSION_EXECUTION_AUTHORIZATION`: Autonomous execution, testing, and protected publication requested by the repository owner.

## Goal and scope

Harden `standard/conformance.py` and `tests/test_conformance.py` (`< 500` lines each):

1. **Filesystem & JSON parser bounds (`read`)**: Reject symlinked ancestor segments before `..` collapse (`CLONERD-IO-001`), NUL-byte paths (`CLONERD-IO-002`), and inode swaps between `os.lstat` and `os.fstat`; reject float-overflow `1e309`/`-1e309` (`CLONERD-PROFILE-004`) via `parse_float` and lone UTF-16 surrogates (`\ud800`..`\udfff`) in JSON keys/strings (`CLONERD-PROFILE-005`).
2. **Environment URL & simulator cookie-host canonicalization (`validate_environment`)**: Reject DEL (`0x7F`), C1 controls (`0x80..0x9F`), and lone surrogates in endpoint URLs (`CLONERD-ENV-002`), prohibit reserved/broadcast IPs (`255.255.255.255`, `::ffff:255.255.255.255`) on service deployments (`CLONERD-ENV-006`), and canonicalize loopback host aliases (`[::1]` vs `[0:0:0:0:0:0:0:1]`, `localhost.` vs `localhost`) so simulator `identity` and `device` endpoints cannot share cookies via alternate spellings (`CLONERD-ENV-005`).

## Acceptance criteria

- [x] AC-01: Scope is approved by a human owner (autonomous hardening and testing requested by repository owner).
- [x] AC-02: `ruff check --no-cache`, `python3 standard/conformance.py`, `python3 -m unittest discover -s tests -v`, `./project/governance-check.sh --base origin/main`, and `wellman check` pass with 0 errors and all owned Python files remain `< 500` lines.

## Tracking boundary

This directory contains the minimal reviewed intent. Optional participant prose
and raw command logs are not required delivery output.
