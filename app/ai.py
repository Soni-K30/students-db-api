"""Optional bonus: answer natural-language questions with a local Ollama model.

Safety design:
  * The model NEVER writes or runs SQL.
  * Backend code decides which records are relevant (fixed, parameterised
    queries through app.crud) and passes them to the model as context.
  * The model is told to answer only from that context.
"""
import os
import re
import sqlite3
from datetime import date

import httpx

from . import crud

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")
MAX_CONTEXT_RECORDS = 50

SYSTEM_PROMPT = (
    "You are an assistant for a student records system. Answer the question using ONLY the "
    "FACTS and RECORDS provided. Do not invent students or numbers. If the answer is not in "
    "the provided data, say you do not have that information. Be concise and clear."
)


class OllamaUnavailable(Exception):
    pass


def retrieve_context(conn: sqlite3.Connection, question: str) -> tuple[dict, list[dict], int, int]:
    """Translate the question into safe filters, then fetch matching records."""
    q = question.lower()
    filters: dict = {}

    m = re.search(r"born\s+(after|before|in)\s+(?:the\s+year\s+)?(\d{4})", q)
    if m:
        kind, year = m.group(1), int(m.group(2))
        if kind == "after":            # born in a year later than `year`
            filters["born_after"] = date(year, 12, 31)
        elif kind == "before":         # born in a year earlier than `year`
            filters["born_before"] = date(year, 1, 1)
        else:                          # born during `year`
            filters["born_after"] = date(year - 1, 12, 31)
            filters["born_before"] = date(year + 1, 1, 1)

    for course in crud.distinct_courses(conn):
        if course.lower() in q:
            filters["course"] = course
            break

    if "course" not in filters and "born_after" not in filters and "born_before" not in filters:
        words = set(re.findall(r"[a-z]{3,}", q))
        for s in crud.list_students(conn, limit=1000):
            tokens = set(re.findall(r"[a-z]{3,}", s["name"].lower()))
            if tokens & words:
                filters["name"] = next(iter(tokens & words))
                break

    total = crud.count_students(conn)
    matching = crud.count_students(conn, **filters)
    records = crud.list_students(conn, limit=MAX_CONTEXT_RECORDS, **filters)
    printable = {k: (v.isoformat() if isinstance(v, date) else v) for k, v in filters.items()}
    return printable, records, total, matching


def build_prompt(question: str, filters: dict, records: list[dict], total: int, matching: int) -> str:
    lines = [
        f"- Today's date: {date.today().isoformat()}",
        f"- Total students in database: {total}",
        f"- Students matching the question's filters {filters or '(none)'}: {matching}",
    ]
    if matching > len(records):
        lines.append(f"- Only the first {len(records)} matching records are listed below.")
    rec_lines = [
        f"id={r['id']} | name={r['name']} | dob={r['date_of_birth']} | email={r['email']} | "
        f"phone={r['phone']} | course={r['course']} | enrolled={r['enrollment_date']}"
        for r in records
    ] or ["(no matching records)"]
    return "FACTS:\n" + "\n".join(lines) + "\n\nRECORDS:\n" + "\n".join(rec_lines) + f"\n\nQUESTION: {question}"


def ask_ollama(prompt: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "options": {"temperature": 0},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    }
    try:
        resp = httpx.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=120)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise OllamaUnavailable(str(exc)) from exc
    return resp.json()["message"]["content"].strip()


def answer_question(conn: sqlite3.Connection, question: str) -> dict:
    filters, records, total, matching = retrieve_context(conn, question)
    answer = ask_ollama(build_prompt(question, filters, records, total, matching))
    return {
        "question": question,
        "answer": answer,
        "model": OLLAMA_MODEL,
        "filters_applied": filters,
        "records_used": len(records),
    }
