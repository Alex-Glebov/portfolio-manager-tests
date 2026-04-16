"""
Pytest configuration and fixtures for Portfolio Manager tests
"""
import os
import sys
import pytest
import httpx

# Add parent project to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../portfolio-manager'))

# API Configuration
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
TEST_USERNAME = os.getenv("TEST_USERNAME", "testuser")
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "testpass123")


@pytest.fixture(scope="session")
def api_client():
    """Create HTTPX client for API tests"""
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        yield client


@pytest.fixture(scope="session")
def base_url():
    """Return API base URL"""
    return BASE_URL


@pytest.fixture(scope="session")
def auth_token(api_client):
    """Get JWT token for authenticated requests"""
    # Try to register first
    try:
        register_response = api_client.post(
            "/auth/register",
            json={"username": TEST_USERNAME, "password": TEST_PASSWORD}
        )
        if register_response.status_code == 409:
            print(f"User {TEST_USERNAME} already exists")
    except Exception as e:
        print(f"Registration attempt: {e}")

    # Login to get token
    login_response = api_client.post(
        "/auth/login",
        data={"username": TEST_USERNAME, "password": TEST_PASSWORD}
    )

    if login_response.status_code != 200:
        pytest.fail(f"Could not authenticate: {login_response.text}")

    token_data = login_response.json()
    return token_data["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    """Return headers with authentication token"""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def sample_transaction():
    """Return sample transaction data"""
    return {
        "name": "Test Item",
        "cost": 10.50,
        "qty": 100,
        "cost_units": "USD",
        "direction": "in",
        "counterpart_id": "TEST_SUPPLIER",
        "notes": "Test transaction"
    }


@pytest.fixture(autouse=True)
def log_test_start(request):
    """Log test start"""
    print(f"\n>>> Running test: {request.node.name}")
