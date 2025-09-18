from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from app.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.services.ai.categorization_service import categorization_service, STANDARD_CATEGORIES

router = APIRouter()


class CategorizationRequest(BaseModel):
    description: str
    amount: float
    merchant: str = None


class CategorizationResponse(BaseModel):
    description: str
    suggested_category: str
    confidence: str
    available_categories: List[str]


class BulkCategorizationRequest(BaseModel):
    transactions: List[dict]


@router.post("/ai/categorize", response_model=CategorizationResponse)
def categorize_transaction_ai(
    request: CategorizationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Get AI-powered category suggestion for a transaction.
    
    - **description**: Transaction description (e.g., "Starbucks Coffee")
    - **amount**: Transaction amount (positive/negative)
    - **merchant**: Optional merchant name
    """
    if not categorization_service.enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI categorization service is not available. Please configure OPENAI_API_KEY."
        )
    
    try:
        category = categorization_service.categorize_transaction(
            description=request.description,
            amount=request.amount,
            merchant=request.merchant
        )
        
        confidence = "high" if categorization_service.enabled else "medium"
        
        return CategorizationResponse(
            description=request.description,
            suggested_category=category,
            confidence=confidence,
            available_categories=STANDARD_CATEGORIES
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Categorization failed: {str(e)}"
        )


@router.get("/ai/categories")
def get_available_categories(current_user: User = Depends(get_current_user)):
    """
    Get list of available transaction categories.
    """
    return {
        "categories": STANDARD_CATEGORIES,
        "ai_enabled": categorization_service.enabled,
        "description": "Standard financial categories used by FinFlow AI"
    }


@router.post("/ai/categorize-bulk")
def bulk_categorize_transactions(
    request: BulkCategorizationRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Categorize multiple transactions at once.
    Useful for importing bank statements.
    
    Request format:
    {
        "transactions": [
            {"id": 1, "description": "Starbucks", "amount": -5.50},
            {"id": 2, "description": "Salary", "amount": 3000.00}
        ]
    }
    """
    if not categorization_service.enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI categorization service is not available."
        )
    
    try:
        results = categorization_service.batch_categorize_transactions(request.transactions)
        
        return {
            "categorized_count": len(results),
            "categories": results,
            "ai_enabled": True
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk categorization failed: {str(e)}"
        )