"""SQLite connection handling and schema creation."""
import os
import sqlite3


def get_db_path() -> str:
    return os.getenv("DATABASE_PATH", "students.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the students table if it does not exist (data persists on disk)."""
    conn = get_connection()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                name            TEXT NOT NULL,
                date_of_birth   TEXT NOT NULL,
                email           TEXT UNIQUE,
                phone           TEXT,
                course          TEXT,
                address         TEXT,
                enrollment_date TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def get_db():
    """FastAPI dependency: one connection per request."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()
