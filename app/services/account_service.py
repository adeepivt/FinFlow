from sqlalchemy.orm import Session
from typing import List

from app.models.account import Account
from app.schemas.account import AccountCreate, AccountUpdate


def create_account(db: Session, account_data: AccountCreate, user_id: int) -> Account:
    db_account = Account(
        user_id=user_id,
        name=account_data.name,
        account_type=account_data.account_type,
        balance=account_data.balance,
        # account_number=account_data.account_number,
        # institution=account_data.institution
    )
    
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account


def get_user_accounts(db: Session, user_id: int) -> List[Account]:
    return db.query(Account).filter(
        Account.user_id == user_id,
        Account.is_active == True
    ).all()


def get_account_by_id(db: Session, account_id: int, user_id: int) -> Account | None:
    return db.query(Account).filter(
        Account.id == account_id,
        Account.user_id == user_id,
        Account.is_active == True
    ).first()


def update_account(db: Session, account_id: int, user_id: int, account_data: AccountUpdate) -> Account | None:
    account = get_account_by_id(db, account_id, user_id)
    if not account:
        return None
    
    update_data = account_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(account, field, value)
    
    db.commit()
    db.refresh(account)
    return account


def delete_account(db: Session, account_id: int, user_id: int) -> bool:
    account = get_account_by_id(db, account_id, user_id)
    if not account:
        return False
    
    account.is_active = False
    db.commit()
    return True