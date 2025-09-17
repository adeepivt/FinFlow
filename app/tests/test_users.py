import pytest
from app.tests.conftest import client


class TestUserRegistration:
    """Test user registration functionality."""
    
    def test_register_user_success(self):
        user_data = {
            "email": "newuser@example.com",
            "full_name": "New User",
            "password": "securepassword123"
        }
        
        response = client.post("/api/v1/users", json=user_data)
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == user_data["email"]
        assert data["full_name"] == user_data["full_name"]
        assert "id" in data
        assert "hashed_password" not in data
        assert "password" not in data
    
    def test_register_duplicate_email(self):
        user_data = {
            "email": "duplicate@example.com",
            "full_name": "First User",
            "password": "password123"
        }
        
        response1 = client.post("/api/v1/users", json=user_data)
        assert response1.status_code == 201
        
        user_data["full_name"] = "Second User"
        response2 = client.post("/api/v1/users", json=user_data)
        assert response2.status_code == 400
        assert "Email already registered" in response2.json()["detail"]
    
    def test_register_invalid_email(self):
        """Test registration with invalid email fails."""
        user_data = {
            "email": "invalid-email",
            "full_name": "Test User",
            "password": "password123"
        }
        
        response = client.post("/api/v1/users", json=user_data)
        assert response.status_code == 422 


class TestUserAuthentication:
    """Test user login and JWT authentication."""
    
    def test_login_success(self, test_user):
        """Test successful login."""
        login_data = {
            "username": test_user.email,
            "password": "testpassword123"
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == test_user.email
    
    def test_login_wrong_password(self, test_user):
        """Test login with wrong password fails."""
        login_data = {
            "username": test_user.email,
            "password": "wrongpassword"
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    def test_login_nonexistent_user(self):
        """Test login with non-existent email fails."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "password123"
        }
        
        response = client.post("/api/v1/auth/login", data=login_data)
        
        assert response.status_code == 401
    
    def test_protected_route_without_token(self, test_user):
        """Test accessing protected route without token fails."""
        response = client.get(f"/api/v1/users/{test_user.id}")
        
        assert response.status_code == 401
    
    def test_protected_route_with_token(self, test_user, auth_headers):
        """Test accessing protected route with valid token succeeds."""
        response = client.get(f"/api/v1/users/{test_user.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user.email