# QR / NFC Visitor Information Platform

Project specification · Draft v0.2 · 20 September 2026

## 1. Purpose

Build an organization-based platform that delivers information about physical objects and places through QR codes and NFC tags. Visitors open a mobile website, consume information independently, and do not need an account or an installed app.

The initial business is a managed service: our team creates and maintains content, produces translations and audio, supplies signage and tags, installs them, and operates the platform. The software supports this service and can later support customer self-service.

Potential customers include museums, heritage sites, historic-city initiatives, and temporary exhibitions such as auto shows. No first customer segment has been selected. Their shared content workflow is in scope; specialized event and outdoor requirements must be validated in the first deployment.

## 2. Decision status

### Confirmed requirements

- Multi-organization SaaS.
- Each collection belongs to exactly one organization.
- Each stop belongs to exactly one collection.
- Stops are independent; there is no required sequence or chain of information.
- QR codes and NFC tags contain short URLs that lead to published content.
- Content supports text, images/visuals, and audio.
- Multiple languages are supported, initially Nepali and English.
- Separate administrative and public visitor experiences.
- Website first; a native app is a possible future decision.
- Our team will initially handle most content work and offer the complete physical and digital service.
- Main stack: Python, Django, PostgreSQL, HTML, Tailwind CSS, and HTMX.

### Proposed defaults requiring validation

The remaining sections propose implementation and operating defaults rather than recording additional customer commitments. In particular: customer approval workflow, role boundaries, analytics, installation tracking, and content-retirement policies need validation before implementation.

## 3. Product structure and rules

### Organization

An organization is the customer account that owns and controls its collections and content within the platform. It represents the responsible institution, company, municipality, or managing body, rather than an individual staff account or a physical location. It is the main boundary for data access, branding, membership, and service administration.

One organization may manage several venues or events. Our service team can work for multiple organizations through explicit permissions without combining their data. Example: a museum trust is an organization; its staff members are users with membership in that organization.

### Collection

A collection is a named administrative group of related stops owned by one organization. It gives staff a clear place to create, find, review, and maintain those stops. It can represent an exhibition, a gallery, a heritage area, or a temporary event, depending on how the customer operates.

A collection is not necessarily a physical building, a sequential tour, or a museum's legal inventory of artifacts. In this project it means a content-management grouping. Each collection belongs to exactly one organization, and each stop has exactly one owning collection. Collections are flat in the first release; nested collections are not required.

### Stop

A stop is the smallest independently consumable visitor-information unit. It represents one subject that deserves its own page, such as an artifact, temple, monument, vehicle, or explanatory display. A visitor can understand it without opening another stop first.

The stop is the persistent content identity, not the physical QR code or NFC tag. It can contain Nepali and English versions, text, images, and audio, and multiple physical markers can lead to it. Different languages and multiple signs do not create additional stops. Every stop belongs to exactly one collection.

### Examples of the hierarchy

These examples are illustrative and do not represent confirmed customers.

| Organization | Collection | Stop |
| --- | --- | --- |
| Museum trust | Bronze sculpture gallery | Standing bronze statue |
| Municipality heritage office | Historic market square | Stone water fountain |
| Exhibition organizer | Annual motor exhibition | Electric vehicle display |

Use the labels Organization, Collection, and Stop consistently in the dashboard. Visitor pages can use the actual names and context rather than exposing administrative terminology.

```text
Organization
  └── Collection
        └── Stop
              ├── Language content and publication history
              ├── Media references
              └── Physical markers / stable entry links
```

A collection is the administrative home for a group of stops, such as an exhibition, heritage area, or event. It does not impose an order. A separate site/project layer is unnecessary until a distinct requirement emerges.

Rules:

1. A stop cannot exist without a collection or belong to multiple collections.
2. All stop content, revisions, media references, and markers must remain within its organization's access boundary.
3. A stop may move between collections in the same organization without changing its identity or existing entry URLs. Cross-organization transfers are out of scope initially.
4. A stop can have multiple physical markers, for example at separate entrances.
5. Editing titles, content, or language versions must not change printed links.
6. Stops with issued markers are archived rather than hard-deleted. Their links display a useful unavailable or retired message.
7. A collection containing stops cannot be deleted. Stops must first be moved, or the collection and its stops retained as archived records.
8. Future curated routes may reference stops without changing their owning collection. Routes are outside the first release.

## 4. Users and access

| Actor | Proposed responsibilities |
| --- | --- |
| Platform administrator | Manage organizations, staff access, system configuration, and service operations |
| Service team member | Work on assigned organizations; create content, upload media, prepare installations, and publish where authorized |
| Organization administrator/reviewer | Access their organization, preview content, approve or request corrections, and view published information |
| Visitor | Read or listen to publicly published content without authentication |

Customer editing is not required for the first release. Approval may initially be received outside the platform and recorded by staff with reviewer, date, and evidence/reference. An interactive customer approval portal can follow later.

Organization access must be enforced by Django on every protected request, including HTMX requests, previews, downloads, and media access. Hiding controls in HTML does not enforce permissions. Platform-wide access must be explicit rather than the default for all staff.

## 5. Visitor experience

### Entry flow

1. Visitor scans a QR code, taps an NFC tag, or types the printed URL.
2. The platform resolves the stable marker token.
3. The visitor sees the stop's published content in an available language.
4. They read, view images, or choose to play audio.
5. They can change language while remaining on the same stop.

The page should show an identifying title/image, a short introduction, optional audio, deeper text, and captioned images. Collection browsing may be added, but consuming one stop must never depend on it.

Visitor requirements:

- Responsive layouts, with mobile use as the primary design case.
- No login, installation prompt, or mandatory onboarding.
- No automatic audio playback.
- Text usable before large media finishes loading.
- Visible language selection; remember the visitor's selection where practical.
- Clearly identified fallback when the requested language is unpublished or absent.
- Semantic HTML, keyboard access, readable contrast, image alternative text, and audio transcripts.
- Nepali text rendered and manually checked on representative mobile devices.
- Clear behavior for invalid links, unpublished stops, and retired content.

First-release visuals mean uploaded images with captions. Video, AR, interactive diagrams, and unrestricted page builders are excluded.

## 6. Content and language workflow

Service workflow:

```text
Collect sources → Write → Translate → Produce audio → Review
→ Record customer approval → Publish → Install → Verify → Maintain
```

Each language has its own title, short introduction, body, captions/alternative text, audio, transcript, and publication state. Images can be shared across languages when appropriate.

Use a structured content form rather than an unrestricted visual editor. The exact rich-text editor is an implementation choice; output must be sanitized and must not permit arbitrary scripts or embedded HTML.

Publishing behavior:

- Saving changes updates a draft; it never silently modifies the live page.
- A preview displays the exact proposed revision to an authorized reviewer.
- Approval is associated with a specific revision. Further edits require review of the changed revision.
- Publishing explicitly selects the revision visitors receive.
- Publishing one language does not automatically publish another.
- Preserve previously published revisions for audit and recovery.
- Unpublishing removes public content but preserves the marker and internal records.
- Editing source-language content flags related translations for review; it does not automatically unpublish them.

Maintain internal source notes for historical or factual claims. Customer approval is acceptance of content, not proof that every claim is correct. Translation and audio quality need human review before release.

## 7. QR, NFC, and installation management

Use a short domain controlled by the service, with opaque stable tokens such as `/r/<token>`. Domain renewal and continuity are operational requirements because printed URLs can remain in use for years.

The resolver looks up a marker and sends the visitor to an internal published stop URL. Prefer a temporary redirect when the destination may change; do not rely on permanently cached redirects. Allow only platform-controlled destinations in the first release, avoiding an arbitrary external redirect feature.

Proposed defaults:

- QR and NFC on one sign use the same marker URL.
- The sign also includes a readable URL and a short instruction.
- Export print-ready QR artwork with adequate contrast and clear surrounding space.
- NFC programming uses the generated URL; generating a URL does not program a physical tag.
- Record placement, marker code, installation status, and verification date.
- Verify both scanning and tapping on-site after installation.
- Retired markers display an explanation rather than a generic error.
- Do not silently reuse a marker for an unrelated stop: old photos and bookmarks may still reference it.

If QR and NFC share a URL, analytics cannot reliably distinguish a scan from a tap. Separate entry identifiers are a future option if that distinction has business value.

Tag type, sign material, attachment method, and weather resistance must be selected for the physical site. NFC does not bypass the need for internet access to load uncached website content.

## 8. Initial dashboard scope

- Organizations, memberships, and access management.
- Collections and independent stops.
- Nepali and English content editing with extensible language support.
- Image and audio upload, captions, alternative text, and transcripts.
- Draft previews, recorded approval, publication, and archive actions.
- Stable marker links, QR export, and installation records.
- Basic audit history for consequential actions.
- Basic aggregated page and audio usage, subject to the analytics decisions below.

The dashboard should guide staff through production status and missing work, rather than only providing database forms.

## 9. Technical architecture

Use a Django monolith with server-rendered HTML. PostgreSQL stores application data. Tailwind CSS styles public and administrative templates. HTMX adds targeted interactions such as inline editing, language panels, and status changes. Public reading and navigation should work without HTMX.

```text
Visitor / staff browser
       ↓
Django routes, views, forms, templates, authorization
       ├── PostgreSQL: organizations, content, revisions, markers
       └── Media storage: images and audio
```

Suggested Django application boundaries:

| Application | Responsibility |
| --- | --- |
| accounts | Users, organization membership, and permissions |
| organizations | Organizations and collections |
| content | Stops, language content, revisions, approval, publication |
| media | Upload validation, metadata, and media access |
| markers | Short-link resolution, QR generation, installation records |
| analytics | Minimal events and aggregated reporting, if included |

These are code-organization proposals, not separate services. Use Django admin for internal support tasks and build a focused dashboard for routine content production. A public REST API, SPA, and microservices are unnecessary for the initial requirements.

Store production media outside application source/deployment directories, with durable storage and backups. Keep unpublished assets private; public media delivery must not expose drafts. Hosting provider, storage provider, caching, background-job tooling, and exact supported dependency versions are decisions for implementation planning.

Use background jobs only when actual work requires them, such as expensive audio processing or bulk exports. Uploaded audio can initially be prepared outside the platform; automated speech generation is not a launch requirement.

## 10. Preliminary domain model

This is a modeling starting point, not a finalized schema or migration specification.

| Entity | Main responsibility and relationships |
| --- | --- |
| Organization | Customer identity, branding, service status |
| Membership | User access to an organization with an explicit role |
| Collection | Organization-owned group of stops; name, description, status |
| Stop | Stable identity, required collection, internal reference, lifecycle status |
| StopLanguage | One record per stop and language; draft and published revision references |
| ContentRevision | Versioned language content, media references, source notes, author, review metadata |
| ApprovalRecord | Approval of a particular revision, reviewer, date, evidence/reference |
| MediaAsset | Organization-owned stored file with type, size, duration/dimensions where applicable |
| Marker | Unique stable token, required stop, placement, installation and retirement status |
| AuditEvent | Actor, action, object, organization context, timestamp |
| UsageEvent / Aggregate | Optional minimal visitor activity and reporting totals |

Important constraints:

- Required foreign keys enforce collection ownership and stop membership.
- Enforce uniqueness of `(stop, language)` and marker tokens in PostgreSQL.
- Published/draft pointers must refer to revisions of the correct stop and language.
- Reject references to media or other objects owned by another organization.
- Publish revisions and update pointers transactionally.
- Derive organization ownership through the collection where practical. If duplicated for performance, explicitly enforce consistency.
- Published revisions must reference stable media; replacing a file must not mutate historical published content unexpectedly.

Revision storage format, reusable collection translations, role granularity, and analytics tables should be settled during detailed model design.

## 11. Security, privacy, and reliability

- Use Django session authentication, CSRF protection, and server-side authorization for dashboard actions.
- Validate uploaded file types and sizes; prevent uploaded content from executing as application code.
- Restrict previews and drafts, including their media.
- Protect accounts and sensitive endpoints against abuse; use HTTPS in production.
- Treat marker tokens as public identifiers, not authentication secrets.
- Back up PostgreSQL and media, and verify restoration before launch.
- Monitor public-link failures, application errors, storage failures, and domain/certificate renewal.
- Define retention and access policies for audit and analytics data before collecting it.

Prefer minimal analytics without persistent visitor identification. Page requests, marker resolutions, and audio-start events are separate measures; none should be presented as a reliable count of unique visitors or completed listening. Avoid counting redirects and resulting page loads as two visits.

Performance must be tested on real devices and the pilot site's connectivity. Exact budgets and expected traffic remain to be agreed. Offline downloads are outside the initial release.

## 12. Service and commercial boundaries

The offering should explicitly scope:

| Component | Items to define in each engagement |
| --- | --- |
| Setup | Site survey, collection setup, visual design |
| Content | Stop count, text length, languages, source research, revision rounds |
| Audio | Recording method, narrator, duration, revisions, rights |
| Installation | Sign quantities/materials, tag programming, mounting, site access |
| Recurring service | Hosting, support, monitoring, included updates |
| Additional work | New stops, major rewrites, re-recording, replacement hardware |

Define customer ownership/licensing of content and recordings, export options, cancellation handling, and how long retired links remain available. Do not promise indefinite hosting by accident. Automated subscriptions and billing are not required for the first version.

## 13. Delivery phases

### Phase 1 — Validate the workflow

Select a real pilot and document its content sources, languages, connectivity, signage requirements, approval owner, and maintenance expectations. Prepare a sample stop and bilingual mobile-page prototype. Validate with actual visitors and customer staff.

### Phase 2 — Build the publishing foundation

Implement organizations, collections, stops, language revisions, media, access control, preview, and explicit publication. Deliver public mobile pages and stable marker resolution with QR export.

### Phase 3 — Run a complete installation

Prepare approximately ten pilot stops, record approval, produce signs/tags, install, and verify. Add the installation records and operational reporting needed to support the pilot. Test backups and restoration.

### Phase 4 — Improve from evidence

Address actual authoring and visitor problems. Expand customer access, reporting, billing, routes, or offline features only when validated demand justifies them.

## 14. First-release acceptance criteria

1. An authorized team member can create an organization, collection, and independent stop.
2. A stop always has exactly one collection; another organization's members cannot access its private data through direct URLs or HTMX requests.
3. Nepali and English content can be edited, previewed, and published independently.
4. Saving a draft does not change the live page. Approval and publication identify the exact revision.
5. Scanning or tapping an installed marker opens the intended published stop without login.
6. A title edit or move between collections within one organization preserves all issued marker links.
7. Visitors can switch available languages and manually play audio, with a transcript available.
8. Unpublished content and media cannot be obtained through public page or asset URLs.
9. Archived stops and retired markers produce clear visitor-facing outcomes.
10. Empty-only collection deletion is enforced; issued stop links cannot be accidentally destroyed by cascading deletion.
11. Representative mobile devices render Nepali text, QR entry, NFC entry, and audio correctly during on-site checks.
12. Database and media restoration has been demonstrated before customer launch.

Use automated tests for tenant isolation, publication boundaries, ownership constraints, stable-link behavior, and lifecycle transitions. Use manual browser and physical-device checks for accessibility, language rendering, signage, NFC, and actual site connectivity.

## 15. Open decisions before detailed implementation

- Working product name, public domain, and short-link domain.
- Pilot customer/site and expected stop count and traffic.
- Whether the default page emphasizes text/images or audio.
- Default language and exact language-fallback behavior.
- Who supplies sources and who has final publishing authority.
- Human or synthesized narration, production process, and asset rights.
- Required customer dashboard access at launch.
- Analytics scope, retention, and reporting expectations.
- Hosting/storage providers, supported dependency versions, recovery objectives, and media limits.
- Hardware procurement, installation responsibilities, and replacement policy.
- Pricing, included revisions, content export, and service-end link behavior.

The next artifact should be a detailed model design with fields, constraints, deletion behavior, publication transitions, and permission rules, derived from this specification after the open workflow decisions are resolved.

## 16. Interface research and recommended starting points

Research reviewed on 20 September 2026. Product references below provide design inspiration; component libraries and templates provide reusable implementation material. The recommendations are our assessment of fit for Django, Tailwind CSS, and HTMX, not a claim that any template implements our domain or permissions.

### Dashboard templates and components

| Candidate | Useful material | Fit and tradeoff |
| --- | --- | --- |
| Flowbite | Admin layouts, CRUD tables, forms, navigation, dialogs | Recommended starting point. Official Django integration guidance exists. Adapt selected HTML layouts into Django templates. |
| TailAdmin HTML | Complete dashboard shell, tables, forms, reusable pages | Useful alternative if its layout is preferred. The HTML edition uses Alpine.js, adding another interaction system alongside HTMX. |
| daisyUI | Tailwind component classes, buttons, cards, inputs, themes | Good alternative for a small custom interface. It is a component library rather than a ready-made publishing dashboard. |

Flowbite's open-source dashboard is MIT licensed and provides CRUD and administrative layouts. Its repository documents Tailwind v3, Hugo, and Webpack, so copying the entire starter would introduce an older build structure. Use its layouts as references and follow the current Django integration documentation when selecting compatible package versions. Sources: [Flowbite dashboard repository](https://github.com/themesberg/flowbite-admin-dashboard) and [Flowbite Django guide](https://flowbite.com/docs/getting-started/django/).

TailAdmin's community HTML repository describes an MIT-licensed edition built with HTML, Tailwind, and Alpine.js. Its commercial editions have separate terms. For this project, either retain Alpine only for local UI state or replace those interactions deliberately; HTMX does not automatically replace every client-side behavior. Sources: [TailAdmin community repository](https://github.com/TailAdmin/tailadmin-free-tailwind-dashboard-template) and [commercial licensing overview](https://tailadmin.com/docs/others/license).

daisyUI provides reusable classes such as buttons and cards on top of Tailwind. It offers a practical alternative when we want to compose a compact design system ourselves. Choose it instead of adding several overlapping component libraries. Sources: [daisyUI introduction](https://daisyui.com/docs/intro/) and [usage guide](https://daisyui.com/docs/use/).

### Visitor interface references

Princeton University Art Museum provides a particularly close reference: its Smartify mobile website requires no download and uses gallery QR codes to open information about objects. Study its entry flow and focus on the object; its map does not need to enter our initial scope. Sources: [Princeton mobile experience](https://artmuseum.princeton.edu/visit/mobile-experience) and [live visitor guide](https://princetonart.smartify.org/).

Smartify offers web and mobile visitor guides, including branded progressive web apps without a required app download. Its product approach is relevant to our combination of content, software, and physical delivery. It is a product reference, not a Django template or source-code kit. Source: [Smartify products](https://smartify.org/partners/products).

Bloomberg Connects is useful for multimedia and accessibility inspiration: its public product description includes audio transcripts, captions, image zoom, and font-size adjustment. Borrow the focus on accessible content and optional depth; our first release should retain direct web entry. Source: [Bloomberg Connects](https://www.bloombergconnects.org/).

### Recommended direction

Use one component foundation: current Flowbite components with Tailwind in Django templates, informed by the Flowbite dashboard layouts. Use HTMX for server-driven filtering, pagination, form submissions, and preview refreshes. If a JavaScript component is inserted by an HTMX swap, its initialization and cleanup need deliberate handling. The integration must be tested; the template alone does not supply it.

Build a small custom visitor page using the same spacing, typography, and form conventions. A general-purpose dashboard or tourism booking template brings unnecessary navigation to a page opened beside a physical exhibit. Start with native HTML audio controls and a readable article layout; customize the player only if visitor testing identifies a need.

### Proposed dashboard screens

- Organization selector and overview: assigned organizations, content awaiting review, missing translations, and installation tasks.
- Collection list: collection name, stop count, publication summary, and archive state.
- Collection detail: stop table with English and Nepali publication states, audio availability, marker status, search, and filters.
- Stop editor: language tabs, structured content fields, image/audio controls, source notes, preview, and explicit save and publish actions.
- Marker detail: QR preview, short URL, placement, installation checks, and retirement status.

The overview should emphasize actionable publishing work. Revenue charts and unrelated commerce widgets from template demos should not determine the dashboard design.

### Proposed visitor page order

1. Small organization identity and visible language selector.
2. Stop title and identifying image.
3. Short introduction.
4. Audio controls with duration when audio is available.
5. Longer explanation and captioned images.
6. Clearly labeled transcript and optional collection link.

Use generous touch targets and a font with tested Devanagari support. Keep reading width controlled on desktop and avoid placing required content behind a carousel or modal. These are proposed design choices, not claims about every referenced product.

### Fast implementation sequence

1. Prototype the collection stop table, bilingual stop editor, and public stop page first.
2. Extract shared Django base templates and includes for forms, status badges, language controls, and pagination.
3. Connect the screens to real Django views and forms before adding HTMX enhancements.
4. Verify keyboard behavior, translated labels, mobile layout, and validation errors.
5. Add the remaining management screens using the same components.

Templates accelerate layout work, but they do not implement tenant isolation, content revisioning, language fallbacks, approval rules, or stable marker links. Those remain application work. Verify the chosen edition's license and dependency compatibility before incorporating its assets.
