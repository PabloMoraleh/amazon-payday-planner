import sqlite3

DATABASE = "payday.db"


def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    # SQLite does not enforce foreign keys unless asked, per connection
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS wishes (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            name               TEXT    NOT NULL,
            url                TEXT,
            store              TEXT    NOT NULL DEFAULT 'Amazon',
            asin               TEXT,
            price_cents        INTEGER NOT NULL CHECK (price_cents >= 0),
            currency           TEXT    NOT NULL DEFAULT 'EUR',
            priority           INTEGER NOT NULL DEFAULT 2
                                       CHECK (priority BETWEEN 1 AND 3),
            notes              TEXT,
            status             TEXT    NOT NULL DEFAULT 'wanted'
                                       CHECK (status IN ('wanted', 'bought', 'dropped')),
            track_price        INTEGER NOT NULL DEFAULT 0
                                       CHECK (track_price IN (0, 1)),
            target_price_cents INTEGER CHECK (target_price_cents >= 0),
            bought_price_cents INTEGER CHECK (bought_price_cents >= 0),
            bought_at          TEXT,
            created_at         TEXT    NOT NULL DEFAULT (datetime('now')),
            updated_at         TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS price_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            wish_id     INTEGER NOT NULL
                                REFERENCES wishes(id) ON DELETE CASCADE,
            price_cents INTEGER NOT NULL CHECK (price_cents >= 0),
            currency    TEXT    NOT NULL DEFAULT 'EUR',
            source      TEXT    NOT NULL DEFAULT 'manual'
                                CHECK (source IN ('manual', 'tracker')),
            recorded_at TEXT    NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_price_history_wish
            ON price_history (wish_id, recorded_at);

        CREATE TABLE IF NOT EXISTS budgets (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            month        TEXT    NOT NULL UNIQUE,
            amount_cents INTEGER NOT NULL CHECK (amount_cents >= 0),
            currency     TEXT    NOT NULL DEFAULT 'EUR',
            payday       TEXT
        );
        """
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("Database ready")