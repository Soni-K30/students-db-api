"""Load DUMMY sample data (fictional people, example.com emails). Run: python -m app.seed"""
from . import crud
from .database import get_connection, init_db

SAMPLE = [
    ("Aarav Sharma", "2004-05-17", "aarav.sharma@example.com", "+91 90000 00001", "B.Tech CSE", "2022-08-01"),
    ("Diya Verma", "2005-11-02", "diya.verma@example.com", "+91 90000 00002", "B.Tech ECE", "2023-08-01"),
    ("Rohan Gupta", "2006-01-23", "rohan.gupta@example.com", None, "B.Tech CSE", "2024-08-01"),
    ("Ananya Singh", "2003-09-09", "ananya.singh@example.com", "+91 90000 00004", "BCA", "2021-08-01"),
    ("Kabir Mehta", "2005-03-30", None, "+91 90000 00005", "B.Tech ME", "2023-08-01"),
    ("Isha Patel", "2006-07-14", "isha.patel@example.com", "+91 90000 00006", "BBA", "2024-08-01"),
    ("Vivaan Rao", "2004-12-25", "vivaan.rao@example.com", None, "B.Tech CSE", "2022-08-01"),
    ("Meera Nair", "2007-02-11", "meera.nair@example.com", "+91 90000 00008", "BCA", "2025-08-01"),
]

if __name__ == "__main__":
    init_db()
    conn = get_connection()
    try:
        for name, dob, email, phone, course, enrolled in SAMPLE:
            if email and crud.count_students(conn, email=email):
                continue
            crud.create_student(conn, {"name": name, "date_of_birth": dob, "email": email, "phone": phone,
                                       "course": course, "enrollment_date": enrolled})
        print(f"Seeded. Total students: {crud.count_students(conn)}")
    finally:
        conn.close()
