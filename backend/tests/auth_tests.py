# Authentication tests
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..main import app
from ..database import Base, get_db
from ..auth import auth_manager
from ..config import settings

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


class TestAuth:
    def test_login_success(self):
        response = client.post(
            "/api/auth/login",
            json={
                "username": settings.admin_username,
                "password": settings.admin_password,
            },
        )
        assert response.status_code == 200
        assert "csrf_token" in response.json()
        assert "session_token" in response.cookies

    def test_login_invalid_credentials(self):
        response = client.post(
            "/api/auth/login", json={"username": "wrong", "password": "wrong"}
        )
        assert response.status_code == 401

    def test_rate_limiting(self):
        # Make 6 requests rapidly
        for i in range(6):
            response = client.post(
                "/api/auth/login", json={"username": "test", "password": "wrong"}
            )
            if i < 5:
                assert response.status_code == 401
            else:
                assert response.status_code == 429

    def test_logout(self):
        # Login first
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": settings.admin_username,
                "password": settings.admin_password,
            },
        )

        # Logout
        response = client.post("/api/auth/logout", cookies=login_response.cookies)
        assert response.status_code == 200

    def test_protected_endpoint(self):
        # Without auth
        response = client.get("/api/settings")
        assert response.status_code == 401

        # With auth
        login_response = client.post(
            "/api/auth/login",
            json={
                "username": settings.admin_username,
                "password": settings.admin_password,
            },
        )

        response = client.get("/api/settings", cookies=login_response.cookies)
        assert response.status_code == 200
