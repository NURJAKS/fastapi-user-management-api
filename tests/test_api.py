"""API Integration and Unit tests for FastAPI User Management."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from fastapi.testclient import TestClient
from api.app import app
from db.database import engine, Base, SessionLocal
from models.user import User
from models.group import Group
from models.student import Student

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    session.query(Student).delete()
    session.query(Group).delete()
    session.query(User).delete()
    session.commit()
    yield
    session.close()


def test_register_user_success():
    resp = client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "Password123!"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "test@example.com"
    assert "id" in data


def test_register_duplicate_email_fails():
    client.post("/auth/register", json={
        "email": "dup@example.com",
        "password": "Password123!"
    })
    resp = client.post("/auth/register", json={
        "email": "dup@example.com",
        "password": "Password123!"
    })
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"]


def test_student_crud_flow():
    session = SessionLocal()
    group = Group(name="SE-24")
    session.add(group)
    session.commit()
    group_id = group.id
    session.close()

    # Create student
    create_resp = client.post("/students", json={
        "name": "Alex",
        "age": 21,
        "group_id": group_id
    })
    assert create_resp.status_code == 201
    student = create_resp.json()
    student_id = student["id"]
    assert student["name"] == "Alex"

    # Read student
    read_resp = client.get(f"/students/{student_id}")
    assert read_resp.status_code == 200
    assert read_resp.json()["name"] == "Alex"

    # List students
    list_resp = client.get("/students")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1
