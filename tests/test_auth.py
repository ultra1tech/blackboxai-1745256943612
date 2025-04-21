import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_register_and_login():
    # Test user registration
    response = client.post("/register", json={
        "email": "testuser@example.com",
        "password": "testpassword",
        "is_seller": False
    })
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testuser@example.com"
    assert data["is_seller"] == False
    assert "id" in data

    # Test login
    response = client.post("/token", data={
        "username": "testuser@example.com",
        "password": "testpassword"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Test get current user
    token = data["access_token"]
    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testuser@example.com"
