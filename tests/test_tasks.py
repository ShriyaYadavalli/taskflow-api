
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app


@pytest.fixture
def client(tmp_path):
    # Give each test its own temporary database.
    database_url = f"sqlite:///{tmp_path / 'test.db'}"

    test_engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
    )

    TestingSessionLocal = sessionmaker(
        bind=test_engine,
        autoflush=False,
        autocommit=False,
    )

    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    test_engine.dispose()


def test_create_and_list_tasks(client):
    response = client.post(
        "/tasks",
        json={
            "title": "Learn automated testing",
            "priority": "high",
        },
    )

    assert response.status_code == 201
    assert response.json()["title"] == "Learn automated testing"

    task_id = response.json()["id"]

    list_response = client.get("/tasks")

    assert list_response.status_code == 200
    assert any(task["id"] == task_id for task in list_response.json())


def test_invalid_priority_is_rejected(client):
    response = client.post(
        "/tasks",
        json={
            "title": "Invalid task",
            "priority": "urgent",
        },
    )

    assert response.status_code == 422


def test_filtering_and_pagination(client):
    for title, priority in [
        ("Task A", "high"),
        ("Task B", "low"),
        ("Task C", "high"),
    ]:
        response = client.post(
            "/tasks",
            json={"title": title, "priority": priority},
        )
        assert response.status_code == 201

    filtered = client.get("/tasks?priority=high")

    assert filtered.status_code == 200
    assert len(filtered.json()) == 2
    assert all(task["priority"] == "high" for task in filtered.json())

    page = client.get("/tasks?limit=1&offset=1")

    assert page.status_code == 200
    assert len(page.json()) == 1


def test_project_and_its_tasks(client):
    project_response = client.post(
        "/projects",
        json={
            "name": "Backend Portfolio",
            "description": "Build backend projects",
        },
    )

    assert project_response.status_code == 201
    project_id = project_response.json()["id"]

    task_response = client.post(
        "/tasks",
        json={
            "title": "Build TaskFlow",
            "project_id": project_id,
        },
    )

    assert task_response.status_code == 201
    assert task_response.json()["project_id"] == project_id

    response = client.get(f"/projects/{project_id}/tasks")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["title"] == "Build TaskFlow"


def test_missing_task_returns_404(client):
    response = client.get("/tasks/999999")

    assert response.status_code == 404
