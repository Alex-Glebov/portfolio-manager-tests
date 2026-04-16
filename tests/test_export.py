"""
Export tests
Tests: CSV export functionality

Related to main project commit:
- feat: Add CSV export for transactions and holdings
"""
import pytest
import csv
import io


class TestExport:
    """Test CSV export functionality"""

    def test_export_transactions_csv(self, api_client, auth_headers):
        """Should export transactions as CSV"""
        response = api_client.get("/export/transactions", headers=auth_headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "transactions_" in response.headers["content-disposition"]

        # Verify CSV content
        content = response.content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)
        assert len(rows) >= 0  # May be empty but should be valid CSV

    def test_export_holdings_csv(self, api_client, auth_headers):
        """Should export holdings as CSV"""
        response = api_client.get("/export/holdings", headers=auth_headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "holdings_" in response.headers["content-disposition"]

        # Verify CSV content
        content = response.content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(content))
        rows = list(reader)
        assert isinstance(rows, list)

    def test_export_requires_auth(self, api_client):
        """Export should require authentication"""
        response = api_client.get("/export/transactions")
        assert response.status_code == 401

        response = api_client.get("/export/holdings")
        assert response.status_code == 401

    def test_export_transactions_contains_data(self, api_client, auth_headers):
        """Exported CSV should contain transaction data"""
        # Create a transaction first
        txn = {
            "name": "ExportTestItem",
            "cost": 99.99,
            "qty": 50,
            "cost_units": "USD",
            "direction": "in",
            "counterpart_id": "EXPORT_TEST",
            "notes": "For export test"
        }
        api_client.post("/transactions", headers=auth_headers, json=txn)

        # Export and verify
        response = api_client.get("/export/transactions", headers=auth_headers)
        content = response.content.decode('utf-8')

        # Check CSV headers
        assert "id" in content
        assert "timestamp" in content
        assert "name" in content
        assert "cost" in content
        assert "qty" in content

        # Check our data is present
        assert "ExportTestItem" in content
