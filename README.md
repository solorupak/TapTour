# TapTour

An organization-based visitor information platform for QR and NFC experiences, with English and Nepali content planned for the first release.

Built with **Python 3.12, Django 5.2, PostgreSQL 17, Tailwind CSS, and Flowbite** using server-rendered templates.

## Current status

Implemented: domain models and initial migrations, email login/logout, and an organization-scoped dashboard with collection search, pagination, and summary counts.

Still in development: content management, publishing, uploads, public visitor pages, and QR/NFC workflows. The full ownership constraints and transactional services described in the design documents are not yet implemented.

## Local setup

Requires Docker with Compose. Run from the repository root:

```sh
make setup       # create .env from .env.example if missing
make start       # build and start PostgreSQL and Django
make migrate    # apply migrations
make superuser  # create an email/password account
```

Open [localhost:8000](http://localhost:8000) and sign in. A fresh database shows an empty workspace until organizations and content are created; management screens and automatic demo data are not available yet.

Configuration lives in `.env`. The default port is `8000`; change `APP_PORT` if needed. Migrations are explicit, not run automatically at startup. This configuration is for local development.

## Development commands

```sh
make check
make test ARGS="apps.accounts apps.core"
make logs
make stop       # stop containers; retain database volume
```

Django commands require the containers to be running. For other management commands, use `make manage ARGS="<command>"`.

Compiled frontend assets are included. To edit styles or templates, install Node.js/npm and run:

```sh
npm ci
npm run build   # compile CSS and copy Flowbite assets
npm run watch   # watch CSS/template changes during development
```

Run `npm run build` after frontend changes and include the generated assets with your changes.

## Documentation

- [Project specification](PROJECT_SPECIFICIATION.md) — requirements and proposed workflows
- [Model design](MODEL_DESIGN.md) — domain rules and service design
- [Database schema](SCHEMA.dbml) — DBML design reference
- [Task backlog](GITHUB_TASKS.md) — implementation tasks and issue links
- [GitHub issues](https://github.com/solorupak/TapTour/issues) — tracked work
