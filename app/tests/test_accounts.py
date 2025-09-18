import pytest
from decimal import Decimal
from app.tests.conftest import client


class TestAccountCreation:
    def test_create_account_success(self, auth_headers):
        """Test successful account creation."""
        account_data = {
            "name": "My Checking Account",
            "account_type": "checking",
            "balance": 1500.50,
            "account_number": "****1234"
        }
        
        response = client.post("/api/v1/accounts", json=account_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == account_data["name"]
        assert data["account_type"] == account_data["account_type"]
        assert float(data["balance"]) == account_data["balance"]
        assert "id" in data
        assert "user_id" in data
    
    def test_create_account_without_auth(self):
        """Test account creation without authentication fails."""
        account_data = {
            "name": "Test Account",
            "account_type": "checking"
        }
        
        response = client.post("/api/v1/accounts", json=account_data)
        assert response.status_code == 401
    
    def test_create_account_invalid_type(self, auth_headers):
        """Test creating account with invalid type fails."""
        account_data = {
            "name": "Test Account",
            "account_type": "invalid_type"
        }
        
        response = client.post("/api/v1/accounts", json=account_data, headers=auth_headers)
        assert response.status_code == 422
    
    def test_create_account_default_balance(self, auth_headers):
        """Test account creation with default balance."""
        account_data = {
            "name": "Zero Balance Account",
            "account_type": "savings"
        }
        
        response = client.post("/api/v1/accounts", json=account_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert float(data["balance"]) == 0.00


class TestAccountRetrieval:
    def test_get_user_accounts(self, auth_headers, test_account):
        """Test getting all user accounts."""
        response = client.get("/api/v1/accounts", headers=auth_headers)
        
        assert response.status_code == 200
        accounts = response.json()
        assert len(accounts) == 1
        assert accounts[0]["id"] == test_account.id
        assert accounts[0]["name"] == test_account.name
    
    def test_get_specific_account(self, auth_headers, test_account):
        """Test getting specific account by ID."""
        response = client.get(f"/api/v1/accounts/{test_account.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_account.id
        assert data["name"] == test_account.name
        assert float(data["balance"]) == float(test_account.balance)
    
    def test_get_nonexistent_account(self, auth_headers):
        """Test getting non-existent account returns 404."""
        response = client.get("/api/v1/accounts/99999", headers=auth_headers)
        assert response.status_code == 404
    
    def test_get_accounts_without_auth(self):
        """Test getting accounts without authentication fails."""
        response = client.get("/api/v1/accounts")
        assert response.status_code == 401


class TestAccountUpdate:
    def test_update_account_name(self, auth_headers, test_account):
        """Test updating account name."""
        update_data = {"name": "Updated Account Name"}
        
        response = client.put(
            f"/api/v1/accounts/{test_account.id}", 
            json=update_data, 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == update_data["name"]
        assert data["id"] == test_account.id
    
    def test_update_account_balance(self, auth_headers, test_account):
        """Test updating account balance."""
        update_data = {"balance": 2500.75}
        
        response = client.put(
            f"/api/v1/accounts/{test_account.id}", 
            json=update_data, 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert float(data["balance"]) == update_data["balance"]
    
    def test_update_nonexistent_account(self, auth_headers):
        """Test updating non-existent account returns 404."""
        update_data = {"name": "New Name"}
        
        response = client.put("/api/v1/accounts/99999", json=update_data, headers=auth_headers)
        assert response.status_code == 404


class TestAccountDeletion:
    def test_delete_account(self, auth_headers, test_account):
        """Test soft deleting an account."""
        response = client.delete(f"/api/v1/accounts/{test_account.id}", headers=auth_headers)
        
        assert response.status_code == 204
        
        # Verify account is not returned in list (soft deleted)
        response = client.get("/api/v1/accounts", headers=auth_headers)
        accounts = response.json()
        assert len(accounts) == 0  # Should be empty since account is inactive
    
    def test_delete_nonexistent_account(self, auth_headers):
        """Test deleting non-existent account returns 404."""
        response = client.delete("/api/v1/accounts/99999", headers=auth_headers)
        assert response.status_code == 404