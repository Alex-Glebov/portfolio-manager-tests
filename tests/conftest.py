"""
Pytest configuration and fixtures for Portfolio Manager tests
"""
import os
import sys
import pytest
import httpx

# Add parent project to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../portfolio-manager'))


# =============================================================================
# Pytest CLI Arguments
# =============================================================================

def pytest_addoption(parser):
    """Add CLI options for test configuration"""
    parser.addoption(
        '--host',
        action='store',
        default=os.getenv('API_HOST', 'localhost'),
        help='API server host (default: localhost or API_HOST env var)'
    )
    parser.addoption(
        '--port',
        action='store',
        default=os.getenv('API_PORT', '8000'),
        help='API server port (default: 8000 or API_PORT env var)'
    )
    parser.addoption(
        '--api-url',
        action='store',
        default=os.getenv('API_BASE_URL', None),
        help='Full API base URL (overrides --host and --port)'
    )
    parser.addoption(
        '--username',
        action='store',
        default=os.getenv('TEST_USERNAME', 'testuser'),
        help='Test username (default: testuser or TEST_USERNAME env var)'
    )
    parser.addoption(
        '--password',
        action='store',
        default=os.getenv('TEST_PASSWORD', 'testpass123'),
        help='Test password (default: testpass123 or TEST_PASSWORD env var)'
    )


@pytest.fixture(scope="session")
def cli_host(request):
    """Get host from CLI or env"""
    return request.config.getoption('--host')


@pytest.fixture(scope="session")
def cli_port(request):
    """Get port from CLI or env"""
    return request.config.getoption('--port')


@pytest.fixture(scope="session")
def cli_api_url(request):
    """Get full API URL from CLI or env"""
    return request.config.getoption('--api-url')


@pytest.fixture(scope="session")
def cli_username(request):
    """Get username from CLI or env"""
    return request.config.getoption('--username')


@pytest.fixture(scope="session")
def cli_password(request):
    """Get password from CLI or env"""
    return request.config.getoption('--password')


# =============================================================================
# API Configuration (uses CLI args with env fallbacks)
# =============================================================================

def get_base_url(cli_api_url, cli_host, cli_port):
    """Construct base URL from CLI args or env"""
    if cli_api_url:
        return cli_api_url
    return f"http://{cli_host}:{cli_port}"


# Legacy env var support (for backward compatibility)
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
TEST_USERNAME = os.getenv("TEST_USERNAME", "testuser")
TEST_PASSWORD = os.getenv("TEST_PASSWORD", "testpass123")


@pytest.fixture(scope="session")
def api_client(cli_api_url, cli_host, cli_port):
    """Create HTTPX client for API tests"""
    base_url = get_base_url(cli_api_url, cli_host, cli_port)
    print(f"\n>>> Testing against API: {base_url}")
    with httpx.Client(base_url=base_url, timeout=30.0) as client:
        yield client


@pytest.fixture(scope="session")
def base_url(cli_api_url, cli_host, cli_port):
    """Return API base URL"""
    return get_base_url(cli_api_url, cli_host, cli_port)


@pytest.fixture(scope="session")
def test_username(cli_username):
    """Return test username"""
    return cli_username


@pytest.fixture(scope="session")
def test_password(cli_password):
    """Return test password"""
    return cli_password


@pytest.fixture(scope="session")
def auth_token(api_client, test_username, test_password):
    """Get JWT token for authenticated requests"""
    # Try to register first
    try:
        register_response = api_client.post(
            "/auth/register",
            json={"username": test_username, "password": test_password}
        )
        if register_response.status_code == 409:
            print(f"User {test_username} already exists")
    except Exception as e:
        print(f"Registration attempt: {e}")

    # Login to get token
    login_response = api_client.post(
        "/auth/login",
        data={"username": test_username, "password": test_password}
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
