# Amazon Payday Planner

> *Not affiliated with or endorsed by Amazon.* Rank what you want to buy and see what your next payday can afford.

**Status:** 🚧 Work in progress. Email/password account flows and the first Supabase schema are implemented; the database migration still needs to be applied to each Supabase environment.

## Why this exists

<!-- TODO: rewrite this section in your own words (2-3 sentences).
     What problem do you have today? How do you handle "I'll buy it as soon as I get paid" right now?
     Example angle: a notes app / spreadsheet that gets messy, impulse buys, forgetting what you wanted. -->

I keep a mental list of things I plan to buy "as soon as I get paid". Amazon Payday Planner turns that list into something I can rank, budget against and actually follow.

## What it does

- Keep a wishlist: name, link, estimated price and priority (1 = most important).
- Set the budget you are willing to spend this month.
- On payday, see which items fit in the budget, in priority order, with the links ready so you can buy them yourself.
- Mark items as bought to keep a simple history.

### What it deliberately does not do

- It **never buys anything for you** and never stores payment details or shop credentials.
- It is a planning tool, not a shopping bot.

## How the budget logic works

Items are taken in priority order (ties broken by the date they were added). Each item is added to the plan if it still fits in the remaining budget; if it does not, it is skipped and the next one is considered.

> This is the first design. It may change as I test it with real wishlists.

## Tech stack

- **Python** + **Flask** for the backend
- **Supabase Auth** for email/password accounts
- **Supabase Postgres** with row-level security for user-owned data
- **Redis-backed server sessions** in production; filesystem sessions for local development
- **Flask-Babel** for English, Spanish, French, and German interface text
- **pytest** for automated checks
- **React** for the frontend (planned, phase 3)

## Getting started

```bash
git clone https://github.com/PabloMoraleh/amazon-payday-planner.git
cd amazon-payday-planner
# Python 3.11 or newer is required by the Supabase Python SDK.
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Fill in SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY, and a random SECRET_KEY.
flask run
```

Apply the checked-in database migration to the matching Supabase project before using the wishlist. For local Supabase development, use the Supabase CLI and its local database; for hosted environments, apply migrations only to the intended project.

## Environments and CI

- **Development:** local Flask app and a separate Supabase development project (or local Supabase stack). Uses filesystem-backed sessions by default.
- **Test:** Jenkins runs the automated test suite with a fake Supabase client. Tests do not contact a Supabase project.
- **Production:** set `APP_ENV=production`, a long random `SECRET_KEY`, `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, and `SESSION_REDIS_URL` in the hosting platform's secret store. Production startup fails if any required secret, Supabase setting or Redis session store is missing.

The `Jenkinsfile` installs dependencies, compiles translations and runs tests. Configure Jenkins with a Multibranch Pipeline and a GitHub webhook to run it for branches and pull requests. Deployment stages are intentionally not configured yet because the production hosting provider and the separate test/production Supabase projects have not been selected. Do not point test or development settings at the production project.

## Roadmap

- [x] **Phase 1 foundation:** Flask email/password auth, Supabase schema and per-user row-level security
- [ ] **Phase 1:** complete wish create, edit, delete and purchase routes
- [ ] **Phase 2:** budget logic with tests
- [ ] **Phase 3:** finish translations across the complete interface (English, Spanish, French and German)
- [ ] **Phase 4:** separate hosted environments and Jenkins deployment stages
- [ ] **Later:** payday reminders, a "cooling-off" period for new wishes, monthly spending history

## License

[MIT](LICENSE)
