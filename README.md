# Payday Planner

> Rank what you want to buy and see what your next payday can afford.

**Status:** 🚧 Work in progress. This README describes what the project is meant to do; the checklist below shows what already works.

## Why this exists

<!-- TODO: rewrite this section in your own words (2-3 sentences).
     What problem do you have today? How do you handle "I'll buy it as soon as I get paid" right now?
     Example angle: a notes app / spreadsheet that gets messy, impulse buys, forgetting what you wanted. -->

I keep a mental list of things I plan to buy "as soon as I get paid". Payday Planner turns that list into something I can rank, budget against and actually follow.

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
- **SQLite** for storage
- **pytest** for tests
- **React** for the frontend (planned, phase 3)

## Getting started

> Not runnable yet. These are the intended steps once phase 1 is done.

```bash
git clone https://github.com/PabloMoraleh/payday-planner.git
cd payday-planner
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask run
```

## Roadmap

- [ ] **Phase 1:** Flask + SQLite backend: add, list and delete wishes
- [ ] **Phase 2:** budget logic with tests
- [ ] **Phase 3:** React frontend
- [ ] **Phase 4:** payday reminders, a "cooling-off" period for new wishes, monthly spending history

## License

[MIT](LICENSE)
