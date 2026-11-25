# HANDOFF: Amazon Payday Planner

Context document so any new session (or collaborator) can pick up the project without re-explaining it.
Repo: https://github.com/PabloMoraleh/amazon-payday-planner

## 1. What the project is

A personal wishlist planner. You list what you want to buy, rank it by priority, set a monthly budget and a payday, and the app tells you which items fit in the budget, in priority order, with links ready so you buy them yourself.

**Non-goals (decided):** it never buys anything automatically and never stores payment details or shop credentials. Amazon only offers an ordering API through Amazon Business (partner onboarding), and scripting the consumer site is fragile and risky for the account. The project is a planning tool, not a shopping bot.

**Why it exists:** portfolio project to restart an abandoned GitHub profile. The goal is a repo that clearly reflects the author's own work, so the author must understand and be able to explain every line.

## 2. Tech stack and environment

- Python 3 + Flask (backend), SQLite via the standard `sqlite3` module (storage)
- pytest (tests, phase 2), React (frontend, phase 3)
- Development in **GitHub Codespaces** (VS Code in the browser) with a virtual environment in `.venv/`
- Run the app: `source .venv/bin/activate` then `flask run` (port 5000; in Codespaces open it from the Ports tab or the "Open in Browser" notification)
- `.gitignore` excludes `.venv/`, `*.db`, `.env`, `instance/`, `__pycache__/`, `.vscode/`, `.DS_Store`

## 3. Current state

Merged into `main`:

- PR #1: README, `.gitignore`, MIT license, minimal Flask app (`app.py`), `requirements.txt`
- PR #2: SQLite schema in `db.py` (`get_connection()`, `init_db()`)

In progress (branch `feature/add-wish`):

- `add_wish(name, price_cents, priority=2, url=None, notes=None)` in `db.py`: inserts a row and returns its id. Written and tested locally (returns `1` on first insert). **Check with `git log` / GitHub whether it has been committed, pushed and merged before continuing.**

Next function to be written by the author: `list_wishes()` (see section 7).

## 4. File structure

```
amazon-payday-planner/
├── app.py            # minimal Flask app, one route "/"
├── db.py             # connection helper, schema, add_wish()
├── requirements.txt  # Flask and its dependencies
├── README.md         # project description (English), roadmap checklist
├── LICENSE           # MIT
└── .gitignore
```

`payday.db` is created locally by `init_db()` and is not committed.

## 5. Database schema (in `db.py`)

- **wishes**: `id`, `name`, `url`, `store` (default 'Amazon'), `asin`, `price_cents`, `currency` (default 'EUR'), `priority` (1-3, default 2), `notes`, `status` ('wanted' | 'bought' | 'dropped'), `track_price` (0/1), `target_price_cents`, `bought_price_cents`, `bought_at`, `created_at`, `updated_at`
- **price_history**: `id`, `wish_id` (FK to wishes, ON DELETE CASCADE), `price_cents`, `currency`, `source` ('manual' | 'tracker'), `recorded_at`; indexed on `(wish_id, recorded_at)`
- **budgets**: `id`, `month` (unique, format `YYYY-MM`), `amount_cents`, `currency`, `payday`

Design decisions:

- **Money is stored as integer cents** (19.99 EUR = 1999) to avoid floating point rounding errors.
- **`status` instead of a `bought` boolean**, so dropped wishes are kept too.
- `track_price`, `target_price_cents`, `asin` and `price_history` exist to support a **future price tracker** without changing the schema.
- `CHECK` constraints make the database reject invalid priorities, negative prices and unknown statuses.
- `PRAGMA foreign_keys = ON` is set on every connection (SQLite ignores foreign keys otherwise).
- `updated_at` is filled on insert; it must be updated **from code** when a wish is modified.
- SQL always uses `?` placeholders, never string formatting (prevents SQL injection).

## 6. Working agreement (how the author wants to work)

- The author is a junior developer with a bootcamp background (HTML/CSS/JS, React with Flux, Flask, SQLAlchemy-style data modeling, JWT, Jest). Conversation is in **Spanish**; **code, comments, commit messages, branch names and docs are in English**.
- **One step at a time.** Give a small number of commands, wait for the author to paste the output, then continue. Verify claims against the pasted output rather than assuming it worked.
- **Git flow:** one branch per task (`feature/<name>`), small commits with imperative messages ("Add ...", "Fix ..."), push the branch, open a pull request, review "Files changed", merge, delete the branch, then `git checkout main && git pull`.
- **Learning goal:** explain what each piece does line by line. The author sometimes asks for the code directly; give it, explain it, and then hand the next small function to the author to write. Review their attempts instead of rewriting them.
- The README section "Why this exists" is a placeholder: the author should rewrite it in their own words.

## 7. Roadmap and next steps

**Phase 1: backend (current)**

1. `list_wishes()`: all wishes with status 'wanted', ordered by `priority ASC, created_at ASC`, returned as a list of dicts (author to write)
2. `get_wish(id)`, `update_wish(...)` (remember `updated_at`), `delete_wish(id)`, `mark_as_bought(id, bought_price_cents)`
3. Call `init_db()` when the Flask app starts
4. Flask routes: list, add, edit, delete, mark as bought (simple HTML templates first)

**Phase 2: budget logic**

- Table `budgets` CRUD (monthly amount and payday)
- Function that takes the wanted items and a budget and returns what fits. Current rule: items in priority order (ties by creation date); an item that does not fit is skipped and the next one is considered. This is a first design and may change after testing with real data.
- pytest tests for the budget logic, including edge cases (empty list, budget of 0, every item too expensive, exact fit)

**Phase 3: React frontend** consuming a JSON API from Flask

**Phase 4: extras**

- Payday reminders (email or Telegram)
- "Cooling-off" period: a wish that stays on the list for N days gains priority
- Monthly spending history
- Price tracker using `price_history`, `track_price` and `target_price_cents` (only through legitimate means; check each site's terms before automating anything)

## 8. Known issues and open questions

- Confirm how to handle wishes in several currencies (the schema has `currency`, the logic assumes one).
- Decide whether skipping an item that does not fit (and continuing) is the right budget rule, or whether to stop at the first item that does not fit.
- Add `requirements.txt` updates whenever a package is installed (`pip freeze > requirements.txt`).
- Port 5000 may be occupied by AirPlay on macOS; use `flask run --port 5001` if running locally on a Mac.

## 9. How to resume

```bash
cd /workspaces/amazon-payday-planner      # or clone the repo
source .venv/bin/activate                 # recreate with: python3 -m venv .venv && pip install -r requirements.txt
git status
git log --oneline -5
git branch
python3 -c "from db import init_db; init_db()"
flask run
```

Then check which branch is active, whether `add_wish` was merged, and continue with the next step in section 7.