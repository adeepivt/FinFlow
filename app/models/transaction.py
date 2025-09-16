from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    amount = Column(Numeric(precision=10, scale=2), nullable=False)  # Positive = income, Negative = expense
    description = Column(String, nullable=False)  # "Salary", "Grocery Store", "Coffee"
    category = Column(String, nullable=True)      # "salary", "food", "transport" (we'll expand this later)
    transaction_type = Column(String, nullable=False)  # "income", "expense", "transfer"
    notes = Column(Text, nullable=True)           # Additional user notes
    reference = Column(String, nullable=True)    # Check number, confirmation code, etc.
    transfer_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    transaction_date = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    account = relationship("Account", foreign_keys=[account_id], back_populates="transactions")
    transfer_account = relationship("Account", foreign_keys=[transfer_account_id])
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, amount={self.amount}, description='{self.description}')>"