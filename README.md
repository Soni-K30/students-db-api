# Students Database CRUD Application

**EWB Edu Tech – Python Backend Development Internship Project**

A backend application that manages student records with full **Create, Read, Update, Delete (CRUD)** operations, built with **Python, FastAPI and SQLite**. Includes the optional **local AI bonus** (Ollama) that answers natural-language questions grounded in the stored records.

## Features

- Create, list/filter, view, update (PUT + PATCH) and delete students
- SQLite persistence (data survives restarts, stored in `students.db`)
- Input validation (names, email format, phone format, date of birth not in the future, at least one contact method)
- Proper error handling: `404` missing record, `409` duplicate email, `422` invalid input
- Interactive API docs at `/docs` (Swagger UI)
- Automated tests (`pytest`)
- Optional: `/ai/ask` endpoint using a local Ollama model (no unrestricted SQL)

## Project structure

```
students-db-api/
├── app/
│   ├── main.py       # FastAPI routes
│   ├── database.py   # SQLite connection + table creation
│   ├── crud.py       # Parameterised database operations
│   ├── schemas.py    # Pydantic models / validation
│   ├── ai.py         # Optional Ollama integration
│   └── seed.py       # Loads DUMMY sample data
├── tests/            # pytest test suite
├── requirements.txt
├── .env.example
└── README.md
```

## Student record fields

| Field | Required | Notes |
|---|---|---|
| `id` | auto | Unique student ID (auto-generated) |
| `name` | yes | 2–100 characters |
| `date_of_birth` | yes | `YYYY-MM-DD`, not in the future |
| `email` | one of email/phone | Valid email, unique |
| `phone` | one of email/phone | 7–15 digits, optional leading `+`, spaces/hyphens allowed |
| `course` | optional | |
| `address` | optional | |
| `enrollment_date` | optional | `YYYY-MM-DD` |

## Prerequisites

- Python 3.10 or newer
- `pip`
- (Optional, for AI bonus) [Ollama](https://ollama.com)

## Installation

```bash
git clone <your-repo-url>
cd students-db-api

python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

## Run the application

```bash
uvicorn app.main:app --reload
```

- API: http://127.0.0.1:8000
- Interactive docs: http://127.0.0.1:8000/docs

The SQLite database file (`students.db`) is created automatically on first start.

### Load dummy sample data (optional)

```bash
python -m app.seed
```

All sample data is fictional (`@example.com` emails). No real student information is used.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/students` | Create a student |
| GET | `/students` | List / filter students |
| GET | `/students/{student_id}` | View a student |
| PUT | `/students/{student_id}` | Replace all details |
| PATCH | `/students/{student_id}` | Update only the given fields |
| DELETE | `/students/{student_id}` | Delete a student |
| POST | `/ai/ask` | (Optional) Ask a question about the data via Ollama |

**Filters for `GET /students`:** `name` (partial), `course` (partial), `email` (exact), `born_after`, `born_before` (strict, `YYYY-MM-DD`), `skip`, `limit`.

## Testing the API

### Option 1: Swagger UI
Open http://127.0.0.1:8000/docs, expand an endpoint, click **Try it out**.

### Option 2: curl

```bash
# Create
curl -X POST http://127.0.0.1:8000/students \
  -H "Content-Type: application/json" \
  -d '{"name":"Aarav Sharma","date_of_birth":"2004-05-17","email":"aarav@example.com","phone":"+91 98765 43210","course":"B.Tech CSE","enrollment_date":"2022-08-01"}'

# List all
curl http://127.0.0.1:8000/students

# Filter
curl "http://127.0.0.1:8000/students?course=CSE&born_after=2004-01-01"

# View one
curl http://127.0.0.1:8000/students/1

# Partial update
curl -X PATCH http://127.0.0.1:8000/students/1 \
  -H "Content-Type: application/json" -d '{"course":"B.Tech AI"}'

# Full update
curl -X PUT http://127.0.0.1:8000/students/1 \
  -H "Content-Type: application/json" \
  -d '{"name":"Aarav Sharma","date_of_birth":"2004-05-17","email":"aarav@example.com","course":"B.Tech CSE"}'

# Delete
curl -X DELETE http://127.0.0.1:8000/students/1
```

### Option 3: automated tests

```bash
python -m pytest -q
```

Tests use a temporary database, so your real `students.db` is never touched.

### Expected error responses

| Situation | Status |
|---|---|
| Student id does not exist | `404` |
| Email already used by another student | `409` |
| Invalid email / phone / name / future DOB / no contact info | `422` |
| PATCH with an empty body | `400` |

## Optional bonus: local AI with Ollama

1. Install Ollama and pull a small model:
   ```bash
   ollama pull llama3.2:1b
   ollama serve        # skip if Ollama is already running
   ```
2. Start the API and ask questions:
   ```bash
   curl -X POST http://127.0.0.1:8000/ai/ask \
     -H "Content-Type: application/json" \
     -d '{"question":"How many students are there?"}'

   curl -X POST http://127.0.0.1:8000/ai/ask \
     -H "Content-Type: application/json" \
     -d '{"question":"List students born after 2005"}'
   ```

**How it works (grounded answers):**
1. Backend code reads the question and picks safe filters (birth year, course, name) using fixed, parameterised queries.
2. It fetches the matching records plus the total/matching counts from SQLite.
3. These are given to the model as context, with an instruction to answer *only* from that data.
4. The response includes `filters_applied` and `records_used` so you can verify what the model saw.

**Security:** the model never writes or executes SQL. Use dummy data only.
"born after 2005" is interpreted as born in a year later than 2005 (from 2006-01-01).

If Ollama is not running, `/ai/ask` returns `503` with instructions; the CRUD endpoints are unaffected.

Configuration (optional environment variables, see `.env.example`): `DATABASE_PATH`, `OLLAMA_URL`, `OLLAMA_MODEL`.

## Architecture summary

- **Routes (`main.py`)** receive requests, validate them with Pydantic, and call `crud.py`.
- **CRUD layer (`crud.py`)** runs parameterised SQL against SQLite.
- **Create:** `POST` validates → `INSERT` → returns the new record (`201`).
- **Update:** `PUT` replaces all fields; `PATCH` merges only provided fields, then `UPDATE`.
- **Delete:** `DELETE` removes the row, or returns `404` if it does not exist.

## Submission notes

- No passwords, secrets, or real student data are committed (`.gitignore` excludes `.env` and `*.db`).
