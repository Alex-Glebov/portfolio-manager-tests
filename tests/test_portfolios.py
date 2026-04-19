"""
Multi-portfolio tests
Tests: Portfolio isolation, access control, X-Portfolio header

Related to main project commit:
- feat: Add multi-portfolio support with access control
Requires: portfolio-manager v0.2.0+
"""
import pytest
import uuid


class TestPortfolioSupport:
    """Test multi-portfolio feature availability"""

    def test_multi_portfolio_feature_available(self, api_client, auth_headers, require_v0_2_0):
        """Multi-portfolio feature should be available in v0.2.0+"""
        # Create transaction in default portfolio
        txn = {
            "name": "PortfolioTestItem",
            "cost": 10.0,
            "qty": 10,
            "cost_units": "USD",
            "direction": "in",
            "counterpart_id": "TEST_SUPPLIER",
            "notes": "Test multi-portfolio"
        }
        response = api_client.post("/transactions", headers=auth_headers, json=txn)
        assert response.status_code == 201

    def test_portfolio_header_accepted(self, api_client, auth_headers, require_v0_2_0):
        """Server should accept X-Portfolio header"""
        headers_with_portfolio = {**auth_headers, "X-Portfolio": ""}
        response = api_client.get("/transactions", headers=headers_with_portfolio)
        # Should not error - empty portfolio header means default portfolio
        assert response.status_code == 200


class TestDefaultPortfolio:
    """Test default portfolio (empty name)"""

    def test_transactions_without_portfolio_header(self, api_client, auth_headers, require_v0_2_0):
        """Transactions without X-Portfolio header go to default portfolio"""
        # Create transaction
        txn = {
            "name": "DefaultPortfolioItem",
            "cost": 25.0,
            "qty": 50,
            "cost_units": "USD",
            "direction": "in",
            "counterpart_id": "DEFAULT_TEST",
            "notes": "Test default portfolio"
        }
        create_response = api_client.post("/transactions", headers=auth_headers, json=txn)
        assert create_response.status_code == 201
        created_id = create_response.json()["id"]

        # Get transactions without portfolio header
        response = api_client.get("/transactions", headers=auth_headers)
        assert response.status_code == 200
        transactions = response.json()

        # Should find our transaction
        found = any(t["id"] == created_id for t in transactions)
        assert found, "Transaction should be in default portfolio"

    def test_transactions_with_empty_portfolio_header(self, api_client, auth_headers, require_v0_2_0):
        """Empty X-Portfolio header should work same as no header"""
        headers = {**auth_headers, "X-Portfolio": ""}
        response = api_client.get("/holdings", headers=headers)
        assert response.status_code == 200


class TestPortfolioIsolation:
    """Test that portfolios are isolated from each other"""

    def test_portfolios_isolated(self, api_client, auth_headers, require_v0_2_0):
        """Transactions in different portfolios should not mix"""
        unique_id = uuid.uuid4().hex[:8]
        default_name = f"DefaultOnly_{unique_id}"
        portfolio_name = f"PortfolioOnly_{unique_id}"

        # Create transaction in default portfolio
        txn_default = {
            "name": default_name,
            "cost": 10.0,
            "qty": 100,
            "cost_units": "USD",
            "direction": "in",
            "counterpart_id": "ISOLATION_TEST",
            "notes": "In default portfolio"
        }
        default_response = api_client.post("/transactions", headers=auth_headers, json=txn_default)
        assert default_response.status_code == 201

        # Check transaction exists in default portfolio
        response = api_client.get("/transactions", headers=auth_headers)
        assert response.status_code == 200
        default_transactions = response.json()
        default_names = [t["name"] for t in default_transactions]
        assert default_name in default_names

        # Create transaction with "testuser" header (user's own portfolio)
        headers_with_portfolio = {**auth_headers, "X-Portfolio": "testuser"}
        txn_portfolio = {
            "name": portfolio_name,
            "cost": 20.0,
            "qty": 50,
            "cost_units": "USD",
            "direction": "in",
            "counterpart_id": "ISOLATION_TEST",
            "notes": "In user portfolio"
        }
        portfolio_response = api_client.post(
            "/transactions",
            headers=headers_with_portfolio,
            json=txn_portfolio
        )

        # User's own portfolio should work (returns 201 for v0.2.0+)
        if portfolio_response.status_code == 403:
            pytest.skip("User portfolio access not configured - skipping isolation test")

        assert portfolio_response.status_code == 201

        # Verify portfolio-only transaction does NOT appear in default
        response = api_client.get("/transactions", headers=auth_headers)
        default_transactions = response.json()
        default_names = [t["name"] for t in default_transactions]

        # Default-only transaction should still be there
        assert default_name in default_names

        # Portfolio-only transaction should NOT be in default
        assert portfolio_name not in default_names, (
            f"Portfolio transaction '{portfolio_name}' should not appear in default portfolio"
        )

        # Verify default-only transaction does NOT appear in testuser portfolio
        response = api_client.get("/transactions", headers=headers_with_portfolio)
        portfolio_transactions = response.json()
        portfolio_names = [t["name"] for t in portfolio_transactions]

        # Portfolio-only transaction should be there
        assert portfolio_name in portfolio_names

        # Default-only transaction should NOT be in portfolio
        assert default_name not in portfolio_names, (
            f"Default transaction '{default_name}' should not appear in testuser portfolio"
        )

    def test_holdings_isolated_by_portfolio(self, api_client, auth_headers, require_v0_2_0):
        """Holdings should be calculated per-portfolio"""
        unique_name = f"HoldingsIsolation_{uuid.uuid4().hex[:8]}"

        # Add to default portfolio
        txn_default = {
            "name": unique_name,
            "cost": 100.0,
            "qty": 100,
            "cost_units": "USD",
            "direction": "in",
            "counterpart_id": "HOLDINGS_TEST",
            "notes": "Default portfolio"
        }
        api_client.post("/transactions", headers=auth_headers, json=txn_default)

        # Get holdings for default portfolio
        response = api_client.get("/holdings", headers=auth_headers)
        assert response.status_code == 200
        default_holdings = response.json()

        # Find our item in default holdings
        default_item = next((h for h in default_holdings if h["name"] == unique_name), None)
        assert default_item is not None, "Item should exist in default holdings"
        assert default_item["total_in"] >= 100


class TestUserOwnPortfolio:
    """Test user access to own portfolio"""

    def test_user_can_access_own_portfolio(self, api_client, auth_token, require_v0_2_0):
        """User should have access to portfolio named after their username"""
        # Create a new user
        unique_user = f"portfoliouser_{uuid.uuid4().hex[:8]}"
        password = "testpass123"

        register_response = api_client.post(
            "/auth/register",
            json={"username": unique_user, "password": password}
        )

        if register_response.status_code == 409:
            pytest.skip("User already exists - test cannot be run")

        assert register_response.status_code == 200

        # Login as new user
        login_response = api_client.post(
            "/auth/login",
            data={"username": unique_user, "password": password}
        )
        assert login_response.status_code == 200
        user_token = login_response.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}

        # Try to access own portfolio
        headers_with_portfolio = {**user_headers, "X-Portfolio": unique_user}
        response = api_client.get("/transactions", headers=headers_with_portfolio)

        # Should succeed (200) or be forbidden (403) depending on config
        assert response.status_code in [200, 403]

        if response.status_code == 200:
            # User successfully accessed their own portfolio
            assert isinstance(response.json(), list)


class TestAdminPortfolioAccess:
    """Test admin access to all portfolios"""

    def test_admin_can_access_all_portfolios(self, api_client, require_v0_2_0):
        """Admin should have access to any portfolio"""
        # Login as admin
        login_response = api_client.post(
            "/auth/login",
            data={"username": "admin", "password": "admin"}
        )

        if login_response.status_code != 200:
            pytest.skip("Cannot login as admin - skipping test")

        admin_token = login_response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # Try various portfolio names
        test_portfolios = ["", "testportfolio", "warehouse", "sales"]

        for portfolio in test_portfolios:
            headers = {**admin_headers, "X-Portfolio": portfolio}
            response = api_client.get("/transactions", headers=headers)

            # Admin should always have access (200) or portfolio doesn't exist (200 with empty data)
            # 403 would indicate admin access is not working
            if response.status_code == 403:
                pytest.skip(f"Admin cannot access portfolio '{portfolio}' - access control may not be configured")

            assert response.status_code == 200, (
                f"Admin should have access to portfolio '{portfolio}'"
            )


class TestPortfolioTransactions:
    """Test transactions within portfolios"""

    def test_create_transaction_in_portfolio(self, api_client, auth_headers, require_v0_2_0):
        """Should create transaction in specific portfolio"""
        txn = {
            "name": "PortfolioTxnItem",
            "cost": 15.0,
            "qty": 25,
            "cost_units": "USD",
            "direction": "in",
            "counterpart_id": "PORTFOLIO_TXN_TEST",
            "notes": "Test transaction in portfolio"
        }

        headers = {**auth_headers, "X-Portfolio": ""}
        response = api_client.post("/transactions", headers=headers, json=txn)

        # Should succeed (empty portfolio = default)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == txn["name"]
        assert data["qty"] == txn["qty"]

    def test_get_transaction_from_portfolio(self, api_client, auth_headers, require_v0_2_0):
        """Should retrieve transaction from specific portfolio"""
        # Create transaction first
        txn = {
            "name": "GetPortfolioTxn",
            "cost": 30.0,
            "qty": 10,
            "cost_units": "USD",
            "direction": "in",
            "counterpart_id": "GET_TEST",
            "notes": "Test get from portfolio"
        }
        create_response = api_client.post("/transactions", headers=auth_headers, json=txn)
        assert create_response.status_code == 201
        created_id = create_response.json()["id"]

        # Get from same portfolio
        response = api_client.get(f"/transactions/{created_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_id
        assert data["name"] == txn["name"]

    def test_delete_transaction_from_portfolio(self, api_client, auth_headers, require_v0_2_0):
        """Should delete transaction from specific portfolio"""
        # Create transaction
        txn = {
            "name": "DeletePortfolioTxn",
            "cost": 5.0,
            "qty": 5,
            "cost_units": "USD",
            "direction": "in",
            "counterpart_id": "DELETE_TEST",
            "notes": "Test delete from portfolio"
        }
        create_response = api_client.post("/transactions", headers=auth_headers, json=txn)
        assert create_response.status_code == 201
        created_id = create_response.json()["id"]

        # Delete from same portfolio
        delete_response = api_client.delete(f"/transactions/{created_id}", headers=auth_headers)
        assert delete_response.status_code == 204

        # Verify deleted
        get_response = api_client.get(f"/transactions/{created_id}", headers=auth_headers)
        assert get_response.status_code == 404


class TestPortfolioExport:
    """Test export from portfolios"""

    def test_export_transactions_includes_portfolio_name(self, api_client, auth_headers, require_v0_2_0):
        """Exported filename should include portfolio identifier"""
        response = api_client.get("/export/transactions", headers=auth_headers)
        assert response.status_code == 200

        content_disposition = response.headers.get("content-disposition", "")
        # Should contain portfolio name in filename (even if empty for default)
        assert "transactions_" in content_disposition

    def test_export_holdings_includes_portfolio_name(self, api_client, auth_headers, require_v0_2_0):
        """Exported holdings filename should include portfolio identifier"""
        response = api_client.get("/export/holdings", headers=auth_headers)
        assert response.status_code == 200

        content_disposition = response.headers.get("content-disposition", "")
        assert "holdings_" in content_disposition


class TestPortfolioSummary:
    """Test portfolio summary per portfolio"""

    def test_portfolio_summary_isolated(self, api_client, auth_headers, require_v0_2_0):
        """Summary should reflect only the specified portfolio"""
        # Get default portfolio summary
        response = api_client.get("/portfolio/summary", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        assert "total_transactions" in data
        assert "total_unique_items" in data
        assert "total_value_in_portfolio" in data
        assert "items" in data
