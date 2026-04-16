"""
Transaction CRUD tests
Tests: create, read, update, delete transactions

Related to main project commits:
- feat: Portfolio manager API with transaction tracking
- feat: Add CSV database persistence
"""
import pytest


class TestTransactionCreation:
    """Test creating transactions"""

    def test_create_transaction_in(self, api_client, auth_headers, sample_transaction):
        """Should create incoming transaction"""
        response = api_client.post(
            "/transactions",
            headers=auth_headers,
            json=sample_transaction
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_transaction["name"]
        assert data["direction"] == "in"
        assert data["qty"] == sample_transaction["qty"]
        assert "id" in data
        assert "timestamp" in data

    def test_create_transaction_out(self, api_client, auth_headers, sample_transaction):
        """Should create outgoing transaction"""
        txn_data = {**sample_transaction, "direction": "out", "counterpart_id": "TEST_CUSTOMER"}
        response = api_client.post(
            "/transactions",
            headers=auth_headers,
            json=txn_data
        )
        assert response.status_code == 201
        data = response.json()
        assert data["direction"] == "out"

    def test_create_transaction_calculates_total_value(self, api_client, auth_headers, sample_transaction):
        """Should auto-calculate total_value"""
        response = api_client.post(
            "/transactions",
            headers=auth_headers,
            json=sample_transaction
        )
        data = response.json()
        expected = sample_transaction["cost"] * sample_transaction["qty"]
        assert data["total_value"] == expected

    def test_create_transaction_requires_auth(self, api_client, sample_transaction):
        """Should require authentication"""
        response = api_client.post("/transactions", json=sample_transaction)
        assert response.status_code == 401


class TestTransactionReading:
    """Test reading transactions"""

    def test_get_all_transactions(self, api_client, auth_headers):
        """Should return list of transactions"""
        response = api_client.get("/transactions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_transactions_pagination(self, api_client, auth_headers):
        """Should support pagination"""
        response = api_client.get("/transactions?limit=5&offset=0", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5

    def test_get_transaction_by_id(self, api_client, auth_headers, sample_transaction):
        """Should get specific transaction by ID"""
        # Create first
        create_response = api_client.post(
            "/transactions",
            headers=auth_headers,
            json=sample_transaction
        )
        created_id = create_response.json()["id"]

        # Get by ID
        response = api_client.get(f"/transactions/{created_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_id

    def test_get_nonexistent_transaction(self, api_client, auth_headers):
        """Should return 404 for nonexistent transaction"""
        response = api_client.get("/transactions/999999", headers=auth_headers)
        assert response.status_code == 404

    def test_filter_transactions_by_name(self, api_client, auth_headers, sample_transaction):
        """Should filter by name"""
        # Create transaction
        api_client.post("/transactions", headers=auth_headers, json=sample_transaction)

        # Filter by name
        response = api_client.get(
            f"/transactions?name={sample_transaction['name']}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert all(t["name"] == sample_transaction["name"] for t in data)

    def test_filter_transactions_by_direction(self, api_client, auth_headers):
        """Should filter by direction"""
        response = api_client.get("/transactions?direction=in", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert all(t["direction"] == "in" for t in data)


class TestTransactionUpdate:
    """Test updating transactions"""

    def test_update_transaction(self, api_client, auth_headers, sample_transaction):
        """Should update transaction fields"""
        # Create
        create_response = api_client.post(
            "/transactions",
            headers=auth_headers,
            json=sample_transaction
        )
        created_id = create_response.json()["id"]

        # Update
        update_data = {"notes": "Updated notes", "qty": 200}
        response = api_client.put(
            f"/transactions/{created_id}",
            headers=auth_headers,
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["notes"] == "Updated notes"
        assert data["qty"] == 200

    def test_update_nonexistent_transaction(self, api_client, auth_headers):
        """Should return 404 for nonexistent transaction"""
        response = api_client.put(
            "/transactions/999999",
            headers=auth_headers,
            json={"notes": "Update"}
        )
        assert response.status_code == 404

    def test_update_with_no_changes(self, api_client, auth_headers):
        """Should return 400 if no fields to update"""
        response = api_client.put(
            "/transactions/1",
            headers=auth_headers,
            json={}
        )
        assert response.status_code == 400


class TestTransactionDeletion:
    """Test deleting transactions"""

    def test_delete_transaction(self, api_client, auth_headers, sample_transaction):
        """Should delete transaction"""
        # Create
        create_response = api_client.post(
            "/transactions",
            headers=auth_headers,
            json=sample_transaction
        )
        created_id = create_response.json()["id"]

        # Delete
        response = api_client.delete(f"/transactions/{created_id}", headers=auth_headers)
        assert response.status_code == 204

        # Verify deleted
        get_response = api_client.get(f"/transactions/{created_id}", headers=auth_headers)
        assert get_response.status_code == 404

    def test_delete_nonexistent_transaction(self, api_client, auth_headers):
        """Should return 404 for nonexistent transaction"""
        response = api_client.delete("/transactions/999999", headers=auth_headers)
        assert response.status_code == 404
