import os
import tempfile

import pytest
from fastapi.testclient import TestClient

DB_FILE = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
DB_FILE.close()
os.environ["DATABASE_URL"] = f"sqlite:///{DB_FILE.name}"
os.environ["JWT_SECRET_KEY"] = "test-secret"
os.environ["ADMIN_SETUP_KEY"] = "test-admin-key"

from app.database import Base, engine
from app.main import app

Base.metadata.create_all(bind=engine)
client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_register_and_login():
    registered = client.post("/auth/register", json={
        "name": "Test Viewer",
        "email": "test-viewer@example.com",
        "password": "TestViewer123",
        "role": "admin",
    })
    assert registered.status_code == 201
    assert registered.json()["role"] == "viewer"

    logged_in = client.post("/auth/login", json={
        "email": "test-viewer@example.com",
        "password": "TestViewer123",
    })
    assert logged_in.status_code == 200
    assert "access_token" in logged_in.json()


def test_password_reset_request():
    response = client.post("/auth/password-reset/request", json={
        "email": "test-viewer@example.com"
    })
    assert response.status_code == 200
    assert "token" in response.json()


def test_viewer_cannot_create_dashboard():
    login = client.post("/auth/login", json={
        "email": "test-viewer@example.com",
        "password": "TestViewer123",
    })
    token = login.json()["access_token"]
    response = client.post("/dashboards", json={
        "name": "Restricted Dashboard",
        "description": "Should be rejected",
    }, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
