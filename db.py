import sqlite3

DATABASE = "payday.db"


def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
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


def add_wish(name, price_cents, priority=2, url=None, notes=None):
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO wishes (name, price_cents, priority, url, notes) "
        "VALUES (?, ?, ?, ?, ?)",
        (name, price_cents, priority, url, notes),
    )
    conn.commit()
    wish_id = cursor.lastrowid
    conn.close()
    return wish_id


def list_wishes():
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM wishes "
            "WHERE status = ? "
            "ORDER BY priority ASC, created_at ASC",
            ("wanted",),
        ).fetchall()

        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_wish(wish_id):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM wishes WHERE id = ?",
            (wish_id,),
        ).fetchone()

        return dict(row) if row is not None else None
    finally:
        conn.close()


def update_wish(wish_id, name, price_cents, priority, url, notes):
    conn = get_connection()
    try:
        cursor = conn.execute(
            "UPDATE wishes "
            "SET name = ?, price_cents = ?, priority = ?, url = ?, notes = ?, "
            "updated_at = datetime('now') "
            "WHERE id = ?",
            (name, price_cents, priority, url, notes, wish_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def delete_wish(wish_id):
    conn = get_connection()
    try:
        cursor = conn.execute(
            "DELETE FROM wishes WHERE id = ?",
            (wish_id,),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def mark_as_bought(wish_id, bought_price_cents):
    conn = get_connection()
    try:
        cursor = conn.execute(
            "UPDATE wishes "
            "SET status = 'bought', "
            "bought_price_cents = ?, "
            "bought_at = datetime('now'), "
            "updated_at = datetime('now') "
            "WHERE id = ?",
            (bought_price_cents, wish_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


if __name__ == "__main__":
    init_db()
    print("Database ready")