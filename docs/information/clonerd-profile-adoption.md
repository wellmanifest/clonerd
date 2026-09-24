---
{
  "schema": "wellmanifest.docs/document/v1",
  "id": "clonerd-profile-adoption",
  "kind": "information",
  "version": 1,
  "title": "Clonerd profile adoption and evidence boundaries",
  "status": "proposed",
  "owner": "wellmanifest/clonerd",
  "scope": "repository",
  "created": "2026-09-24",
  "updated": "2026-09-24",
  "review_after": "2026-10-24",
  "source_revision": "3804d7bca474dd1dfeb1a29f214fc566d05cbbbd",
  "affected_repositories": [
    "wellmanifest/clonerd"
  ],
  "evidence": [
    "repo://wellmanifest/clonerd/standard/sources.lock.json",
    "repo://wellmanifest/clonerd/standard/CLONERD.md"
  ]
}
---

# Clonerd profile adoption

<!-- docs:section purpose -->
## Purpose

Define how a consumer adopts the proposed Clonerd composition profile without
confusing a declaration with deployed enforcement.

<!-- docs:section scope -->
## Scope

This repository owns the profile and reference conformance fixtures. Product
code, domain projections, theme assets and live authority remain with their
existing owners. Source inventory covers local Git repositories in clonerd-com
and wellmanifest; entry-point review is not an exhaustive audit of every file.
Non-Git workspace directories and external installations are outside that inventory.

<!-- docs:section evidence -->
## Evidence

[sources.lock.json](../../standard/sources.lock.json) binds inspected entry
points and selected architecture documents to exact commits and byte digests.
Historical README claims can lag implementation. Local HEAD is not necessarily
a published revision. The inventory records inputs, not compatibility certification.
App changes may continue independently after this observation.

<!-- docs:section content -->
## Content

1. Review [CLONERD.md](../../standard/CLONERD.md), resolve ownership and select an
   immutable reviewed version. Preserve upstream contract ownership.
2. Map rules to consumer tests: real login/logout and all themes/layouts;
   authenticated demo and AUTO; tenant isolation and no demo side effects;
   contract freshness; negation/scope cache rejection; visible chat errors.
3. Configure the protected OneDev profile and Validator registry for the exact
   consumer. Profile check names are the observed app policy, not requirements
   silently imposed on every ecosystem repository.
4. Independently verify executor image, runtime dependencies, network policy,
   Chromium execution and non-skipped browser coverage. Obtain head/base-bound
   test receipts before Validator review and merge.
5. For lease handoff, locate the existing registered authority, provide explicit
   handoff evidence plus revision/fence, and re-observe dirty state and receipts.
   A new store or manual lease rewrite is not adoption.
6. Record configured, deployed, verified, published and runtime-adopted stages
   separately. Roll back by restoring the previous reviewed consumer pin;
   never roll back shared data or somebody else's work as a documentation step.

<!-- docs:section limitations -->
## Limitations

No controller transport is implemented here. No runtime lease has been renewed.
No OneDev/Validator profile for wellmanifest/clonerd has been deployed by this
change. Passing schema/tests validates the proposed declaration only. Several
composed packs remain experimental. App frontend/backend and generated contracts
need their own tests, review and publication.

<!-- docs:section next_actions -->
## Next actions

The product maintainer owns adoption; the protected delivery operator owns CI
and controller configuration. Review this profile, provision missing authority
transport, then resume app ticket984 using its preserved handoff checkpoint.
Do not use this standard as a workaround for an expired lease.
