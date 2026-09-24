# Clonerd composition standard 0.1.0

Start with [the environment reuse guide](REUSE.md) to run and integrate Clonerd.
This document defines the behavior an integration must preserve.

Status: experimental proposal. HOME `wellmanifest`, SHAPE `domain_pack`.
This document defines Clonerd-specific requirements. Existing Wellmanifest
packs retain ownership of generic vocabulary and lifecycle contracts.
`profiles/clonerd.v1.json` is the closed machine-readable profile; the schema
validates its declaration, not the deployed application or a review decision.

## Ownership and composition

| Concern | Canonical owner / adopted standard |
| --- | --- |
| Application sessions, data, backend and generated HTTP contracts | `clonerd-com/app` |
| PostgreSQL backend work | `clonerd-com/api`; do not assume it replaces app storage |
| Domain pages and API projections | matching `clonerd-com/*-clonerd-com` repository |
| Tokens and shared navigation | `clonerd-com/theme`, `clonerd-com/menu-clonerd` |
| Runtime/workstation orchestration | `vnclone`, `premote`, `premesh`, `prepanel`, `vncguard` |
| Authentication vs authorization | `wellmanifest/auth-lifecycle`, `authority-lifecycle` |
| Accounts and tool isolation | `wellmanifest/account-runtime`, `agent` |
| NL interpretation and process addressing | `wellmanifest/nl-api-llm`, `nl-dsl-llm`, `poa`, `uriprocess` |
| Twin stages and evidence | `wellmanifest/twin-lifecycle` |
| SaaS state and releases | `wellmanifest/saas-lifecycle`, `product-lifecycle`, `deployment` |
| Work ownership and publication | `wellmanifest/new-project`, `ticket-lifecycle`, `worktrees`, `git-lifecycle`, `validation-attestation` |
| Documentation and observations | `wellmanifest/docs`, `logs`, `status` |

These bindings do not claim formal adoption of each pack. Exact inspected source
revisions are in `sources.lock.json`; several upstream packs are experimental.
Product assets, commercial offers, providers and executing controllers remain
in their existing product repositories. This pack implements no authority issuer.

## Normative requirements

**CLONERD-001 — Session presentation.** Anonymous sessions MUST be blue
`#22d3ee`, including login/registration on app and user domains. Demo MUST be
blue even for an authenticated user. Authenticated normal mode MUST be green
`#21efad`; authenticated AUTO MUST be yellow `#facc15`. Precedence is anonymous,
demo, AUTO, normal authenticated. An anonymous AUTO request remains blue and
requires authentication. Hostname, URL query, layout or theme MUST NOT prove
login or authority. The six reference cases cover session/mode combinations;
actual browser tests MUST cover every supported layout and theme separately.

**CLONERD-002 — Identity and tenant isolation.** The server MUST authenticate
and authorize each protected operation against caller and tenant. UI surfaces
are not security boundaries. Cloud accounts, local unlock and device activation
MUST remain distinct. Host-only cookies MUST NOT be represented as federated SSO.
Authentication errors MUST be visible without exposing whether an account exists.
No change of theme or mode may create a session, credential or authority grant.

**CLONERD-003 — Demo and data provenance.** Demo MUST NOT create paid actions,
invoke live integrations or mutate live records. Live/cloud queries MUST NOT
silently substitute local/demo data or server-side fallback credentials. Empty,
unavailable, unauthorized and unsupported MUST remain distinguishable.

**CLONERD-004 — Domains and contracts.** `app` owns the generated aggregate
FastAPI contract; domain projects own projections, not copied business logic.
`get` owns the release catalog, `download` redirects and `sh` owns the installer.
`proxy` exposes bounded provider operations; public `status` excludes private
payloads. OpenAPI projections MUST be generated from the same backend revision.
Operation IDs MUST remain stable except for an explicit compatibility change.
Schema-enum changes MUST regenerate all affected JSON/YAML and domain projections.
Contract freshness MUST be tested against actual generated routes.

**CLONERD-005 — NL and execution.** NL/LLM/cache output is an untrusted proposal.
The same grammar, parameter checks, tenant binding and execution policy MUST run
regardless of translation source. Negation, entities and scope MUST participate
in cache safety. Confidence MUST NOT authorize execution. A plan/proposal MUST
NOT be reported as executed; unsupported execution returns an explicit error.
Registered URI processes MUST distinguish queries from commands and retain traces.

**CLONERD-006 — Twins and runtime.** A host record, simulated twin or session
reference MUST NOT be reported as a provisioned machine or successful KVM action.
Execution requires bounded external authority and a result receipt. Inventory
MUST NOT copy secrets; account-runtime and lifecycle evidence remain separate.
Native installers MUST be reported as built/signed/deployed only with evidence.

**CLONERD-007 — Continuation and ownership.** Resume the matching durable ticket
before starting another implementation. A distinct request MUST be queued and
allocated independently. Exactly one writer owns a ticket/worktree. Expiry
MUST NOT transfer ownership. A protected controller MUST observe explicit handoff
or owner disappearance, then use expected revision/fencing and re-observe HEAD,
dirty state and receipts before granting a new bounded lease. A local JSON edit,
new parallel store or this profile MUST NOT substitute for that controller.
If no transport exists, checkpoint the exact blocker and preserve work.

**CLONERD-008 — Verification and publication.** OneDev owns isolated tests;
Validator owns independent exact-subject review/publication. Candidate tests
MUST have no publishing credentials. Head, base, ticket, repository, profile
and policy MUST be bound to evidence. Retain all required protected checks;
only protected policy migration may replace one. Self-approval and admin bypass
are prohibited by this profile. Local PASS is not trusted approval. Profile
configuration, executor deployment, successful canary and actual merge MUST be
reported separately. Revalidate when the tested head or base changes.

**CLONERD-009 — Feedback and truthful status.** Failed commands MUST display a
visible, escaped, dismissible message in each layout. Status feedback MUST NOT
be counted as conversation history; clearing chat removes user/agent history
while preserving any separate confirmation. Report completed, local commit,
pushed/PR, and merged/deployed states independently.

## Compatibility and adoption

This initial version adds a proposed composition profile without migrating any
runtime, data, API or existing lease. A consumer adopts a reviewed immutable
revision and verifies negative cases through its protected CI. Unknown schema
fields, removed gates and weaker authority declarations reject. Dependency pins
are review inputs, not permission to execute upstream code. A passing profile
validator certifies only this fixed declaration; behavioral conformance needs
consumer tests and independently obtained evidence.
