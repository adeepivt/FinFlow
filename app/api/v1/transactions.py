from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from app.database import get_db
from app.schemas.transaction import TransactionCreate, TransactionResponse, TransactionUpdate, TransactionSummary
from app.services.transaction_service import (
    create_transaction, get_user_transactions, get_transaction_by_id,
    update_transaction, delete_transaction, get_transaction_summary
)
from app.api.v1.auth import get_current_user
from app.models.user import User

router = APIRouter()


@router.post("/transactions", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_user_transaction(
    transaction_data: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new transaction.
    
    - **account_id**: Account to affect
    - **amount**: Amount (positive for income, will be converted for expenses)
    - **transaction_type**: income, expense, or transfer
    - **description**: What this transaction is for
    - **transfer_account_id**: Required for transfers only
    """
    try:
        return create_transaction(db, transaction_data, current_user.id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/transactions", response_model=List[TransactionResponse])
async def get_my_transactions(
    account_id: Optional[int] = Query(None, description="Filter by specific account"),
    limit: int = Query(100, ge=1, le=1000, description="Number of transactions to return"),
    offset: int = Query(0, ge=0, description="Number of transactions to skip"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get transactions for the authenticated user.
    Returns most recent transactions first.
    """
    return get_user_transactions(db, current_user.id, account_id, limit, offset)


@router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get specific transaction by ID.
    User can only access their own transactions.
    """
    transaction = get_transaction_by_id(db, transaction_id, current_user.id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    return transaction


@router.put("/transactions/{transaction_id}", response_model=TransactionResponse)
async def update_user_transaction(
    transaction_id: int,
    transaction_data: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a transaction.
    User can only update their own transactions.
    Note: Updating transfers is complex and may create inconsistencies.
    """
    transaction = update_transaction(db, transaction_id, current_user.id, transaction_data)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    return transaction


@router.delete("/transactions/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a transaction.
    This will reverse the transaction's effect on account balance.
    """
    success = delete_transaction(db, transaction_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    return None


@router.get("/transactions/reports/summary", response_model=TransactionSummary)
async def get_my_transaction_summary(
    account_id: Optional[int] = Query(None, description="Filter by specific account"),
    start_date: Optional[date] = Query(None, description="Start date for summary (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date for summary (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get transaction summary with totals and statistics.
    Useful for dashboards and reports.
    
    - **account_id**: Optional filter by account
    - **start_date**: Optional start date filter  
    - **end_date**: Optional end date filter
    """
    return get_transaction_summary(db, current_user.id, account_id, start_date, end_date)