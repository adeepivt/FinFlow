from fastapi import APIRouter, Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from collections import defaultdict

from app.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.account import Account
from app.models.transaction import Transaction
from app.services.user_service import create_user, get_user_by_email
from app.services.account_service import get_user_accounts, create_account
from app.services.transaction_service import get_user_transactions, create_transaction
# from app.services.ai.insights_service import insights_service
from app.schemas.user import UserCreate
from app.schemas.account import AccountCreate
from app.schemas.transaction import TransactionCreate
from app.utils.security import verify_password, create_access_token

templates = Jinja2Templates(directory="app/templates")

router = APIRouter()


def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    """Get current user if logged in, None otherwise."""
    try:
        token = request.cookies.get("access_token")
        if not token:
            return None
        
        from app.utils.security import verify_token
        payload = verify_token(token)
        if not payload:
            return None
            
        email = payload.get("sub")
        if not email:
            return None
            
        return get_user_by_email(db, email)
    except:
        return None


def calculate_dashboard_stats(user_id: int, db: Session) -> dict:
    """Calculate dashboard statistics."""
    accounts = get_user_accounts(db, user_id)
    
    month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_transactions = db.query(Transaction).filter(
        Transaction.user_id == user_id,
        Transaction.transaction_date >= month_start
    ).all()
    
    total_balance = sum(float(acc.balance) for acc in accounts)
    monthly_income = sum(float(t.amount) for t in monthly_transactions if t.amount > 0)
    monthly_expenses = abs(sum(float(t.amount) for t in monthly_transactions if t.amount < 0))
    
    category_spending = defaultdict(float)
    for transaction in monthly_transactions:
        if transaction.amount < 0:  # Only expenses
            category = transaction.category or "uncategorized"
            category_spending[category] += abs(float(transaction.amount))
    
    return {
        "total_balance": total_balance,
        "monthly_income": monthly_income,
        "monthly_expenses": monthly_expenses,
        "accounts": accounts,
        "category_spending": dict(category_spending),
        "recent_transactions": monthly_transactions[-10:]  # Last 10 transactions
    }


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Display login form."""
    return templates.TemplateResponse("auth/login.html", {"request": request})


@router.post("/login")
async def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Process login form."""
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse(
            "auth/login.html", 
            {
                "request": request, 
                "error": "Invalid email or password"
            }
        )
    
    access_token = create_access_token(data={"sub": user.email})
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key="access_token", 
        value=access_token,
        httponly=True,
        max_age=1800,
        samesite="lax"
    )
    return response

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request, 
    db: Session = Depends(get_db)
):
    """Main dashboard page."""
    user = get_current_user_optional(request, db)
    
    if not user:
        return RedirectResponse(url="/login")
    
    stats = calculate_dashboard_stats(user.id, db)
    
    category_labels = list(stats["category_spending"].keys()) or ["No Data"]
    category_data = list(stats["category_spending"].values()) or [0]

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "total_balance": stats["total_balance"],
            "monthly_income": stats["monthly_income"],
            "monthly_expenses": stats["monthly_expenses"],
            "accounts": stats["accounts"],
            "recent_transactions": stats["recent_transactions"],
            "category_labels": category_labels,
            "category_data": category_data,
        }
    )


