# TapTour

## Local development with Docker

The development setup uses Python 3.12, Django 5.2, and PostgreSQL 17. Install Docker with Compose, then run from the repository root:

```sh
cp .env.example .env
docker compose up --build
```

Or run `make up` (creates `.env` if missing and starts containers in the background). Use `make help` for Docker/Django shortcuts. Django targets require running containers; pass extra arguments with `ARGS`, for example `make check ARGS="--database default"`. `make down` retains database storage.

Open [the health endpoint](http://localhost:8000/health/). It returns `{"status": "ok"}` when Django can query PostgreSQL. No homepage has been implemented yet.

Source files are mounted into the web container and Django reloads Python changes. The web port is bound to localhost; PostgreSQL is available only inside the Compose network. Change `APP_PORT` in `.env` if port 8000 is occupied. PostgreSQL data persists in the `postgres_data` named volume across ordinary container stops and rebuilds.

Useful commands in a second terminal:

```sh
docker compose exec web python manage.py check
docker compose logs -f web
docker compose exec db psql -U taptour -d taptour
docker compose down
```

The `psql` example uses the default database/user from `.env.example`; adjust it if you change them. PostgreSQL initialization variables apply when the data volume is first created; changing the password in `.env` does not change an existing database user's password.

The existing model apps are registered, including `AUTH_USER_MODEL = "accounts.User"`. **Application migrations have not been created or applied.** Startup deliberately does not generate or run migrations. The health endpoint works without application tables; authentication and `/admin/` require the initial migrations. Django may report unapplied built-in migrations until that work is complete. The schema's composite ownership foreign keys must be included when implementing migrations; generating ordinary model migrations alone will not enforce them.

This is a development setup using Django's development server and example local credentials. `.env` is ignored by Git and excluded from the image build. Dependencies are bounded to compatible release ranges; an exact dependency lock and deployment settings are deferred. PostgreSQL readiness uses [Compose's health-based dependency ordering](https://docs.docker.com/compose/how-tos/startup-order/). Django 5.2 is an [LTS release](https://www.djangoproject.com/download/).

## Database design

See [SCHEMA.dbml](SCHEMA.dbml) for the complete proposed 15-table schema and [MODEL_DESIGN.md](MODEL_DESIGN.md) for proposed Django app boundaries and implementation workflows. The design document includes proposed refinements; the DBML remains the field-level schema reference until those refinements are adopted.

Proposed v1 schema for the QR/NFC visitor information platform. This is a design artifact, not deployed Django models or production migrations.

## Open the diagram

1. Open [dbdiagram.io](https://dbdiagram.io/d).
2. Create a diagram if needed.
3. Copy the entire contents of `SCHEMA.dbml` into the DBML editor on the left, replacing its example schema. The right-hand canvas renders the relationships.
4. Save under your own account if you want a persistent hosted diagram. This task does not create or publish an account-hosted diagram.

The file uses native DBML, with PostgreSQL types, named checks, indexes, table notes, and grouped tables. See the [official editor instructions](https://docs.dbdiagram.io/basic-editing-experience/) and [DBML syntax reference](https://dbml.dbdiagram.io/docs/).

## Core concepts

- **Organization:** the customer account, such as a museum trust, municipality, or exhibition organizer. It owns data and defines the access boundary.
- **Collection:** one named group of related stops, such as a gallery, heritage area, or event. It belongs to one organization and does not define a route.
- **Stop:** one independently understandable subject, such as an artifact, temple, or display. Its required `collection_id` means it belongs to exactly one collection. It has no many-to-many collection join table.
- **Stop translation:** the language-specific editorial record for a stop, unique by stop and language.
- **Content revision:** an immutable saved version of that translation, including its media references and localized captions/transcript.
- **Marker:** one physical sign or placement that carries a stable link. The sign can have QR, NFC, or both. Several markers may lead to one stop.

For example: Heritage Office → Historic Courtyard → Stone Water Spout → English and Nepali translations. A sign at each of two entrances creates two markers, not two copies of the stop.

## Scope and proposed decisions

The 15 tables cover access, collection browsing, independent stops, bilingual publishing, media, customer approval, and physical installation checks. English (`en`) and Nepali (`ne`) are initial rows in `languages`; new languages do not require new columns or tables.

The following details are proposals, not previously confirmed product requirements:

- Saved revisions are immutable. A save creates a new revision and updates the working pointer.
- Public collection labels have a small translation table but no separate draft/review workflow in v1. Editing an already visible collection label changes that label immediately. If collection descriptions require approval, add collection revisions before implementation.
- Rich text is stored as sanitized HTML; supporting images form an ordered gallery below it. Arbitrary interleaving of image and text blocks is outside this schema. If the UI requires that behavior, agree on a block model before building the editor.
- Uploaded files become immutable when ready; replacing an audio or image file creates a new asset.
- Customer approval is recorded against the exact saved revision. A reviewer need not have an account.
- Roles are deliberately simple; invitations, configurable role policies, subscriptions, payments, routes, maps, and visitor accounts are not included.
- Visitor analytics are deferred until event definitions and retention are agreed. `audit_events` records staff/system actions, not scans or listening.
- Optional branding media and custom domains are not modeled yet. Add same-organization asset relationships for organization logos/collection covers when their requirements are approved.

## Why revisions are separate

Putting a `published` flag on one editable content row is insufficient: editing that row could change the live experience before approval. Instead, `stop_translations` has two nullable pointers:

- `working_revision_id`: latest saved editorial version.
- `published_revision_id`: exact version visitors receive, or NULL if unpublished.

When both pointers are equal, there are no saved unpublished changes. Saving a new revision moves only the working pointer. Publishing changes only the published pointer and publication metadata; it does not overwrite content.

Creating a translation avoids the circular-reference problem: insert the translation with NULL pointers, insert its first revision and images, then set the working pointer. Perform this in one transaction. Use a row lock on the translation to allocate the next revision number; its unique constraint protects against duplicate numbers.

## Publication transaction

1. Authenticate the actor and verify active organization membership and publishing permission.
2. Lock the relevant organization/collection/stop, translation, and revision review path in a consistent order. All competing lifecycle/review writers must follow the same locking convention.
3. Confirm the organization, collection, and stop are available and the requested revision belongs to this translation.
4. Check the latest approval decision ordered by `(recorded_at, id)` is approved. Serialize approval recording with publication so a simultaneous revocation cannot be missed.
5. Validate a nonempty title and introduction, safe body markup, correct media types, ready files, image alternative text, and a transcript if audio is present. Drafts may be incomplete.
6. Set `published_revision_id`, `published_at`, and `published_by_id` together.
7. Write an audit event containing previous and new revision identifiers in the same transaction.

Unpublishing clears all three publication fields and records an event. Rollback selects an earlier approved revision through the same validation path. The complete content history remains available.

An approval revocation does not silently alter a live page in this proposal. The dashboard must surface it for an authorized publisher to unpublish or replace. Decide whether the business instead requires immediate automatic unpublishing before implementation.

## Translation freshness

`stops.source_language_code` identifies the editorial source language. A translated revision records `based_on_source_revision_id`, referring to a source revision of the same stop. The FK enforces the same stop; the application validates the source language and prevents changing the source-language configuration without an explicit migration workflow.

The dashboard compares this pointer with the source translation's working revision to flag changes awaiting translation. It may separately compare against the source published revision for live-content parity. Do not store a second `is_outdated` flag that can drift out of sync. Outdated translations remain public until deliberately replaced or unpublished.

## Stable links and public access

The link on a sign is `/r/<token>`. It resolves to a canonical stop URL based on `stops.public_id`, independent of collection names and IDs. Moving a stop changes `collection_id`, not its UUID or marker links. Transfers between organizations are excluded.

Generate random URL-safe tokens with collision retries. A token is public and is not an access credential. Issue QR and NFC with the same URL initially, so analytics cannot claim to distinguish the two methods.

The public resolver must verify that the marker is not retired, the organization is active and not archived, the collection and stop are not archived, and at least one language has a published revision. A retired marker shows an explanation; direct access to a still-published stop can continue through another marker.

`collections.is_public` controls whether visitors can browse the collection landing page. It does not disable published individual stops. This permits a project containing only directly scannable pages. Archiving a collection, in contrast, blocks both the landing page and all its stops.

Language selection: requested language if published, then organization default if published, then a deterministic available published language. Indicate fallback explicitly. Never fall back to a draft.

Public media access must be checked against currently visible published revisions. An unpublished revision cannot expose its files through a private preview URL. A file deliberately shared with a public revision is naturally public in that context. Unpublishing cannot retract copies already downloaded; use short-lived delivery URLs/cache policy consistent with the required withdrawal behavior.

## Data integrity and Django mapping

Every entity uses a single primary key (normally Django `BigAutoField`); public stop/collection UUIDs use `UUIDField(default=uuid.uuid4, unique=True)`. The `languages` lookup uses its code as the primary key. Timestamps are timezone-aware.

Some child tables repeat `organization_id` so PostgreSQL can enforce cross-table ownership using composite foreign keys. For example, `(collection_id, organization_id)` must match one collection row. These columns are not independently editable organization choices. Tables such as markers and approval records derive ownership through a single parent and do not duplicate it.

Composite foreign keys also prevent a translation's published pointer from referencing another stop or another language. Nullable pointers use PostgreSQL's default MATCH SIMPLE behavior; the non-null identity columns remain required.

Implement ordinary Django relations and `UniqueConstraint`/`CheckConstraint` declarations, then add the scoped composite foreign keys through explicit migrations where the chosen Django version does not provide the required relation support. Do not assume model `clean()` or form validation protects bulk imports and direct SQL. Migration tests must verify the actual database constraints. See [Django composite-key limitations](https://docs.djangoproject.com/en/5.2/topics/composite-primary-key/) for the framework distinction; this schema does not require composite primary keys.

Use `TextChoices` plus database checks for role and state fields. No PostgreSQL-specific enum migration machinery is needed. Apply case-insensitive email uniqueness with `UniqueConstraint(Lower('email'))` and normalize the login flow consistently.

Set `updated_at` explicitly on every write path, including bulk updates; its creation-time default does not update it automatically. Use ordinary foreign-key indexes when translating the schema to models, in addition to the documented compound indexes.

### Database versus application rules

| Rule | Enforcement |
| --- | --- |
| Exactly one collection per stop | Required foreign key |
| Collection and stop in same organization | Composite foreign key |
| One translation per stop/language | Unique constraint |
| Published/working revision in exact translation | Composite foreign key |
| Assets and content in same organization | Composite foreign keys |
| Unique permanent marker token | Unique constraint; application prohibits later reuse/change |
| Only approved complete content is published | Transactional publishing service |
| Source revision uses the source language | Transactional editorial service |
| Correct image/audio type and private asset delivery | Upload/publishing/access services |
| Saved revision and gallery immutability | Central write service; add database triggers if direct SQL writers must be supported |
| Users may act only within assigned organizations | Server authorization on every request/job |
| Archive, issuance, and timestamp transitions | Service validation and transactional audit |

Foreign keys preserve consistency; they do not authorize reads. Every admin query, preview, export, HTMX endpoint, and background job still needs organization scoping. PostgreSQL row-level security is not included in this proposal.

## Roles

| Role | Proposed permissions within assigned organization |
| --- | --- |
| admin | Membership and organization settings; all editorial and installation actions |
| publisher | Edit, record approval evidence, publish/unpublish, and manage markers |
| editor | Create content, upload media, preview, and prepare installation records; cannot publish or record customer approval |
| reviewer | Preview and record own review decisions; cannot edit content or publish |
| viewer | Read dashboard and previews only |

Recording external approval is distinct from claiming to be the customer approver. Retain the real reviewer name and evidence. Global superusers have explicit platform access; `is_staff` alone is insufficient. These role boundaries should be confirmed before implementation.

## Deletion and retention

All displayed FKs restrict deletion to avoid accidental cascades. Archive organizations, collections, and stops; retire markers; deactivate users. Collection deletion requires no stops and explicit cleanup of collection labels. A historical author's departure must not delete revisions.

Issued markers and approved/published revisions must not be hard-deleted through normal application actions. Unused draft cleanup needs an explicit transaction that removes references in a safe order. Database restriction alone does not stop deleting an issued marker with no checks, so issuance guards remain necessary. A legal retention/anonymization policy needs a separate design before production.

## Verification before migrations

The file was reviewed against the official DBML syntax and checked locally for structural relationship consistency. Installation of the official parser was declined, so successful import in dbdiagram.io or parsing with `@dbml/core` remains to be confirmed. No database has been created or migrated.

When implementation begins, test rejected cross-organization asset links, incorrect publication pointers, duplicate languages/tokens, collection deletion with stops, and source-revision links to other stops. Also test that editing a draft leaves the live revision unchanged and moving a stop preserves its canonical URL and markers.
