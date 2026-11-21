"""SQLite connection helper and schema for WebiMeet.

Kept in its own module so that app.py and both route blueprints can share the
exact same connection logic without creating circular imports.
"""

import os
import sqlite3

from flask import g

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, "database")
DB_PATH = os.path.join(DB_DIR, "webimeet.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS webinars (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    title        TEXT NOT NULL,
    speaker      TEXT NOT NULL,
    category     TEXT NOT NULL,
    mode         TEXT NOT NULL CHECK (mode IN ('live', 'recorded')),
    video_url    TEXT NOT NULL DEFAULT '',
    description  TEXT NOT NULL DEFAULT '',
    slides_url   TEXT NOT NULL DEFAULT '',
    starts_at    TEXT NOT NULL DEFAULT '',
    duration     TEXT NOT NULL DEFAULT '60 min',
    attendees    INTEGER NOT NULL DEFAULT 0,
    accent       TEXT NOT NULL DEFAULT 'rose',
    icon         TEXT NOT NULL DEFAULT '🎬',
    created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    webinar_id  INTEGER NOT NULL,
    name        TEXT NOT NULL,
    message     TEXT NOT NULL,
    is_question INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (webinar_id) REFERENCES webinars(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS registrations (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_code  TEXT NOT NULL UNIQUE,
    webinar_id   INTEGER NOT NULL,
    name         TEXT NOT NULL,
    email        TEXT NOT NULL,
    seat_code    TEXT NOT NULL,
    status       TEXT NOT NULL DEFAULT 'REGISTERED',
    created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    attended_at  TEXT,
    FOREIGN KEY (webinar_id) REFERENCES webinars(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS reactions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    webinar_id  INTEGER NOT NULL,
    emoji       TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (webinar_id) REFERENCES webinars(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_chat_webinar_id ON chat_messages(webinar_id, id);
CREATE INDEX IF NOT EXISTS idx_reactions_webinar_id ON reactions(webinar_id, id);
CREATE INDEX IF NOT EXISTS idx_reg_ticket ON registrations(ticket_code);
"""


def get_db():
    """Return a per-request SQLite connection with row access by column name."""
    if "db" not in g:
        os.makedirs(DB_DIR, exist_ok=True)
        connection = sqlite3.connect(DB_PATH)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        g.db = connection
    return g.db


def close_db(_error=None):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def init_db():
    """Create the database file and all tables if they do not exist yet."""
    os.makedirs(DB_DIR, exist_ok=True)
    with sqlite3.connect(DB_PATH) as connection:
        connection.executescript(SCHEMA)


def fetch_all(query, params=()):
    return get_db().execute(query, params).fetchall()


def fetch_one(query, params=()):
    return get_db().execute(query, params).fetchone()


def execute(query, params=()):
    db = get_db()
    cursor = db.execute(query, params)
    db.commit()
    return cursor
