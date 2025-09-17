from pydantic import BaseModel, field_validator
from datetime import datetime
from decimal import Decimal
from typing import Optional


class AccountBase(BaseModel):
    name: str
    account_type: str
    # account_number: Optional[str] = None
    # institution: Optional[str] = None


class AccountCreate(AccountBase):
    balance: Optional[Decimal] = Decimal('0.00')
    
    @field_validator('account_type')
    def validate_account_type(cls, v):
        """Ensure account type is valid."""
        allowed_types = ['checking', 'savings', 'credit_card', 'investment', 'cash']
        if v not in allowed_types:
            raise ValueError(f'Account type must be one of: {", ".join(allowed_types)}')
        return v
    
    @field_validator('balance')
    def validate_balance(cls, v):
        """Ensure balance is reasonable."""
        if v is not None and v < Decimal('-999999.99'):
            raise ValueError('Balance cannot be less than -999,999.99')
        if v is not None and v > Decimal('999999999.99'):
            raise ValueError('Balance cannot be more than 999,999,999.99')
        return v


class AccountResponse(AccountBase):
    """Data returned when showing account info."""
    id: int
    user_id: int
    balance: Decimal
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class AccountUpdate(BaseModel):
    """Data that can be updated."""
    name: Optional[str] = None
    account_type: Optional[str] = None
    balance: Optional[Decimal] = None
    # account_number: Optional[str] = None
    # institution: Optional[str] = None
    is_active: Optional[bool] = None
    
    @field_validator('account_type')
    def validate_account_type(cls, v):
        """Ensure account type is valid if provided."""
        if v is not None:
            allowed_types = ['checking', 'savings', 'credit_card', 'investment', 'cash']
            if v not in allowed_types:
                raise ValueError(f'Account type must be one of: {", ".join(allowed_types)}')
        return v