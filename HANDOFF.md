# HANDOFF: Amazon Payday Planner

Repository: https://github.com/PabloMoraleh/amazon-payday-planner

## Product decisions

- This is a wishlist and budgeting planner. It never purchases products or stores payment details or shop credentials.
- Users can make accounts with email and password. Supabase Auth handles passwords.
- The interface supports English, Spanish, French and German.
- Payday reminders are postponed. Do not require a user to disclose their payday just to use the app.
- The owner is learning software development and wants to understand the code. Conversation is in Spanish; source code, comments, branch names, commits and docs are in English.

## Current architecture

- Python and Flask web app.
- Supabase Auth for accounts; Supabase Postgres for shared, persistent data.
- PostgreSQL row-level security isolates each user's wishes, price history and budgets.
- Flask-Session stores Supabase tokens server-side. Development uses a local filesystem cache; deployed environments require Redis.
- Flask-Babel handles interface translations.
- Jenkins runs automated checks through the repository's `Jenkinsfile`.

## Current implementation state

The `feature/auth` branch contains an initial implementation of:

- Email/password sign-up, sign-in and sign-out routes.
- CSRF protection and server-side sessions with secure cookie settings.
- A Supabase migration for user-owned tables and RLS policies.
- A protected wishlist listing page and basic data-access helpers.
- English, Spanish, French and German strings for the account and wishlist pages.
- Jenkins test pipeline and automated tests using a fake Supabase client.

The migration has **not** been applied to any hosted Supabase project. The Supabase project URL and publishable key have not been configured in this checkout. Do not ask for or use a service-role key or database password in the web app.

The repository copy used in this Codex chat is separate from the user's GitHub Codespace. It was synced from `origin/main` and has a local `feature/auth` branch. Keep the branch workflow in the repo: review changes, push the feature branch, open a PR, then merge after approval. Never include `.env`, local session files or database files.

## Important files

- `app.py`: Flask app, auth routes, locale selection and protected page.
- `db.py`: Supabase-backed wish data operations.
- `supabase/config.jsonc`: local Supabase CLI configuration.
- `supabase/migrations/`: versioned database schema and RLS policies.
- `templates/auth.html`, `templates/wishes.html`: account and wishlist screens.
- `translations/`: gettext catalogs for Spanish, French and German; English is the source language.
- `tests/`: tests that do not connect to a hosted Supabase project.
- `Jenkinsfile`: dependency setup, translation compilation and test execution.
- `.env.example`: local variable names with placeholders only.

## Environments and deployment

The code distinguishes local development, automated tests and production configuration. The actual hosted development/test/production projects and deployment stages still need to be set up. Use separate Supabase projects and secrets per environment; do not point test credentials at production. Production startup requires `SECRET_KEY`, `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY` and `SESSION_REDIS_URL`.

Jenkins currently runs tests only. Connect a Jenkins Multibranch Pipeline to this GitHub repository so it discovers the `Jenkinsfile`; configure the GitHub webhook and Jenkins credentials in Jenkins itself. Deployment stages must wait until the hosting provider and environments are selected.

## Next work

1. Configure a separate Supabase development project and apply the checked-in migration there.
2. Set the development `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY` and `SECRET_KEY` in the Codespace secret store; test account confirmation and sign-in against that project.
3. Add forms/routes for creating, editing, deleting and marking wishes as bought; retain RLS on every request.
4. Connect Jenkins as a Multibranch Pipeline and confirm pull-request checks run.
5. Create separate test and production Supabase projects, choose a hosting provider, then add deployment stages and their secrets.
6. Complete translations for later screens as they are added.

## Development notes

- Money is stored as integer cents; priorities are 1 (highest) through 3.
- The old SQLite database is local-only and is not migrated automatically. Existing sample rows will need an explicit import if they should be kept.
- Supabase CLI v3 targets local resources by default. Use `--remote` explicitly for hosted targets and review every hosted change before applying it. Never run a migration against production during development.
- To extract and compile translations, use `pybabel extract`, `pybabel update` and `pybabel compile` with `babel.cfg` from the repository root.
- Run automated tests with `.venv/bin/python -m pytest -q` (or `python -m pytest -q` in the Codespace virtual environment).
