from pydantic import BaseModel, field_validator, Field, ValidationInfo
from datetime import datetime
from decimal import Decimal
from typing import Optional


class TransactionBase(BaseModel):
    transaction_type: str
    amount: Decimal
    description: str
    category: Optional[str] = None
    notes: Optional[str] = None
    reference: Optional[str] = None
    transaction_date: datetime = Field(default_factory=datetime.now)


class TransactionCreate(TransactionBase):
    account_id: int
    transfer_account_id: Optional[int] = None
    
    @field_validator('transaction_type')
    @classmethod
    def validate_transaction_type(cls, v):
        """Ensure transaction type is valid."""
        allowed_types = ['income', 'expense', 'transfer']
        if v not in allowed_types:
            raise ValueError(f'Transaction type must be one of: {", ".join(allowed_types)}')
        return v
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v, info: ValidationInfo):
        """Validate amount based on transaction type."""
        transaction_type = info.data.get('transaction_type')
        
        if v == 0:
            raise ValueError('Amount cannot be zero')
        if transaction_type == 'expense' and v > 0:
            v = -abs(v)
        if transaction_type == 'income' and v < 0:
            v = abs(v) 
            
        return v
    
    @field_validator('transfer_account_id')
    @classmethod
    def validate_transfer_account(cls, v, info: ValidationInfo):
        """Transfer transactions must have transfer_account_id."""
        transaction_type = info.data.get('transaction_type')
        
        if transaction_type == 'transfer':
            if v is None:
                raise ValueError('Transfer transactions must specify transfer_account_id')
            if v == info.data.get('account_id'):
                raise ValueError('Cannot transfer to the same account')
        
        elif transaction_type in ['income', 'expense'] and v is not None:
            raise ValueError('Income and expense transactions cannot have transfer_account_id')
            
        return v


class TransactionResponse(TransactionBase):
    id: int
    user_id: int
    account_id: int
    transaction_type: str
    transfer_account_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TransactionUpdate(BaseModel):
    amount: Optional[Decimal] = None
    description: Optional[str] = None
    category: Optional[str] = None
    notes: Optional[str] = None
    reference: Optional[str] = None
    transaction_date: Optional[datetime] = None
    
    @field_validator('amount')
    def validate_amount(cls, v):
        """Amount cannot be zero if provided."""
        if v is not None and v == 0:
            raise ValueError('Amount cannot be zero')
        return v


class TransactionSummary(BaseModel):
    total_income: Decimal
    total_expenses: Decimal
    net_amount: Decimal
    transaction_count: int