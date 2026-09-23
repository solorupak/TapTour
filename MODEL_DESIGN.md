# TapTour model design

Status: implementation design based on the project specification. Django models and initial migration files exist under `apps/`; applied migration state has not been verified for TT-02. Composite ownership foreign-key migrations and transactional write services are not yet implemented. Product defaults below remain proposals, especially approval and role policy. Django migrations are the executable database history; `SCHEMA.dbml` describes the intended schema, including constraints still awaiting implementation.

## Application boundaries

Separate apps by responsibility and ownership of business rules, rather than one app per model or dashboard screen.

| App | Owns | Responsibility |
| --- | --- | --- |
| `accounts` | `User` | Authentication and global user identity |
| `organizations` | `Organization`, `Membership` | Customer lifecycle, tenant access, roles |
| `content` | `Language`, `Collection`, `CollectionTranslation`, `Stop`, `StopTranslation`, `ContentRevision`, `RevisionImage`, `ApprovalRecord` | Visitor content structure, editorial history, approval, publication |
| `media` | `MediaAsset` | File validation, storage metadata, immutable ready files |
| `markers` | `Marker`, `MarkerCheck` | Physical entry links, issuance, installation, verification |
| `audit` | `AuditEvent` | Append-only records of consequential staff/system actions |
| `core` | No concrete models | Small, domain-independent shared utilities and abstract timestamp models |

Collections belong in `content`: they organize visitor content and participate in archive/public-visibility rules. They are not part of account administration. `RevisionImage` belongs there too: its ordering, caption, and alternative text are part of a particular editorial revision, not intrinsic file metadata.

Keep approvals and publishing within `content` initially. Splitting them out would create mutual dependencies around the same revision and transaction. `Language` is a shared lookup owned by `content`; organizations reference it for their default language. This small explicit dependency is preferable to inventing another app for one table. Seed languages before creating organizations.

Public and dashboard views can have separate URL modules and templates without duplicating domain models. Defer analytics until event meanings and retention are decided. No billing, routes, visitor accounts, generic workflow engine, or generic translation framework in v1.

Suggested layout, created when implementation starts:

```text
config/                  # project settings and root URLs
apps/
  core/models.py         # abstract CreatedAtModel and TimestampedModel
  accounts/
  organizations/
  content/
    models/              # split by subject only when the file grows
    services/            # editorial, review, publication, lifecycle writes
    selectors.py         # scoped dashboard/public reads
    policies.py          # content permissions and eligibility rules
    urls_public.py
    urls_dashboard.py
  media/
  markers/
  audit/
```

Do not create empty service/repository layers just to match a pattern. Ordinary ORM reads can stay straightforward; reuse selectors where authorization or visibility rules would otherwise be repeated.

## Accepted public-link contract (TT-02)

See the `Marker` docstring in [apps/markers/models.py](apps/markers/models.py)
for a brief explanation of marker and stop URLs.

The [specification's accepted link contract](PROJECT_SPECIFICIATION.md#accepted-link-contract--tt-02-23-september-2026)
is authoritative. `Marker.get_absolute_url()` returns `/r/<token>` without
a trailing slash; `Marker.public_url` prefixes `PUBLIC_BASE_URL` and is the
QR/NFC payload. `Stop.get_absolute_url()` remains `/s/<public-id>/` and
`Stop.public_url` remains the absolute canonical destination/share URL.
No existing helper output or database identity is changed. The owner confirmed
no previously issued links or tags on 23 September 2026.

Both use one configured visitor origin, independent of the dashboard host.
Production issuance requires permanent HTTPS; helpers tolerate a trailing
slash but do not yet enforce the origin contract. TT-22 implements issuance
validation. TT-19 implements the canonical page and TT-21 implements the
retirement-aware, non-cacheable temporary HTTP 302 resolver. No public route
is implemented by these helpers. Separate placement URLs support independent
retirement, at the cost of a redirect and lookup; direct stop URLs cannot
provide placement-specific retirement or identification. Existing/future
issued URLs must retain their origin, token/UUID, and target identity.

## Shared conventions and DRY

- Internal IDs: integer primary keys. Public collection/stop IDs: generated unique UUIDs. Marker entry URLs use a separate opaque unique token.
- Mutable records use `created_at` and `updated_at`; immutable records need creation/event timestamps, not a misleading update field. Explicitly maintain update timestamps on bulk/service writes.
- Use concrete foreign keys. Do not introduce a generic parent/object relation for ownership, translations, assets, or approval.
- Use an abstract timestamp model for repeated mechanics. Avoid a universal base carrying organization, soft-delete flags, status, and publication fields: those concepts do not apply to every model.
- Store facts once. Derive `has_unpublished_changes`, translation freshness, and current verification summary. Do not store parallel booleans for the same lifecycle.
- `archived_at`, `retired_at`, and `issued_at` represent distinct facts. Avoid adding corresponding `is_archived`, `is_retired`, and `is_issued` fields.
- Repeat `organization_id` only on the content rows identified below to support database-enforced ownership constraints. This is deliberate redundancy with enforcement, not independently editable data.
- Use explicit choices plus database constraints for roles, asset states, approval decisions, and check results.
- Default domain foreign-key deletion behavior is protection. Archive/deactivate/retire historical entities; use explicit cleanup for unused drafts.

DRY applies to repeated knowledge and rules. Similar-looking fields do not justify merging models with different lifecycles.

## Model fields

`?` denotes nullable. Empty optional text uses an empty string rather than NULL. Mutable records include shared creation/update timestamps unless specified otherwise. Exact text length limits are implementation choices; uniqueness, ownership, and lifecycle constraints are part of this design.

### accounts

**User**

- Custom Django user established before initial application migrations.
- `id`, unique login `email`, `display_name`, standard authentication/password and active/staff/superuser fields.
- Case-insensitive email uniqueness and a matching login normalization policy.
- No organization or tenant role on the user: one person can have different roles in multiple organizations.
- Deactivation preserves authorship and review history. Staff status alone grants no tenant access.

### organizations

**Organization**

- `id`, `name`, `default_language → content.Language`, `is_active`, `archived_at?`.
- `is_active` controls service availability; archive represents retained historical closure. An inactive or archived organization cannot expose content publicly.
- Branding assets and custom domains are deferred.

**Membership**

- `id`, `organization → Organization`, `user → accounts.User`, `role`, `is_active`.
- Unique `(organization, user)`, including inactive memberships. Reactivation updates the existing membership.
- Proposed roles: `admin`, `publisher`, `editor`, `reviewer`, `viewer`.
- Cross-organization service-team work uses multiple memberships; platform superuser access is explicit.

### content

**Language**

- `code` primary key, `name`, `native_name`.
- Seed `en` and `ne`; accept extensible language tags rather than limiting codes to two characters.
- No per-language content columns or separate Nepali/English models.

**Collection**

- `id`, unique `public_id`, `organization → Organization`, `internal_name`, `is_public`, `archived_at?`.
- `is_public` enables the collection landing page; it does not gate direct access to published stops.
- Archive gates both the collection and its stops. Deletion is blocked while stops exist.
- Unique `(id, organization)` supports scoped references from stops.

**CollectionTranslation**

- `id`, `collection → Collection`, `language → Language`, `title`, `description`.
- Unique `(collection, language)`.
- Proposed v1 policy: changes to visible collection labels go live immediately. If customer approval must cover these labels, add a collection revision workflow before implementing them; do not pretend stop approval covers them.

**Stop**

- `id`, unique `public_id`, `organization → Organization`, required `collection → Collection`, `internal_name`, `internal_reference`, `source_language → Language`, `archived_at?`.
- Unique `(id, organization)`; enforce `(collection_id, organization_id)` references the same collection row.
- One collection per stop. Moving to another collection in the same organization preserves identity, revisions, and all marker links.
- Organization and source language are not ordinary editable fields after content creation. Cross-organization transfer is excluded; source-language changes require a dedicated migration workflow.

**StopTranslation**

- `id`, `organization → Organization`, `stop → Stop`, `language → Language`.
- `working_revision → ContentRevision?`, `published_revision → ContentRevision?`, `published_at?`, `published_by → User?`.
- Unique `(stop, language)` and `(id, stop, organization)` for scoped references.
- Enforce same-organization stop ownership. Both revision pointers must refer to a revision belonging to this exact translation.
- Publication pointer, timestamp, and publisher are all present or all absent. System publication is outside v1.
- No `status` that duplicates the pointers: unpublished means no published revision; unpublished saved changes means working and published pointers differ.

**ContentRevision** — immutable after transactional creation

- `id`, `organization → Organization`, `stop → Stop`, `stop_translation → StopTranslation`, `revision_number`.
- `title`, `introduction`, `body_html`, private `source_notes`.
- `hero_image_asset → media.MediaAsset?`, `hero_image_alt`, `hero_image_caption`.
- `audio_asset → media.MediaAsset?`, `transcript`.
- `based_on_source_revision → ContentRevision?`, `created_by → User`, `created_at`.
- Unique `(stop_translation, revision_number)`; revision number is positive. Add unique scoped keys required by publication, source, and gallery composite foreign keys.
- Enforce matching translation/stop/organization. A source reference must belong to the same stop; the editorial service additionally checks it is a revision in that stop's source language. Source-language revisions have no source pointer.
- Hero/audio assets must belong to the same organization. Publishing additionally checks their types and ready state.
- Drafts can be incomplete. Publishing requires nonblank title and introduction, valid safe body, meaningful image alternative text, and transcript for audio.
- Sanitize body markup through one content write path. Render previews and public pages from the same safe representation, excluding private notes.

**RevisionImage** — immutable with its revision

- `id`, `organization → Organization`, `content_revision → ContentRevision`, `media_asset → MediaAsset`, `position`, `alt_text`, `caption`.
- Unique `(content_revision, position)`; position is nonnegative. Same-organization composite references to revision and asset.
- A new save copies the gallery rows into the new revision. Binary files remain shared; copying caption/order snapshots preserves history.
- Gallery images follow the body in v1. Arbitrarily interleaved rich-text images require a different editor/storage contract.

**ApprovalRecord** — append-only decision history

- `id`, `content_revision → ContentRevision`, `decision`, `reviewer_user → User?`, `reviewer_name`, `evidence_reference`, `notes`, `decided_at`, `recorded_by → User`, `recorded_at`.
- Decisions: `approved`, `changes_requested`, `revoked`. Effective decision is the latest by `(recorded_at, id)`; index that lookup by revision.
- `decided_at` records when the customer decided; `recorded_at` records when the platform learned it. Backdated evidence must not silently replace the latest recorded decision.
- Keep the actual reviewer identity separate from the staff member recording external approval. Require reviewer identity and evidence for external decisions; internal reviewers may record their own decisions.
- Every new content revision requires its own approval. Revocation adds a record; it does not edit history.
- Proposed policy: revoking approval flags already-live content for publisher action; it does not automatically unpublish it. This needs business validation.

### media

**MediaAsset**

- `id`, `organization → Organization`, `uploaded_by → User`, unique private `storage_key`, `original_filename`, `type`, `mime_type`, `byte_size`, `state`.
- `width?`, `height?`, `duration_ms?`, `checksum`, shared timestamps.
- Kinds: `image`, `audio`; states: `pending`, `ready`, `failed`. Nonnegative byte size/duration; positive dimensions where present.
- Unique `(id, organization)` enables same-tenant asset references. Validate file content, not just extension or submitted MIME type.
- Once ready, the binary and identifying metadata are immutable. Replacing a file creates a new asset; it never overwrites a published asset's key.
- Caption, alt text, transcript, and editorial title belong to revisions, because their language/context can vary.
- No stored `is_public`: access depends on whether an asset is used in an effectively visible published revision. A content selector supplies this decision to the delivery boundary; storage helpers need not import content models.
- Unreferenced failed/pending uploads can be cleaned up explicitly. Retained revision references prevent destructive cleanup.

### markers

**Marker**

- `id`, `stop → content.Stop`, unique `token`, `label`, `placement_notes`, `has_qr`, `has_nfc`, `issued_at?`, `installed_at?`, `retired_at?`, `retirement_reason`, shared timestamps.
- At least one of QR/NFC must be true. Installation requires prior issuance; timestamps must follow the lifecycle order.
- Ownership derives from stop; do not duplicate organization here.
- QR and NFC on one sign share a token. Several signs for one stop are separate markers.
- Token is immutable from creation and never reused. Stop assignment becomes immutable at issuance; changing an unissued marker remains an explicit staff action.
- An issued marker cannot be hard-deleted. Retirement preserves the URL and serves an explanation.

**MarkerCheck** — append-only verification history

- `id`, `marker → Marker`, `checked_by → User`, `checked_at`, `qr_result`, `nfc_result`, `notes`.
- Results: `passed`, `failed`, `not_tested`, `not_present`; index `(marker, checked_at, id)`.
- Validate results against the physical media present when recording the check. After issuance, medium changes need an explicit audited service operation; prior checks describe the configuration tested at that time.
- Installation and successful on-site verification are distinct facts. Derive latest results rather than maintaining a second verification flag.

### audit

**AuditEvent** — append-only operational history

- `id`, `organization → Organization`, `actor_user → User?`, `action`, `entity_type`, `entity_id`, `details`, `occurred_at`.
- Null actor denotes a system action. Details are small allowlisted JSON metadata; do not dump requests, private content, or credentials.
- Index `(organization, occurred_at)` and `(organization, entity_type, entity_id)`.
- Target intentionally has no foreign key so audit survives permitted draft cleanup. The calling service validates target ownership.
- Publication events record old/new revision IDs. This table is not visitor analytics.

## Central write paths

Views, forms, admin actions, jobs, and commands call the same services for consequential writes. Do not implement publication in signals or repeat its rules in each interface.

| Service | Atomic responsibility |
| --- | --- |
| `save_revision` | Authorize editor; lock translation; reject stale expected working pointer; allocate number; create immutable revision and gallery; advance working pointer only |
| `record_approval` | Authorize reviewer/recorder; lock translation; append exact-revision decision and audit event |
| `publish_revision` | Authorize publisher; lock lifecycle/review path; validate ownership, availability, latest approval, text and assets; update publication fields and audit |
| `unpublish_translation` | Authorize publisher; clear all publication fields; write audit event |
| `move_stop` | Authorize actor in organization; lock affected collections/stop; verify same tenant and active destination; change collection and audit |
| `archive_collection` / `archive_stop` | Authorize actor; serialize with publication; archive and audit without destroying pointers/history |
| `issue_marker` / `install_marker` / `retire_marker` | Authorize operator; validate lifecycle; preserve issued identity; update timestamps and audit |

Create a translation initially with null pointers, then create its first revision and set its working pointer in one transaction. This resolves the circular data relationship without weakening pointer ownership constraints.

Publication can select an earlier approved revision. It changes the published pointer only; working content remains where the editor left it. Preview URLs identify an exact revision and require organization access.

Use a consistent locking protocol across competing writes: organization, collections in ID order, stop, translation, then any mutable dependent rows. Resolve/recheck parents after locks to handle a concurrent move. A coarse organization lock is an acceptable initial serialization strategy if used consistently by membership/lifecycle/publication writers; narrow it only if measured contention warrants it. Recheck permission and eligibility under the locks. Save operations also accept the expected working revision to prevent silently overwriting another editor's progress.

Locking translation during both approval recording and publication serializes a simultaneous revocation. All-or-nothing transactions include audit writes. File storage is external to the database transaction: use pending uploads, mark ready only after verified storage, and clean up orphaned files separately.

## Public visibility and authorization

A single content visibility policy serves direct stop pages, marker resolution, language selection, collection listings, and media access:

1. Organization is active and not archived.
2. Owning collection and stop are not archived.
3. Requested translation has a published revision, or use a published fallback.
4. Marker resolution additionally requires a non-retired marker. Direct stop access does not require a marker.

Fallback order: requested language, organization default, then available language code in stable order. Explicitly indicate fallback. Never use the working revision as fallback. Collection landing pages additionally require `is_public`.

All private queries are organization-scoped after verifying active user/membership. Public IDs and marker tokens do not grant private access. Media delivery consults effective publication visibility rather than merely checking whether any historical revision references the file. Ready-file immutability makes concurrent replacement unable to alter published content.

Proposed role policy:

| Role | Permissions within its organization |
| --- | --- |
| admin | Membership/settings plus all content and marker actions |
| publisher | Edit, upload, record external approval, publish/unpublish, manage markers |
| editor | Edit, upload, preview, prepare/check installations; no approval or publication |
| reviewer | Preview and record own decisions; no editing or publication |
| viewer | Read dashboard and private previews |

Issuance/retirement are publisher/admin actions; installation preparation/checks are available to editors. Admins/publishers can record external decisions but must identify the actual approver. Membership changes must not permit self-escalation through a lower-privilege endpoint.

## Database constraints versus service rules

Database constraints enforce required relationships, uniqueness, valid enum values, local timestamp consistency, and same-organization/same-translation references. Ordinary single-column foreign keys alone cannot enforce that a referenced asset belongs to the same tenant.

Retain ordinary single-column model identities. Scoped composite foreign keys need explicit migrations unless the selected Django release supports the exact relationship declaration required. Select and verify framework versions before writing these migrations; model validation alone is insufficient. Add scoped unique keys before adding composite references. Add working/published pointer constraints after both participating tables exist.

Services enforce permission, valid lifecycle transitions, immutable revision writes, publication completeness, source-language correctness, and external-file readiness. Ordinary application admin must not permit direct revision/gallery updates or bypass protected write paths. If direct SQL writers become a supported workflow, add database immutability guards rather than claiming service checks protect those writers.

Archive organizations/collections/stops, deactivate users/memberships, retire issued markers. Do not expose routine deletion of approved/published revisions. Protect all historical user references. Deleting an unused draft is an explicit transaction handling gallery, review, and pointer references; physical file removal follows confirmed reference checks and retention rules.

## Implementation sequence and verification

1. Create project, custom user, timestamp abstractions, language lookup, organizations, and memberships.
2. Add collections, stops, and media metadata with ownership constraints.
3. Add translations, revisions, gallery, review records, then circular pointer constraints.
4. Add audit and transactional editorial/publication services before editable admin forms.
5. Add markers, resolver, private previews, and shared visibility/media policies.

Meaningful database/service tests must demonstrate:

- Cross-organization collection/asset links and wrong-language publication pointers fail at the database boundary.
- Duplicate memberships, stop languages, revision numbers, marker tokens, and gallery positions are rejected.
- Editing and stale concurrent saves cannot silently change live content or overwrite another working revision.
- New revisions do not inherit approval; concurrent review/publication follows the locking policy.
- A same-organization move preserves public identity and issued markers; a cross-organization move fails.
- Archived/inactive parents block public pages and media; private preview requires tenant access.
- Collection deletion with stops fails; issued marker deletion/reassignment is blocked.
- Restoring an older approved publication preserves the working revision and records an audit event.

## Schema reference

[SCHEMA.dbml](SCHEMA.dbml) contains the complete proposed 15-table schema, including gallery and physical check history; Django authentication infrastructure is additional. Use it as the field-level reference. The app boundaries and workflow refinements above are proposals, not an instruction to replace the existing schema. Differences in proposed field names, metadata, or constraints must be reconciled explicitly before implementation. All tables referenced by the current relationship declarations are present; this structural check does not constitute DBML parser or PostgreSQL migration validation.
