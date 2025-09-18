from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal
from datetime import datetime, date

from app.models.transaction import Transaction
from app.models.account import Account
from app.schemas.transaction import TransactionCreate, TransactionUpdate, TransactionSummary
from app.services.ai.categorization_service import categorization_service

def create_transaction(db: Session, transaction_data: TransactionCreate, user_id: int) -> Transaction:
    """
    Create a new transaction and update account balance.
    Handles transfers by creating two transactions.
    """
    account = db.query(Account).filter(
        Account.id == transaction_data.account_id,
        Account.user_id == user_id,
        Account.is_active == True
    ).first()
    
    if not account:
        raise ValueError("Account not found or access denied")
    
    if not transaction_data.category and transaction_data.transaction_type != "transfer":
        ai_category = categorization_service.categorize_transaction(
            description=transaction_data.description,
            amount=float(transaction_data.amount)
        )
        transaction_data.category = ai_category
        print(f"AI categorized '{transaction_data.description}' as '{ai_category}'")

    if transaction_data.transaction_type == 'transfer':
        return _create_transfer_transactions(db, transaction_data, user_id)
    else:
        return _create_single_transaction(db, transaction_data, user_id)


def _create_single_transaction(db: Session, transaction_data: TransactionCreate, user_id: int) -> Transaction:
    """Create a single transaction (income or expense)."""
    
    db_transaction = Transaction(
        user_id=user_id,
        account_id=transaction_data.account_id,
        amount=transaction_data.amount,
        description=transaction_data.description,
        category=transaction_data.category,
        transaction_type=transaction_data.transaction_type,
        notes=transaction_data.notes,
        reference=transaction_data.reference,
        transaction_date=transaction_data.transaction_date
    )
    
    db.add(db_transaction)
    account = db.query(Account).filter(Account.id == transaction_data.account_id).first()
    account.balance += transaction_data.amount
    
    db.commit()
    db.refresh(db_transaction)
    return db_transaction


def _create_transfer_transactions(db: Session, transaction_data: TransactionCreate, user_id: int) -> Transaction:
    """
    Create transfer between two accounts.
    Creates two transactions: negative in source, positive in destination.
    """
 
    transfer_account = db.query(Account).filter(
        Account.id == transaction_data.transfer_account_id,
        Account.user_id == user_id,
        Account.is_active == True
    ).first()
    
    if not transfer_account:
        raise ValueError("Transfer account not found or access denied")
    
    transfer_amount = abs(transaction_data.amount)
    
    outgoing_transaction = Transaction(
        user_id=user_id,
        account_id=transaction_data.account_id,
        amount=-transfer_amount,
        description=f"Transfer to {transfer_account.name}",
        category="transfer",
        transaction_type="transfer",
        transfer_account_id=transaction_data.transfer_account_id,
        notes=transaction_data.notes,
        reference=transaction_data.reference,
        transaction_date=transaction_data.transaction_date
    )
    
    incoming_transaction = Transaction(
        user_id=user_id,
        account_id=transaction_data.transfer_account_id,
        amount=transfer_amount,
        description=f"Transfer from {db.query(Account).filter(Account.id == transaction_data.account_id).first().name}",
        category="transfer",
        transaction_type="transfer",
        transfer_account_id=transaction_data.account_id,
        notes=transaction_data.notes,
        reference=transaction_data.reference,
        transaction_date=transaction_data.transaction_date
    )
    
    source_account = db.query(Account).filter(Account.id == transaction_data.account_id).first()
    source_account.balance -= transfer_amount
    transfer_account.balance += transfer_amount
    
    db.add(outgoing_transaction)
    db.add(incoming_transaction)
    db.commit()
    
    db.refresh(outgoing_transaction)
    return outgoing_transaction


def get_user_transactions(
    db: Session, 
    user_id: int, 
    account_id: Optional[int] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Transaction]:
    """
    Get transactions for a user, optionally filtered by account.
    """
    query = db.query(Transaction).filter(Transaction.user_id == user_id)
    
    if account_id:
        account = db.query(Account).filter(
            Account.id == account_id,
            Account.user_id == user_id
        ).first()
        if not account:
            return []
        
        query = query.filter(Transaction.account_id == account_id)
    
    return query.order_by(Transaction.transaction_date.desc()).offset(offset).limit(limit).all()


def get_transaction_by_id(db: Session, transaction_id: int, user_id: int) -> Transaction | None:
    """
    Get specific transaction by ID (only if user owns it).
    """
    return db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == user_id
    ).first()


def update_transaction(
    db: Session, 
    transaction_id: int, 
    user_id: int, 
    transaction_data: TransactionUpdate
) -> Transaction | None:
    """
    Update a transaction.
    Note: Transfer transactions require special handling.
    """
    transaction = get_transaction_by_id(db, transaction_id, user_id)
    if not transaction:
        return None
    
    old_amount = transaction.amount
    update_data = transaction_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(transaction, field, value)
    
    if 'amount' in update_data:
        account = db.query(Account).filter(Account.id == transaction.account_id).first()
        balance_diff = transaction.amount - old_amount
        account.balance += balance_diff
    
    db.commit()
    db.refresh(transaction)
    return transaction


def delete_transaction(db: Session, transaction_id: int, user_id: int) -> bool:
    """
    Delete a transaction and reverse its effect on account balance.
    """
    transaction = get_transaction_by_id(db, transaction_id, user_id)
    if not transaction:
        return False
    
    account = db.query(Account).filter(Account.id == transaction.account_id).first()
    account.balance -= transaction.amount
    
    # Delete the transaction
    db.delete(transaction)
    db.commit()
    return True


def get_transaction_summary(
    db: Session, 
    user_id: int, 
    account_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> TransactionSummary:
    """
    Get transaction summary (total income, expenses, etc.) for reporting.
    """
    query = db.query(Transaction).filter(Transaction.user_id == user_id)
    
    if account_id:
        query = query.filter(Transaction.account_id == account_id)
    
    if start_date:
        query = query.filter(Transaction.transaction_date >= start_date)
    
    if end_date:
        query = query.filter(Transaction.transaction_date <= end_date)
    
    transactions = query.all()
    
    total_income = sum(t.amount for t in transactions if t.amount > 0)
    total_expenses = abs(sum(t.amount for t in transactions if t.amount < 0))
    
    return TransactionSummary(
        total_income=Decimal(str(total_income)),
        total_expenses=Decimal(str(total_expenses)),
        net_amount=Decimal(str(total_income)) - Decimal(str(total_expenses)),
        transaction_count=len(transactions)
    )