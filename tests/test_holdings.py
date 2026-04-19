"""
Holdings and Portfolio tests
Tests: Portfolio calculations, holdings summary

Related to main project commit:
- feat: Add portfolio summary and holdings calculation
"""
import pytest


class TestHoldings:
    """Test holdings calculations"""

    def test_get_holdings_returns_list(self, api_client, auth_headers):
        """Should return list of holdings"""
        response = api_client.get("/holdings", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_holdings_requires_auth(self, api_client):
        """Should require authentication"""
        response = api_client.get("/holdings")
        assert response.status_code == 401

    def test_get_specific_holding(self, api_client, auth_headers):
        """Should get holding for specific item"""
        # Get existing balance first (handles CSV persistence)
        response = api_client.get("/holdings/TestSteel", headers=auth_headers)
        initial_balance = 0
        if response.status_code == 200:
            initial_balance = response.json().get("current_balance", 0)

        # Create a transaction
        txn = {
            "name": "TestSteel",
            "cost": 50.0,
            "qty": 100,
            "cost_units": "USD",
            "direction": "in",
            "counterpart_id": "TEST",
            "notes": ""
        }
        api_client.post("/transactions", headers=auth_headers, json=txn)

        # Verify balance increased by 100
        response = api_client.get("/holdings/TestSteel", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "TestSteel"
        assert data["current_balance"] == initial_balance + 100

    def test_get_nonexistent_holding(self, api_client, auth_headers):
        """Should return 404 for nonexistent holding"""
        response = api_client.get("/holdings/NONEXISTENT_ITEM_12345", headers=auth_headers)
        assert response.status_code == 404


class TestPortfolioSummary:
    """Test portfolio summary"""

    def test_get_portfolio_summary(self, api_client, auth_headers):
        """Should return portfolio summary"""
        response = api_client.get("/portfolio/summary", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_transactions" in data
        assert "total_unique_items" in data
        assert "total_value_in_portfolio" in data
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_portfolio_summary_calculations(self, api_client, auth_headers):
        """Summary should reflect actual transactions"""
        # Create some transactions
        for i in range(3):
            txn = {
                "name": f"Item{i}",
                "cost": 10.0 + i,
                "qty": 10,
                "cost_units": "USD",
                "direction": "in",
                "counterpart_id": "TEST",
                "notes": ""
            }
            api_client.post("/transactions", headers=auth_headers, json=txn)

        response = api_client.get("/portfolio/summary", headers=auth_headers)
        data = response.json()

        assert data["total_unique_items"] >= 3
        assert data["total_transactions"] >= 3


class TestCounterpartHistory:
    """Test counterpart history"""

    def test_get_counterpart_history(self, api_client, auth_headers):
        """Should return history for counterpart"""
        # Create transactions with same counterpart
        for _ in range(2):
            txn = {
                "name": "TestItem",
                "cost": 25.0,
                "qty": 10,
                "cost_units": "USD",
                "direction": "in",
                "counterpart_id": "HISTORY_TEST_SUPPLIER",
                "notes": ""
            }
            api_client.post("/transactions", headers=auth_headers, json=txn)

        response = api_client.get(
            "/portfolio/counterpart/HISTORY_TEST_SUPPLIER/history",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["counterpart_id"] == "HISTORY_TEST_SUPPLIER"
        assert "transaction_count" in data
        assert "total_quantity_in" in data
        assert "total_quantity_out" in data
        assert "net_flow" in data
        assert "transactions" in data
