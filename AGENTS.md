# Project instructions for coding agents

These instructions apply to the entire repository. Follow more specific
instructions in nested `AGENTS.md` files when working in their directories.

## Project context

Build an organization-based QR/NFC visitor information platform using Python,
Django, PostgreSQL, server-rendered HTML, Tailwind CSS, and HTMX.

Read these files before changing architecture or domain behavior:

- `PROJECT_SPECIFICIATION.md`: product requirements and proposed defaults.
- `SCHEMA.dbml`: proposed database structure.
- `MODEL_DESIGN.md`: publishing workflows, constraints, and Django mapping.

Distinguish confirmed requirements from proposals. Do not silently turn an open
decision into a product commitment. Explain material design choices and keep
the relevant documentation synchronized with accepted changes. Once Django
migrations exist, treat them as the executable database history; keep DBML
aligned with their intended schema.

## Collaboration and judgment

- Challenge assumptions when they affect correctness, maintainability, or scope.
- Identify logical gaps and offer concrete alternatives with tradeoffs.
- Prioritize evidence and correctness over agreement. Do not manufacture
  objections when a straightforward implementation is appropriate.
- Complete authorized work and routine reversible fixes without repeatedly
  asking for confirmation. Ask when a missing decision materially changes the
  product behavior or an action needs authorization.

## Python style

- Follow PEP 8 for naming, imports, whitespace, and code organization.
- Limit Python code lines to 79 characters and comments/docstrings to 72
  characters. Wrap expressions naturally rather than using backslashes.
- Use `snake_case` for functions, methods, and variables, `PascalCase` for
  classes, and `UPPER_SNAKE_CASE` for constants.
- Group imports as standard library, third-party, and local imports, separated
  by blank lines. Avoid wildcard imports and unnecessary imports.
- Keep functions focused and prefer clear control flow over deeply nested
  conditions, clever expressions, or compressed one-liners.
- Use specific exceptions. Never silently swallow errors or use a bare
  `except`. Add useful context without logging credentials or private content.

## Type hints

- Add type hints to every parameter of newly written or modified functions and
  methods, except conventional `self` and `cls` parameters.
- Add return type hints, including `-> None` when nothing is returned.
- Annotate constructors, helpers, views, service functions, and test helpers.
- Use concrete domain and Django types when available, such as `HttpRequest`,
  `HttpResponse`, and model types. Use protocols or structured types when they
  clarify an interface.
- Avoid `Any` and suppressed type errors as shortcuts. If framework behavior
  makes either necessary, keep the exception narrow and explain why.
- Use syntax compatible with the project's selected Python version. Type hints
  do not replace runtime validation of requests, uploads, or external data.

## Docstrings and comments

- Give every newly written or modified class, function, and method a short,
  meaningful docstring, including constructors and private helpers.
- Use triple double quotes and a concise first sentence. For functions and
  methods, describe the action, for example: `"""Publish an approved revision."""`.
- Keep simple docstrings to one line. Add detail only for a non-obvious contract,
  side effect, exception, or return value. Do not repeat the signature or list
  obvious parameter types already expressed by type hints.
- Comment complex logic, especially transaction ordering, permission boundaries,
  publication transitions, language fallbacks, and unusual database constraints.
- Explain why an approach is needed or which invariant it protects. Do not
  narrate obvious assignments or add comments to every line.
- Update comments and docstrings when behavior changes. Remove stale comments
  and commented-out code.

## DRY and abstraction

- Keep business rules in one authoritative implementation. Share validation,
  authorization, and publication logic across views, jobs, and management
  commands rather than copying it.
- Extract repeated template fragments into Django includes or shared base
  templates. Reuse form fields and UI components where their behavior matches.
- Prefer Django's built-in features before introducing a custom framework.
- Extract an abstraction when it represents a shared responsibility, not merely
  because two snippets look similar. Avoid speculative base classes, generic
  repositories, or utility modules that hide unrelated behavior.
- Keep request handling in views and multi-step domain operations in focused
  service functions. Do not introduce a service layer for trivial operations
  that ordinary Django forms and models already express clearly.

## Domain and data integrity

- Each collection belongs to exactly one organization. Each stop belongs to
  exactly one collection. Stops remain independently consumable.
- Scope every protected request, query, preview, export, and background job to
  the authorized organization. HTMX requests require the same authorization as
  ordinary requests. `is_staff` alone never grants access to every organization.
- Validate related-object ownership, including media and content revisions.
  Enforce invariants with database constraints where possible; forms and model
  `clean()` alone are insufficient protection for all write paths.
- Saving a draft must not change published content. Approved and published
  revision snapshots and their media references must remain stable.
- Use explicit transactions for publication, approval changes, and other
  multi-record transitions. Use row locks when concurrent writes can violate an
  invariant, and apply a consistent lock order.
- Preserve QR/NFC tokens and canonical stop identifiers when content is edited
  or moved between collections. Never reuse an issued token for another stop.
- Archive or retire issued content and markers through the documented lifecycle.
  Avoid accidental cascading deletion of content, links, and history.
- Keep language data extensible. Do not add separate English and Nepali columns
  to the stop model when translations already have their own records.
- Use timezone-aware datetimes. Update modification timestamps deliberately on
  bulk write paths.

## Django and frontend implementation

- Keep the initial architecture a Django monolith. Do not add a SPA framework,
  public API layer, microservice, or dependency without a concrete requirement.
- Use Django forms for validation and preserve CSRF protection. Public reading
  and essential navigation should work without HTMX.
- Use semantic HTML, accessible form labels, visible focus states, and responsive
  Tailwind layouts. Check Nepali and English text wrapping.
- Prefer template inheritance and includes over duplicated page markup. Avoid
  business logic in templates and unsafe use of `safe` or `mark_safe`.
- Sanitize authored rich text and validate uploaded files. Keep unpublished media
  and previews private. Never store secrets in source control or logs.
- Check query behavior on list/detail screens. Use `select_related` and
  `prefetch_related` when needed to prevent N+1 queries; avoid speculative
  optimization or caching before the access rules are correct.
- Use Django migrations for schema changes. Do not rewrite migrations that have
  already been applied in a shared environment. Document custom SQL constraints
  and provide a safe reverse operation where feasible.

## Verification and tooling

- Inspect existing configuration and use the repository's established commands.
  Do not replace tools or install dependencies merely to satisfy a preference.
- When bootstrapping Python tooling, prefer Ruff for linting and formatting,
  configured for the 79-character code limit and import sorting. Check line
  length explicitly; formatting alone may not wrap every long string.
- If type checking is configured, run it on affected code. Do not claim that type
  annotations have been checked when no checker was run.
- Test meaningful behavior: organization isolation, ownership constraints,
  draft/published separation, approval transitions, language fallback, permanent
  links, and deletion restrictions. Include failure and unauthorized cases.
- Use PostgreSQL for tests that depend on PostgreSQL constraints or locking.
  SQLite passing is not evidence that those behaviors work.
- Run focused tests and the relevant lint/format checks. Broaden testing when the
  change affects shared behavior or existing results reveal an unresolved risk.
- Do not add trivial tests that only repeat implementation details. Small copy
  or styling edits generally need direct verification rather than new tests.
- Never claim a command passed unless it actually ran successfully. Report
  unavailable tools, skipped checks, and remaining validation clearly.

## Completion criteria

- Preserve unrelated user changes and keep the patch scoped to the task.
- Remove temporary debugging code and unused imports introduced by the change.
- Update affected documentation and DBML when domain or schema behavior changes.
- Report what changed, why, which checks ran, and any material limitations.
