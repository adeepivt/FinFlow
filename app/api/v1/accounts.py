from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas.account import AccountCreate, AccountResponse, AccountUpdate
from app.services.account_service import (
    create_account, get_user_accounts, get_account_by_id, 
    update_account, delete_account
)
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.account import Account

router = APIRouter()


@router.post("/accounts", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_user_account(
    account_data: AccountCreate, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new account for the authenticated user.
    """
    # Check if the user already has an account with the same name
    existing_account = db.query(Account).filter(
        Account.user_id == current_user.id,
        Account.name == account_data.name
    ).first()
    if existing_account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have an account with this name"
        )
    return create_account(db, account_data, current_user.id)


@router.get("/accounts", response_model=List[AccountResponse])
async def get_my_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_user_accounts(db, current_user.id)


@router.get("/accounts/{account_id}", response_model=AccountResponse)
async def get_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    account = get_account_by_id(db, account_id, current_user.id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    return account


@router.put("/accounts/{account_id}", response_model=AccountResponse)
def update_user_account(
    account_id: int,
    account_data: AccountUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    account = update_account(db, account_id, current_user.id, account_data)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    return account


@router.delete("/accounts/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    success = delete_account(db, account_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    return None