# Ticket 001: Clonerd domain standard

- **ID**: ticket-001
- **Owner**: agent:codex
- **Status**: IN_PROGRESS
- **Workflow state**: EDIT

## Goal and scope

SESSION_EXECUTION_AUTHORIZATION: user requested examination of Clonerd and
Wellmanifest and creation of wellmanifest/clonerd. HOME wellmanifest, shape
domain_pack. This ticket owns a versioned composition profile, normative rules,
source inventory, schema and conformance tests. Runtime services remain in their
existing repositories. No authority-controller implementation or lease takeover.
Accepted seed base: 3804d7bca474dd1dfeb1a29f214fc566d05cbbbd.
Existing app ticket984 remains preserved in its recovery outbox.

## Acceptance criteria

- [x] AC-01: Inventory binds local repositories and reviewed sources to commits.
- [x] AC-02: Standard covers identity, demo, modes, domains, API, NL, twins and delivery.
- [x] AC-03: Closed profile schema and negative conformance tests pass.
- [x] AC-04: Documentation distinguishes proposals, deployed controls and evidence.

## Delivery

Canonical result: [standard](../../standard/CLONERD.md).
Publication and adoption are separate from local conformance validation.

Validation: profile + six presentation fixtures PASS; six unittest methods
(including 16 unsafe mutation subcases) PASS; governance 0 errors/0 warnings.
No remote publication or consumer deployment claimed.
