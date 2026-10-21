"""All database operations. Every query is parameterised (no SQL injection)."""
import sqlite3
from datetime import date
from typing import Any, Optional

COLUMNS = ["name", "date_of_birth", "email", "phone", "course", "address", "enrollment_date"]


def _serialise(data: dict) -> dict:
    return {k: (v.isoformat() if isinstance(v, date) else v) for k, v in data.items()}


def _where(name=None, course=None, email=None, born_after: Optional[date] = None,
           born_before: Optional[date] = None):
    clauses, params = [], []
    if name:
        clauses.append("name LIKE ?")
        params.append(f"%{name}%")
    if course:
        clauses.append("course LIKE ?")
        params.append(f"%{course}%")
    if email:
        clauses.append("email = ?")
        params.append(email.lower())
    if born_after:
        clauses.append("date_of_birth > ?")
        params.append(born_after.isoformat())
    if born_before:
        clauses.append("date_of_birth < ?")
        params.append(born_before.isoformat())
    sql = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    return sql, params


def create_student(conn: sqlite3.Connection, data: dict) -> dict:
    data = _serialise(data)
    placeholders = ", ".join("?" for _ in COLUMNS)
    cur = conn.execute(
        f"INSERT INTO students ({', '.join(COLUMNS)}) VALUES ({placeholders})",
        [data.get(c) for c in COLUMNS],
    )
    conn.commit()
    return get_student(conn, cur.lastrowid)


def get_student(conn: sqlite3.Connection, student_id: int) -> Optional[dict]:
    row = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    return dict(row) if row else None


def list_students(conn: sqlite3.Connection, skip: int = 0, limit: int = 100, **filters) -> list[dict]:
    where, params = _where(**filters)
    rows = conn.execute(
        f"SELECT * FROM students{where} ORDER BY id LIMIT ? OFFSET ?",
        [*params, limit, skip],
    ).fetchall()
    return [dict(r) for r in rows]


def count_students(conn: sqlite3.Connection, **filters) -> int:
    where, params = _where(**filters)
    return conn.execute(f"SELECT COUNT(*) FROM students{where}", params).fetchone()[0]


def update_student(conn: sqlite3.Connection, student_id: int, data: dict[str, Any]) -> Optional[dict]:
    data = {k: v for k, v in _serialise(data).items() if k in COLUMNS}
    if not data:
        return get_student(conn, student_id)
    sets = ", ".join(f"{k} = ?" for k in data)
    cur = conn.execute(f"UPDATE students SET {sets} WHERE id = ?", [*data.values(), student_id])
    conn.commit()
    return get_student(conn, student_id) if cur.rowcount else None


def delete_student(conn: sqlite3.Connection, student_id: int) -> bool:
    cur = conn.execute("DELETE FROM students WHERE id = ?", (student_id,))
    conn.commit()
    return cur.rowcount > 0


def distinct_courses(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute("SELECT DISTINCT course FROM students WHERE course IS NOT NULL").fetchall()
    return [r[0] for r in rows]
