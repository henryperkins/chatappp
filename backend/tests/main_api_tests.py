# Main API tests
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..main import app
from ..database import Base, get_db
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


class TestMainAPI:

    @pytest.fixture
    def auth_cookies(self):
        response = client.post(
            "/api/auth/login",
            json={
                "username": settings.admin_username,
                "password": settings.admin_password,
            },
        )
        return response.cookies

    def test_health_check(self):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_get_chat_history(self, auth_cookies):
        response = client.get("/api/chat/history", cookies=auth_cookies)
        assert response.status_code == 200
        assert "messages" in response.json()
        assert "total" in response.json()

    def test_get_chat_history_with_search(self, auth_cookies):
        response = client.get("/api/chat/history?search=test", cookies=auth_cookies)
        assert response.status_code == 200

    def test_clear_chat_history(self, auth_cookies):
        response = client.delete("/api/chat/history", cookies=auth_cookies)
        assert response.status_code == 200
        assert response.json() == {"status": "success"}

    def test_get_settings(self, auth_cookies):
        response = client.get("/api/settings", cookies=auth_cookies)
        assert response.status_code == 200
        data = response.json()
        assert "model" in data
        assert "max_tokens" in data
        assert "temperature" in data
        assert "provider" in data

    def test_update_settings(self, auth_cookies):
        response = client.post(
            "/api/settings",
            json={"model": "gpt-4o", "max_tokens": 1024, "temperature": 0.5},
            cookies=auth_cookies,
        )
        assert response.status_code == 200
        assert response.json() == {"status": "success"}

    def test_update_settings_validation(self, auth_cookies):
        # Invalid model
        response = client.post(
            "/api/settings", json={"model": "invalid-model"}, cookies=auth_cookies
        )
        assert response.status_code == 422

        # Invalid temperature
        response = client.post(
            "/api/settings", json={"temperature": 3.0}, cookies=auth_cookies
        )
        assert response.status_code == 422

        # Invalid max_tokens
        response = client.post(
            "/api/settings", json={"max_tokens": 10000}, cookies=auth_cookies
        )
        assert response.status_code == 422
