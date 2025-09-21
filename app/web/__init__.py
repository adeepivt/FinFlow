from fastapi import APIRouter, Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
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
from app.services.ai.insights_service import insights_service
from app.schemas.user import UserCreate
from app.schemas.account import AccountCreate
from app.schemas.transaction import TransactionCreate
from app.utils.security import verify_password, create_access_token

templates = Jinja2Templates(directory="app/templates")

router = APIRouter()


def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
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
    return templates.TemplateResponse("auth/login.html", {"request": request})


@router.post("/login")
async def login_post(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
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


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("auth/register.html", {"request": request})


@router.post("/register")
async def register_post(
    request: Request,
    email: str = Form(...),
    full_name: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    if password != confirm_password:
        return templates.TemplateResponse(
            "auth/register.html",
            {
                "request": request,
                "error": "Passwords do not match",
                "email": email,
                "full_name": full_name
            }
        )
    
    try:
        user_data = UserCreate(email=email, full_name=full_name, password=password)
        user = create_user(db, user_data)
        
        access_token = create_access_token(data={"sub": user.email})
        response = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            max_age=1800
        )
        return response
        
    except ValueError as e:
        return templates.TemplateResponse(
            "auth/register.html",
            {
                "request": request,
                "error": str(e),
                "email": email,
                "full_name": full_name
            }
        )


@router.post("/logout")
async def logout():
    response = Response(status_code=200)
    response.delete_cookie(key="access_token")
    response.headers["HX-Redirect"] = "/login"
    return response


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request, 
    db: Session = Depends(get_db)
):
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


@router.get("/accounts", response_class=HTMLResponse)
async def accounts_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if not user:
        return RedirectResponse(url="/login")
    
    accounts = get_user_accounts(db, user.id)
    
    return templates.TemplateResponse(
        "accounts/list.html",
        {
            "request": request,
            "user": user,
            "accounts": accounts
        }
    )


@router.get("/accounts/add", response_class=HTMLResponse)
async def add_account_form(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if not user:
        return RedirectResponse(url="/login")
    
    return templates.TemplateResponse(
        "accounts/form.html",
        {
            "request": request,
            "user": user,
            "action": "add"
        }
    )


@router.post("/accounts/add")
async def add_account_post(
    request: Request,
    name: str = Form(...),
    account_type: str = Form(...),
    balance: float = Form(0.0),
    db: Session = Depends(get_db)
):
    user = get_current_user_optional(request, db)
    if not user:
        return RedirectResponse(url="/login")
    
    try:
        account_data = AccountCreate(
            name=name,
            account_type=account_type,
            balance=balance,
        )
        create_account(db, account_data, user.id)
        
        return HTMLResponse("""
            <div class="bg-green-50 border border-green-200 rounded-md p-4">
                <p class="text-green-800">Account created successfully!</p>
            </div>
            <script>
                setTimeout(() => window.location.reload(), 1000);
            </script>
        """)
        
    except Exception as e:
        return templates.TemplateResponse(
            "accounts/form.html",
            {
                "request": request,
                "user": user,
                "error": str(e),
                "name": name,
                "account_type": account_type,
                "balance": balance,
            }
        )


@router.get("/transactions", response_class=HTMLResponse)
async def transactions_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if not user:
        return RedirectResponse(url="/login")
    
    transactions = get_user_transactions(db, user.id, limit=50)
    accounts = get_user_accounts(db, user.id)
    
    return templates.TemplateResponse(
        "transactions/list.html",
        {
            "request": request,
            "user": user,
            "transactions": transactions,
            "accounts": accounts
        }
    )


@router.get("/transactions/add", response_class=HTMLResponse)
async def add_transaction_form(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if not user:
        return RedirectResponse(url="/login")
    
    accounts = get_user_accounts(db, user.id)
    
    return templates.TemplateResponse(
        "transactions/form.html",
        {
            "request": request,
            "user": user,
            "accounts": accounts,
            "transaction_type": "income"
        }
    )


@router.get("/transactions/add-expense", response_class=HTMLResponse)
async def add_expense_form(request: Request, db: Session = Depends(get_db)):
    user = get_current_user_optional(request, db)
    if not user:
        return HTMLResponse("<p>Please login</p>", status_code=401)
    
    accounts = get_user_accounts(db, user.id)
    
    return templates.TemplateResponse(
        "transactions/form.html",
        {
            "request": request,
            "user": user,
            "accounts": accounts,
            "transaction_type": "expense"
        }
    )


@router.post("/transactions/add")
async def add_transaction_post(
    request: Request,
    account_id: int = Form(...),
    amount: float = Form(...),
    description: str = Form(...),
    transaction_type: str = Form(...),
    category: str = Form(""),
    transaction_date: str = Form(...),
    db: Session = Depends(get_db)
):
    user = get_current_user_optional(request, db)
    if not user:
        return RedirectResponse(url="/login")
    
    try:
        parsed_date = datetime.fromisoformat(transaction_date.replace('T', ' '))
        
        transaction_data = TransactionCreate(
            account_id=account_id,
            amount=amount,
            description=description,
            transaction_type=transaction_type,
            category=category or None,
            transaction_date=parsed_date
        )
        
        create_transaction(db, transaction_data, user.id)
        
        return HTMLResponse("""
            <div class="bg-green-50 border border-green-200 rounded-md p-4">
                <p class="text-green-800">Transaction added successfully!</p>
            </div>
            <script>
                setTimeout(() => window.location.reload(), 1000);
            </script>
        """)
        
    except Exception as e:
        accounts = get_user_accounts(db, user.id)
        return templates.TemplateResponse(
            "transactions/form.html",
            {
                "request": request,
                "user": user,
                "accounts": accounts,
                "error": str(e),
                "account_id": account_id,
                "amount": amount,
                "description": description,
                "transaction_type": transaction_type,
                "category": category
            }
        )


@router.get("/insights", response_class=HTMLResponse)
async def insights_page(request: Request, db: Session = Depends(get_db)):
    """AI insights page."""
    user = get_current_user_optional(request, db)
    if not user:
        return RedirectResponse(url="/login")
    
    insights = insights_service.generate_spending_insights(user.id, db)
    
    return templates.TemplateResponse(
        "insights.html",
        {
            "request": request,
            "user": user,
            "insights": insights
        }
    )


# # HTMX Partial Routes (for dynamic content)
# @router.get("/transactions/recent", response_class=HTMLResponse)
# async def recent_transactions_partial(request: Request, db: Session = Depends(get_db)):
#     """Return recent transactions HTML partial for HTMX."""
#     user = get_current_user_optional(request, db)
#     print(user,'user-------')
#     if not user:
#         return HTMLResponse("<p>Please login</p>")
    
#     transactions = get_user_transactions(db, user.id, limit=5)
#     print('we are here-----\n\n', transactions)
#     html = ""
#     for transaction in transactions:
#         amount_color = "text-green-600" if transaction.amount > 0 else "text-red-600"
#         amount_prefix = "+" if transaction.amount > 0 else ""
        
#         html += f"""
#         <div class="flex justify-between items-center py-2 border-b">
#             <div>
#                 <p class="font-medium">{transaction.description}</p>
#                 <p class="text-sm text-gray-500">{transaction.category or 'Uncategorized'}</p>
#             </div>
#             <div class="text-right">
#                 <p class="{amount_color} font-medium">
#                     {amount_prefix}₹{abs(float(transaction.amount)):.2f}
#                 </p>
#                 <p class="text-sm text-gray-500">
#                     {transaction.transaction_date.strftime('%m/%d')}
#                 </p>
#             </div>
#         </div>
#         """
    
#     return HTMLResponse(html)