# Portfolio Manager Tests

Test suite for Portfolio Manager API.

## Version Compatibility

**Current Test Suite Version:** `0.2.0`

**Compatible API Versions:** `0.1.0` - `0.3.0`

This test suite validates the Portfolio Manager API functionality. Ensure you're running a compatible API version before testing.

## Structure

```
portfolio-manager-tests/
├── tests/
│   ├── test_version.py         # Version compatibility tests
│   ├── test_portfolios.py      # Multi-portfolio feature tests
│   ├── test_transactions.py    # Transaction CRUD tests
│   ├── test_auth.py            # Authentication tests (JWT, login, register)
│   ├── test_holdings.py        # Portfolio calculations
│   ├── test_export.py          # CSV export tests
│   └── conftest.py             # Pytest fixtures and configuration
├── requirements.txt            # Test dependencies
└── README.md                   # This file
```

## Setup

### 1. Create Virtual Environment

```bash
cd portfolio-manager-tests
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Test Environment

Tests can be configured via **CLI arguments** (recommended) or environment variables:

#### CLI Arguments (New in v0.1.1)

| Argument | Description | Default |
|----------|-------------|---------|
| `--host` | API server host | `localhost` |
| `--port` | API server port | `8000` |
| `--api-url` | Full API base URL (overrides host/port) | (none) |
| `--username` | Test user username | `testuser` |
| `--password` | Test user password | `testpass123` |

**Examples:**
```bash
# Test against remote server
pytest -v --host 192.168.1.100 --port 8080

# Test with full URL
pytest -v --api-url http://myserver:9000

# Custom credentials
pytest -v --username admin --password secret123
```

**Priority:** CLI args > Environment variables > Defaults

#### Environment Variables (Legacy)

| Variable | Description | Default |
|----------|-------------|---------|
| `API_BASE_URL` | API endpoint URL | `http://localhost:8000` |
| `API_HOST` | API server host (if --host not set) | `localhost` |
| `API_PORT` | API server port (if --port not set) | `8000` |
| `TEST_USERNAME` | Test user username | `testuser` |
| `TEST_PASSWORD` | Test user password | `testpass123` |

### 3. Start the API Server

Make sure the main API is running first:

```bash
cd ../portfolio-manager
source venv/bin/activate
python main.py
```

Or with custom configuration:
```bash
PORTFOLIO_MANAGER_PORT=8000 python main.py
```

### 4. Run Tests

```bash
cd portfolio-manager-tests
source venv/bin/activate

# Run all tests
pytest -v

# Run specific test file
pytest tests/test_auth.py -v

# Run specific test
pytest tests/test_auth.py::TestAuthentication::test_login_with_valid_credentials -v

# Run with coverage
pytest -v --cov=.
```

## Test Coverage

### Version Compatibility (`test_version.py`)
- ✅ Server version is 0.2.0 or higher
- ✅ Version follows semantic versioning format
- ✅ Health endpoint returns version info
- ✅ Version fixture skips incompatible tests

### Multi-Portfolio (`test_portfolios.py`) - Requires v0.2.0+
- ✅ Multi-portfolio feature available (v0.2.0+)
- ✅ X-Portfolio header accepted
- ✅ Default portfolio access (no header)
- ✅ Empty portfolio header works
- ✅ Portfolio data isolation
- ✅ Holdings isolation per portfolio
- ✅ User can access own portfolio
- ✅ Admin can access all portfolios
- ✅ Transaction CRUD in portfolios
- ✅ Portfolio-specific exports
- ✅ Portfolio summary isolation

### Authentication (`test_auth.py`)
- ✅ Health endpoint (no auth required)
- ✅ Root endpoint (no auth required)
- ✅ Protected endpoints require authentication
- ✅ Login with valid credentials
- ✅ Login with invalid credentials (rejected)
- ✅ Access protected with valid token
- ✅ Access protected with invalid token (rejected)
- ✅ Token expiration handling
- ✅ User registration (new user)
- ✅ Duplicate user registration (rejected)

### Transactions (`test_transactions.py`)
- ✅ Create transaction (incoming)
- ✅ Create transaction (outgoing)
- ✅ Calculate total_value automatically
- ✅ Protected endpoint requires auth
- ✅ Get all transactions
- ✅ Pagination support
- ✅ Get transaction by ID
- ✅ Get non-existent transaction (404)
- ✅ Filter by name
- ✅ Filter by direction
- ✅ Update transaction
- ✅ Update non-existent transaction (404)
- ✅ Update with no changes
- ✅ Delete transaction
- ✅ Delete non-existent transaction (404)

### Holdings (`test_holdings.py`)
- ✅ Get holdings list
- ✅ Holdings calculation (in/out/balance)
- ✅ Get specific holding
- ✅ Get non-existent holding (404)
- ✅ Portfolio summary endpoint
- ✅ Portfolio summary calculations
- ✅ Counterpart history tracking

### Export (`test_export.py`)
- ✅ Export transactions to CSV
- ✅ Export holdings to CSV
- ✅ Export requires authentication
- ✅ Exported CSV contains data

## Test Configuration

### conftest.py

The `conftest.py` file provides:
- `api_client` - HTTPX client for API requests
- `base_url` - API base URL from env or default
- `auth_token` - JWT token for authenticated requests
- `auth_headers` - Headers with Bearer token
- `sample_transaction` - Sample transaction data fixture

### Adding New Tests

Example test structure:
```python
def test_my_feature(api_client, auth_headers):
    """Test description"""
    response = api_client.get(
        "/my-endpoint",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "expected_field" in data
```

## Expected API Behavior

### HTTP Status Codes
- `200` - Success
- `201` - Created
- `204` - No content (deleted)
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (inactive user)
- `404` - Not found
- `409` - Conflict (duplicate user)
- `422` - Validation error (invalid data)

### Authentication Flow
1. Register user (if not exists) - `POST /auth/register`
2. Login - `POST /auth/login`
3. Use token in `Authorization: Bearer <token>` header
4. Token expires after 30 minutes (configurable)

## Troubleshooting

### Connection Refused
- Ensure API server is running
- Check `API_BASE_URL` matches server port
- Default: `http://localhost:8000`

### Authentication Failures
- Check that default admin user exists
- Default credentials: `admin` / `admin`
- Or register a test user first

### Version Mismatch
- Tests expect API version in compatible range
- Check `__min_version__` and `__max_version__` in API
- Update tests if API version changed significantly
- **v0.2.0+ required for multi-portfolio tests** - Use `--ignore=tests/test_portfolios.py` to skip

## Version-Specific Testing

### Skip Multi-Portfolio Tests (v0.1.x API)
```bash
# Run only tests compatible with v0.1.x
pytest -v --ignore=tests/test_portfolios.py --ignore=tests/test_version.py
```

### Run All Tests (v0.2.0+ API)
```bash
# Verify version first, then run all tests
pytest tests/test_version.py -v  # Checks v0.2.0+
pytest -v  # Run all tests
```

## Continuous Integration

Example GitHub Actions workflow:
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Start API (in background)
        run: |
          cd ../portfolio-manager
          pip install -r requirements.txt
          python main.py &
          sleep 5
      - name: Run tests
        run: pytest -v
```

## Contributing

When adding new tests:
1. Follow existing test structure
2. Use fixtures from `conftest.py`
3. Test both success and failure cases
4. Update this README with new coverage

## License

MIT License

## See Also

- [Portfolio Manager API](https://github.com/Alex-Glebov/portfolio-manager) - The main application
- API Documentation: `http://localhost:8000/docs` (when running)
