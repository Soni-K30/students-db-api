from app import ai

VALID = {"name": "Test Student", "date_of_birth": "2004-05-17", "email": "test@example.com",
         "phone": "+91 98765 43210", "course": "B.Tech CSE"}


def make(client, **over):
    return client.post("/students", json={**VALID, **over})


def test_create_and_read(client):
    r = make(client)
    assert r.status_code == 201
    sid = r.json()["id"]
    assert client.get(f"/students/{sid}").json()["name"] == "Test Student"
    assert len(client.get("/students").json()) == 1


def test_filtering(client):
    make(client)
    make(client, name="Other Person", email="other@example.com", course="BBA", date_of_birth="2006-02-02")
    assert len(client.get("/students", params={"course": "BBA"}).json()) == 1
    assert len(client.get("/students", params={"name": "test"}).json()) == 1
    assert len(client.get("/students", params={"born_after": "2005-01-01"}).json()) == 1


def test_put_and_patch(client):
    sid = make(client).json()["id"]
    r = client.patch(f"/students/{sid}", json={"course": "BCA"})
    assert r.status_code == 200 and r.json()["course"] == "BCA" and r.json()["name"] == "Test Student"
    r = client.put(f"/students/{sid}", json={**VALID, "name": "Renamed Student"})
    assert r.json()["name"] == "Renamed Student"


def test_delete(client):
    sid = make(client).json()["id"]
    assert client.delete(f"/students/{sid}").status_code == 200
    assert client.get(f"/students/{sid}").status_code == 404


def test_missing_records_404(client):
    assert client.get("/students/999").status_code == 404
    assert client.patch("/students/999", json={"course": "X"}).status_code == 404
    assert client.put("/students/999", json=VALID).status_code == 404
    assert client.delete("/students/999").status_code == 404


def test_validation(client):
    assert make(client, email="not-an-email").status_code == 422
    assert make(client, name="").status_code == 422
    assert make(client, date_of_birth="2999-01-01").status_code == 422
    assert make(client, email=None, phone=None).status_code == 422
    assert make(client, phone="abc").status_code == 422


def test_duplicate_email_409(client):
    make(client)
    assert make(client).status_code == 409


def test_patch_rules(client):
    sid = make(client, phone=None).json()["id"]
    assert client.patch(f"/students/{sid}", json={}).status_code == 400
    assert client.patch(f"/students/{sid}", json={"email": None}).status_code == 422
    assert client.patch(f"/students/{sid}", json={"name": None}).status_code == 422


def test_ai_grounded_context(client, monkeypatch):
    make(client)
    make(client, name="Young Student", email="y@example.com", date_of_birth="2006-03-03")
    captured = {}

    def fake(prompt):
        captured["p"] = prompt
        return "ok"

    monkeypatch.setattr(ai, "ask_ollama", fake)
    r = client.post("/ai/ask", json={"question": "List students born after 2005"})
    assert r.status_code == 200
    assert r.json()["records_used"] == 1
    assert "Young Student" in captured["p"] and "Test Student" not in captured["p"]
    r = client.post("/ai/ask", json={"question": "How many students are there?"})
    assert "Total students in database: 2" in captured["p"]


def test_ai_ollama_down(client, monkeypatch):
    monkeypatch.setattr(ai, "OLLAMA_URL", "http://localhost:1")
    assert client.post("/ai/ask", json={"question": "How many students?"}).status_code == 503
