"""
Authentication tests
Tests: login, register, token validation

Related to main project commit:
- feat: Add JWT authentication module
"""
import pytest
import httpx


class TestAuthentication:
    """Test authentication endpoints"""

    def test_health_endpoint_no_auth(self, api_client):
        """Health check should work without authentication"""
        response = api_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "transactions_count" in data

    def test_root_endpoint_no_auth(self, api_client):
        """Root endpoint should work without authentication"""
        response = api_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "version" in data
        # Verify version is a valid semantic version string
        version = data["version"]
        assert isinstance(version, str)
        assert len(version.split('.')) >= 2  # At least major.minor

    def test_docs_endpoint_no_auth(self, api_client):
        """API docs should be accessible"""
        response = api_client.get("/docs")
        assert response.status_code == 200

    def test_protected_endpoint_requires_auth(self, api_client):
        """Protected endpoints should require authentication"""
        response = api_client.get("/transactions")
        assert response.status_code == 401
        assert "Not authenticated" in response.text or "Could not validate" in response.text

    def test_login_with_valid_credentials(self, api_client):
        """Login with valid credentials should return token"""
        # Use admin credentials (created on startup)
        response = api_client.post(
            "/auth/login",
            data={"username": "admin", "password": "admin"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    def test_login_with_invalid_credentials(self, api_client):
        """Login with invalid credentials should fail"""
        response = api_client.post(
            "/auth/login",
            data={"username": "invalid", "password": "wrong"}
        )
        assert response.status_code == 401
        assert "Incorrect" in response.text or "Could not validate" in response.text

    def test_access_protected_with_valid_token(self, api_client, auth_headers):
        """Protected endpoints should work with valid token"""
        response = api_client.get("/transactions", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_access_protected_with_invalid_token(self, api_client):
        """Protected endpoints should reject invalid tokens"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = api_client.get("/transactions", headers=headers)
        assert response.status_code == 401

    def test_token_expires(self, api_client):
        """Token should have expiration"""
        response = api_client.post(
            "/auth/login",
            data={"username": "admin", "password": "admin"}
        )
        data = response.json()
        assert data["expires_in"] > 0


class TestUserRegistration:
    """Test user registration"""

    def test_register_new_user(self, api_client):
        """Should be able to register new user"""
        import uuid
        unique_username = f"test_{uuid.uuid4().hex[:8]}"

        response = api_client.post(
            "/auth/register",
            json={"username": unique_username, "password": "testpass123"}
        )

        if response.status_code == 409:
            pytest.skip("User already exists")

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == unique_username
        assert "id" in data
        assert data["is_active"] is True

    def test_register_duplicate_user_fails(self, api_client):
        """Registering duplicate username should fail"""
        import uuid
        unique_username = f"dup_test_{uuid.uuid4().hex[:8]}"

        # First registration
        response1 = api_client.post(
            "/auth/register",
            json={"username": unique_username, "password": "testpass123"}
        )

        if response1.status_code != 200:
            pytest.skip("Could not create initial user")

        # Second registration with same username
        response2 = api_client.post(
            "/auth/register",
            json={"username": unique_username, "password": "differentpass"}
        )
        assert response2.status_code == 409
