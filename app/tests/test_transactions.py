import pytest
from datetime import datetime, date
from decimal import Decimal
from app.tests.conftest import client


class TestTransactionCreation:
    def test_create_income_transaction(self, auth_headers, test_account, db):
        """Test creating an income transaction."""
        transaction_data = {
            "account_id": test_account.id,
            "amount": 2500.00,
            "description": "Salary Payment",
            "transaction_type": "income",
            "category": "income",
            "transaction_date": "2024-01-15T10:00:00"
        }
        
        original_balance = test_account.balance
        response = client.post("/api/v1/transactions", json=transaction_data, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["description"] == transaction_data["description"]
        assert data["transaction_type"] == "income"
        assert float(data["amount"]) == transaction_data["amount"]
        
        db.refresh(test_account)
        assert test_account.balance == original_balance + Decimal(str(transaction_data["amount"]))
    
    def test_create_expense_transaction(self, auth_headers, test_account, db):
        """Test creating an expense transaction."""
        transaction_data = {
            "account_id": test_account.id,
            "amount": 150.75,
            "description": "Grocery Store",
            "transaction_type": "expense",
            "category": "groceries",
            "transaction_date": "2024-01-15T14:30:00"
        }
        
        original_balance = test_account.balance
        response = client.post("/api/v1/transactions", json=transaction_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["description"] == transaction_data["description"]
        assert data["transaction_type"] == "expense"
        assert float(data["amount"]) == -transaction_data["amount"]
        db.refresh(test_account)
        expected_balance = original_balance - Decimal(str(transaction_data["amount"]))
        assert test_account.balance == expected_balance
    
    def test_create_transfer_transaction(self, auth_headers, test_account, test_savings_account, db):
        """Test creating a transfer between accounts."""
        transaction_data = {
            "account_id": test_account.id,
            "transfer_account_id": test_savings_account.id,
            "amount": 200.00,
            "description": "Transfer to Savings",
            "transaction_type": "transfer",
            "transaction_date": "2024-01-15T16:00:00"
        }
        
        original_checking = test_account.balance
        original_savings = test_savings_account.balance
        
        response = client.post("/api/v1/transactions", json=transaction_data, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["transaction_type"] == "transfer"
        
        db.refresh(test_account)
        db.refresh(test_savings_account)
        
        transfer_amount = Decimal(str(transaction_data["amount"]))
        assert test_account.balance == original_checking - transfer_amount
        assert test_savings_account.balance == original_savings + transfer_amount
    
    def test_create_transaction_invalid_account(self, auth_headers):
        """Test creating transaction with invalid account ID fails."""
        transaction_data = {
            "account_id": 99999,
            "amount": 100.00,
            "description": "Test Transaction",
            "transaction_type": "income",
            "transaction_date": "2024-01-15T10:00:00"
        }
        
        response = client.post("/api/v1/transactions", json=transaction_data, headers=auth_headers)
        assert response.status_code == 400
    
    def test_create_transaction_without_auth(self, test_account):
        """Test creating transaction without authentication fails."""
        transaction_data = {
            "account_id": test_account.id,
            "amount": 100.00,
            "description": "Test Transaction",
            "transaction_type": "income",
            "transaction_date": "2024-01-15T10:00:00"
        }
        
        response = client.post("/api/v1/transactions", json=transaction_data)
        assert response.status_code == 401


class TestTransactionRetrieval:
    """Test transaction retrieval functionality."""
    
    def test_get_user_transactions(self, auth_headers, test_account):
        """Test getting all user transactions."""
        transaction_data = {
            "account_id": test_account.id,
            "amount": 500.00,
            "description": "Test Income",
            "transaction_type": "income",
            "transaction_date": "2024-01-15T10:00:00"
        }
        
        client.post("/api/v1/transactions", json=transaction_data, headers=auth_headers)

        response = client.get("/api/v1/transactions", headers=auth_headers)
        
        assert response.status_code == 200
        transactions = response.json()
        assert len(transactions) >= 1
        assert transactions[0]["description"] == "Test Income"
    
    def test_get_transactions_by_account(self, auth_headers, test_account):
        """Test filtering transactions by account."""
        transaction_data = {
            "account_id": test_account.id,
            "amount": 300.00,
            "description": "Account Specific Transaction",
            "transaction_type": "income",
            "transaction_date": "2024-01-15T10:00:00"
        }
        
        client.post("/api/v1/transactions", json=transaction_data, headers=auth_headers)
        
        response = client.get(
            f"/api/v1/transactions?account_id={test_account.id}", 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        transactions = response.json()
        assert len(transactions) >= 1
        assert all(t["account_id"] == test_account.id for t in transactions)


class TestTransactionSummary:
    """Test transaction summary functionality."""
    
    def test_get_transaction_summary(self, auth_headers, test_account):
        """Test getting transaction summary."""
        transactions = [
            {
                "account_id": test_account.id,
                "amount": 1000.00,
                "description": "Income 1",
                "transaction_type": "income",
                "transaction_date": "2024-01-15T10:00:00"
            },
            {
                "account_id": test_account.id,
                "amount": 200.00,
                "description": "Expense 1",
                "transaction_type": "expense",
                "transaction_date": "2024-01-15T14:00:00"
            }
        ]
        
        for transaction in transactions:
            client.post("/api/v1/transactions", json=transaction, headers=auth_headers)
        
        response = client.get("/api/v1/transactions/reports/summary", headers=auth_headers)
        
        assert response.status_code == 200
        summary = response.json()
        assert "total_income" in summary
        assert "total_expenses" in summary
        assert "net_amount" in summary
        assert "transaction_count" in summary
        
        assert float(summary["total_income"]) == 1000.00
        assert float(summary["total_expenses"]) == 200.00
        assert summary["transaction_count"] >= 2