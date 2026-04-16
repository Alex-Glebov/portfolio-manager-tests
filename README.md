# Portfolio Manager Tests

Test suite for Portfolio Manager API.

## Structure

```
portfolio-manager-tests/
├── tests/
│   ├── test_transactions.py    # Transaction CRUD tests
│   ├── test_auth.py            # Authentication tests
│   ├── test_holdings.py        # Portfolio calculations
│   ├── test_export.py          # CSV export tests
│   └── conftest.py             # Pytest fixtures
├── test_data/
│   └── sample_transactions.csv # Test data
├── requirements.txt            # Test dependencies
└── README.md                   # This file
```

## Setup

```bash
cd portfolio-manager-tests
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running Tests

Make sure the main API is running first:

```bash
cd ../portfolio-manager
source venv/bin/activate
python main.py
```

Then in another terminal:

```bash
cd portfolio-manager-tests
source venv/bin/activate
pytest -v
```

## Test Coverage

- Authentication (login, register, token validation)
- Transactions (create, read, update, delete)
- Holdings calculation
- Portfolio summary
- CSV export
- Error handling

## Commit References

Test commits reference corresponding commits in the main project:

- Test commit `tests: Add transaction CRUD` → references main `feat: Portfolio manager API`

## License

MIT License
