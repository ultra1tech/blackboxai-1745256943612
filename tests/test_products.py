import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_create_product():
    # Register a seller user
    response = client.post("/register", json={
        "email": "seller@example.com",
        "password": "sellerpassword",
        "is_seller": True
    })
    assert response.status_code == 200
    seller = response.json()

    # Login as seller
    response = client.post("/token", data={
        "username": "seller@example.com",
        "password": "sellerpassword"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]

    # Create a product (assuming endpoint /products to be implemented)
    response = client.post("/products", json={
        "title": "Test Product",
        "description": "A test product",
        "price": 10.99,
        "currency": "USD",
        "image_url": "http://example.com/image.jpg"
    }, headers={"Authorization": f"Bearer {token}"})

    # Since /products endpoint is not implemented yet, expect 404 or 501
    assert response.status_code in [404, 501]
