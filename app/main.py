"""Students Database CRUD API (FastAPI + SQLite) with an optional Ollama AI endpoint."""
import sqlite3
from contextlib import asynccontextmanager
from datetime import date
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query

from . import ai, crud
from .database import get_db, init_db
from .schemas import AIAnswer, AIQuestion, StudentCreate, StudentOut, StudentUpdate


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Students Database API",
    description="CRUD backend for student records (FastAPI + SQLite) with an optional local-AI endpoint.",
    version="1.0.0",
    lifespan=lifespan,
)


def _not_found(student_id: int) -> HTTPException:
    return HTTPException(status_code=404, detail=f"Student with id {student_id} not found")


def _duplicate_email() -> HTTPException:
    return HTTPException(status_code=409, detail="A student with this email already exists")


@app.get("/", tags=["Health"])
def root():
    return {"message": "Students Database API is running", "docs": "/docs"}


# ---------- CREATE ----------
@app.post("/students", response_model=StudentOut, status_code=201, tags=["Students"])
def create_student(student: StudentCreate, db: sqlite3.Connection = Depends(get_db)):
    try:
        return crud.create_student(db, student.model_dump())
    except sqlite3.IntegrityError:
        raise _duplicate_email()


# ---------- READ (list / filter) ----------
@app.get("/students", response_model=list[StudentOut], tags=["Students"])
def list_students(
    name: Optional[str] = Query(None, description="Partial, case-insensitive name match"),
    course: Optional[str] = Query(None, description="Partial course match"),
    email: Optional[str] = Query(None, description="Exact email match"),
    born_after: Optional[date] = Query(None, description="date_of_birth strictly after (YYYY-MM-DD)"),
    born_before: Optional[date] = Query(None, description="date_of_birth strictly before (YYYY-MM-DD)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: sqlite3.Connection = Depends(get_db),
):
    return crud.list_students(
        db, skip=skip, limit=limit, name=name, course=course, email=email,
        born_after=born_after, born_before=born_before,
    )


# ---------- READ (single) ----------
@app.get("/students/{student_id}", response_model=StudentOut, tags=["Students"])
def get_student(student_id: int, db: sqlite3.Connection = Depends(get_db)):
    student = crud.get_student(db, student_id)
    if not student:
        raise _not_found(student_id)
    return student


# ---------- UPDATE (full replace) ----------
@app.put("/students/{student_id}", response_model=StudentOut, tags=["Students"])
def replace_student(student_id: int, student: StudentCreate, db: sqlite3.Connection = Depends(get_db)):
    try:
        updated = crud.update_student(db, student_id, student.model_dump())
    except sqlite3.IntegrityError:
        raise _duplicate_email()
    if not updated:
        raise _not_found(student_id)
    return updated


# ---------- UPDATE (partial) ----------
@app.patch("/students/{student_id}", response_model=StudentOut, tags=["Students"])
def update_student(student_id: int, changes: StudentUpdate, db: sqlite3.Connection = Depends(get_db)):
    existing = crud.get_student(db, student_id)
    if not existing:
        raise _not_found(student_id)
    data = changes.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields provided to update")
    merged = {**existing, **{k: (v.isoformat() if isinstance(v, date) else v) for k, v in data.items()}}
    if not merged.get("email") and not merged.get("phone"):
        raise HTTPException(status_code=422, detail="A student must keep at least one contact (email or phone)")
    try:
        return crud.update_student(db, student_id, data)
    except sqlite3.IntegrityError:
        raise _duplicate_email()


# ---------- DELETE ----------
@app.delete("/students/{student_id}", tags=["Students"])
def delete_student(student_id: int, db: sqlite3.Connection = Depends(get_db)):
    if not crud.delete_student(db, student_id):
        raise _not_found(student_id)
    return {"detail": f"Student {student_id} deleted"}


# ---------- OPTIONAL BONUS: local AI (Ollama) ----------
@app.post("/ai/ask", response_model=AIAnswer, tags=["AI (optional)"])
def ask_ai(body: AIQuestion, db: sqlite3.Connection = Depends(get_db)):
    try:
        return ai.answer_question(db, body.question)
    except ai.OllamaUnavailable:
        raise HTTPException(
            status_code=503,
            detail=f"Ollama is not reachable at {ai.OLLAMA_URL}. Start it with 'ollama serve' "
                   f"and pull the model with 'ollama pull {ai.OLLAMA_MODEL}'.",
        )
