import sqlite3
import os
from contextlib import contextmanager

DB_PATH = os.getenv("DB_PATH", "contracts.db")


def init_db():
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS contracts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                counterparty TEXT NOT NULL,
                email_alerts TEXT,
                start_date TEXT,
                end_date TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                renewal_type TEXT DEFAULT 'manual',
                value REAL,
                currency TEXT DEFAULT 'USD',
                notes TEXT,
                reminder_days TEXT DEFAULT '30,14,7',
                extracted_dates TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        conn.commit()


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
