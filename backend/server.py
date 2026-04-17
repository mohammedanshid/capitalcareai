from dotenv import load_dotenv
from pathlib import Path
import os

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends
from fastapi.responses import StreamingResponse
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import logging
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from bson import ObjectId
import bcrypt
import jwt
import secrets
from emergentintegrations.llm.chat import LlmChat, UserMessage
import csv
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'default-secret-change-me')
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Create the main app
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ============== AUTH UTILITIES ==============

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def create_access_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        "type": "access"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def create_refresh_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        "type": "refresh"
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        user["id"] = str(user["_id"])
        user.pop("_id", None)
        user.pop("password_hash", None)
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication error: {str(e)}")

# ============== MODELS ==============

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    created_at: str

class TransactionCreate(BaseModel):
    type: str  # "income" or "expense"
    amount: float
    category: str
    description: Optional[str] = ""
    date: str

class TransactionResponse(BaseModel):
    id: str
    user_id: str
    type: str
    amount: float
    category: str
    description: str
    date: str
    created_at: str

class DashboardSummary(BaseModel):
    total_income: float
    total_expenses: float
    balance: float
    transaction_count: int

class AnalyzeRequest(BaseModel):
    transactions: List[Dict[str, Any]]

class AnalyzeResponse(BaseModel):
    insights: str
    raw_reasoning: str
    created_at: str

# ============== AUTH ENDPOINTS ==============

@api_router.post("/auth/register")
async def register(user: UserRegister, response: Response):
    email_lower = user.email.lower()
    existing = await db.users.find_one({"email": email_lower})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed = hash_password(user.password)
    user_doc = {
        "name": user.name,
        "email": email_lower,
        "password_hash": hashed,
        "created_at": datetime.now(timezone.utc)
    }
    
    result = await db.users.insert_one(user_doc)
    user_id = str(result.inserted_id)
    
    access_token = create_access_token(user_id, email_lower)
    refresh_token = create_refresh_token(user_id)
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/"
    )
    
    return {
        "id": user_id,
        "name": user.name,
        "email": email_lower,
        "created_at": user_doc["created_at"].isoformat()
    }

@api_router.post("/auth/login")
async def login(credentials: UserLogin, response: Response, request: Request):
    email_lower = credentials.email.lower()
    
    # Check brute force protection
    ip = request.client.host
    identifier = f"{ip}:{email_lower}"
    attempts = await db.login_attempts.find_one({"identifier": identifier})
    
    if attempts and attempts.get("count", 0) >= 5:
        lockout_until = attempts.get("lockout_until")
        if lockout_until and lockout_until > datetime.now(timezone.utc):
            raise HTTPException(status_code=429, detail="Too many failed attempts. Try again later.")
    
    user = await db.users.find_one({"email": email_lower})
    if not user or not verify_password(credentials.password, user["password_hash"]):
        # Increment failed attempts
        await db.login_attempts.update_one(
            {"identifier": identifier},
            {
                "$inc": {"count": 1},
                "$set": {
                    "lockout_until": datetime.now(timezone.utc) + timedelta(minutes=15),
                    "updated_at": datetime.now(timezone.utc)
                }
            },
            upsert=True
        )
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Clear failed attempts on successful login
    await db.login_attempts.delete_one({"identifier": identifier})
    
    user_id = str(user["_id"])
    access_token = create_access_token(user_id, email_lower)
    refresh_token = create_refresh_token(user_id)
    
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/"
    )
    
    return {
        "id": user_id,
        "name": user["name"],
        "email": email_lower,
        "created_at": user["created_at"].isoformat()
    }

@api_router.post("/auth/logout")
async def logout(response: Response, user: dict = Depends(get_current_user)):
    response.delete_cookie(key="access_token", path="/")
    response.delete_cookie(key="refresh_token", path="/")
    return {"message": "Logged out successfully"}

@api_router.get("/auth/me")
async def get_me(user: dict = Depends(get_current_user)):
    return user

@api_router.post("/auth/refresh")
async def refresh(request: Request, response: Response):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        user = await db.users.find_one({"_id": ObjectId(payload["sub"])})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        user_id = str(user["_id"])
        access_token = create_access_token(user_id, user["email"])
        
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            path="/"
        )
        
        return {"message": "Token refreshed"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

# ============== FINANCE ENDPOINTS ==============

@api_router.post("/transactions")
async def create_transaction(transaction: TransactionCreate, user: dict = Depends(get_current_user)):
    if transaction.type not in ["income", "expense"]:
        raise HTTPException(status_code=400, detail="Type must be 'income' or 'expense'")
    
    if transaction.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than 0")
    
    trans_doc = {
        "user_id": user["id"],
        "type": transaction.type,
        "amount": transaction.amount,
        "category": transaction.category,
        "description": transaction.description or "",
        "date": transaction.date,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    result = await db.transactions.insert_one(trans_doc)
    trans_doc["id"] = str(result.inserted_id)
    trans_doc.pop("_id", None)
    
    return trans_doc

@api_router.get("/transactions")
async def get_transactions(user: dict = Depends(get_current_user)):
    transactions = await db.transactions.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).sort("date", -1).to_list(1000)
    
    # Add id field from stored data
    for trans in transactions:
        if "id" not in trans and "_id" in trans:
            trans["id"] = str(trans["_id"])
    
    return transactions

@api_router.delete("/transactions/{transaction_id}")
async def delete_transaction(transaction_id: str, user: dict = Depends(get_current_user)):
    # Try to delete by MongoDB _id first, then by custom id field
    try:
        # Try as MongoDB ObjectId
        result = await db.transactions.delete_one({"_id": ObjectId(transaction_id), "user_id": user["id"]})
        if result.deleted_count == 0:
            # Try as custom id field
            result = await db.transactions.delete_one({"id": transaction_id, "user_id": user["id"]})
    except:
        # If ObjectId conversion fails, try as custom id field
        result = await db.transactions.delete_one({"id": transaction_id, "user_id": user["id"]})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"message": "Transaction deleted"}

@api_router.get("/dashboard/summary")
async def get_summary(user: dict = Depends(get_current_user)):
    transactions = await db.transactions.find({"user_id": user["id"]}).to_list(10000)
    
    total_income = sum(t["amount"] for t in transactions if t["type"] == "income")
    total_expenses = sum(t["amount"] for t in transactions if t["type"] == "expense")
    balance = total_income - total_expenses
    
    # Build monthly data for sparklines (last 6 months)
    from collections import defaultdict
    monthly = defaultdict(lambda: {"income": 0, "expenses": 0})
    for t in transactions:
        month_key = t["date"][:7]  # "YYYY-MM"
        if t["type"] == "income":
            monthly[month_key]["income"] += t["amount"]
        else:
            monthly[month_key]["expenses"] += t["amount"]
    
    sorted_months = sorted(monthly.keys())[-6:]
    sparkline_income = [round(monthly[m]["income"], 2) for m in sorted_months]
    sparkline_expenses = [round(monthly[m]["expenses"], 2) for m in sorted_months]
    sparkline_profit = [round(monthly[m]["income"] - monthly[m]["expenses"], 2) for m in sorted_months]
    sparkline_cashflow = sparkline_profit  # alias
    
    # Trends (compare last two months)
    def calc_trend(values):
        if len(values) < 2 or values[-2] == 0:
            return 0
        return round(((values[-1] - values[-2]) / abs(values[-2])) * 100, 1)
    
    # Current month cash flow
    now_month = datetime.now(timezone.utc).strftime("%Y-%m")
    current_income = monthly[now_month]["income"]
    current_expenses = monthly[now_month]["expenses"]
    cash_flow = round(current_income - current_expenses, 2)
    
    # Monthly breakdown for line chart
    monthly_series = []
    for m in sorted_months:
        monthly_series.append({
            "month": m,
            "income": round(monthly[m]["income"], 2),
            "expenses": round(monthly[m]["expenses"], 2),
            "profit": round(monthly[m]["income"] - monthly[m]["expenses"], 2),
        })
    
    return {
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expenses, 2),
        "balance": round(balance, 2),
        "cash_flow": cash_flow,
        "transaction_count": len(transactions),
        "sparkline_income": sparkline_income,
        "sparkline_expenses": sparkline_expenses,
        "sparkline_profit": sparkline_profit,
        "sparkline_cashflow": sparkline_cashflow,
        "trend_income": calc_trend(sparkline_income),
        "trend_expenses": calc_trend(sparkline_expenses),
        "trend_profit": calc_trend(sparkline_profit),
        "trend_cashflow": calc_trend(sparkline_cashflow),
        "monthly_series": monthly_series,
    }

@api_router.post("/analyze")
async def analyze_finances(user: dict = Depends(get_current_user)):
    # Get all user transactions
    transactions = await db.transactions.find({"user_id": user["id"]}).to_list(10000)
    
    if not transactions:
        raise HTTPException(status_code=400, detail="No transactions found. Add some transactions first.")
    
    # Prepare data for AI
    trans_summary = []
    for t in transactions:
        trans_summary.append({
            "type": t["type"],
            "amount": t["amount"],
            "category": t["category"],
            "date": t["date"],
            "description": t.get("description", "")
        })
    
    # Calculate basic stats
    total_income = sum(t["amount"] for t in transactions if t["type"] == "income")
    total_expenses = sum(t["amount"] for t in transactions if t["type"] == "expense")
    
    # Group expenses by category
    expense_by_category = {}
    for t in transactions:
        if t["type"] == "expense":
            cat = t["category"]
            expense_by_category[cat] = expense_by_category.get(cat, 0) + t["amount"]
    
    # Prepare prompt for AI
    prompt = f"""You are a professional financial advisor. Analyze the following financial data and provide actionable insights.

User's Financial Summary:
- Total Income: ${total_income:.2f}
- Total Expenses: ${total_expenses:.2f}
- Net Balance: ${total_income - total_expenses:.2f}
- Number of Transactions: {len(transactions)}

Expenses by Category:
{chr(10).join([f"- {cat}: ${amt:.2f}" for cat, amt in sorted(expense_by_category.items(), key=lambda x: x[1], reverse=True)])}

Recent Transactions:
{chr(10).join([f"- {t['date']}: {t['type'].title()} ${t['amount']:.2f} ({t['category']}) - {t.get('description', 'No description')}" for t in transactions[-20:]])}

Please analyze this data and provide insights in TWO sections:

SECTION 1 - REASONING:
Your detailed internal analysis and thought process (this will be hidden by default).

SECTION 2 - INSIGHTS:
Provide clear, well-structured recommendations using this EXACT format:

1. Spending behavior analysis
- Key observation 1
- Key observation 2
- Key observation 3

2. Overspending patterns (if any)
- Pattern 1 with specific details
- Pattern 2 with specific details

3. Money leaks or wasteful spending
- Leak 1 with recommendation
- Leak 2 with recommendation

4. Budget optimization suggestions
- Suggestion 1 with specific numbers
- Suggestion 2 with specific numbers
- Suggestion 3 with specific numbers

5. Savings recommendations
- Recommendation 1 with actionable steps
- Recommendation 2 with actionable steps
- Recommendation 3 with actionable steps

6. Action items for better financial health
- Action 1 (specific and measurable)
- Action 2 (specific and measurable)
- Action 3 (specific and measurable)

IMPORTANT: Use bullet points (-) for all items. Be specific with numbers and percentages. Keep each bullet point concise (1-2 sentences max).

Format your complete response as:

REASONING:
[Your detailed analysis here]

INSIGHTS:
[Your structured recommendations here following the exact format above]
"""
    
    try:
        # Use emergentintegrations to call OpenAI GPT-5.2
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        chat = LlmChat(
            api_key=api_key,
            session_id=f"finance_analysis_{user['id']}_{datetime.now(timezone.utc).timestamp()}",
            system_message="You are a professional financial advisor providing clear, actionable financial insights."
        )
        chat.with_model("openai", "gpt-5.2")
        
        user_message = UserMessage(text=prompt)
        ai_response = await chat.send_message(user_message)
        
        # Parse response to extract reasoning and insights
        response_text = ai_response.strip()
        
        reasoning = ""
        insights = ""
        
        if "REASONING:" in response_text and "INSIGHTS:" in response_text:
            parts = response_text.split("INSIGHTS:")
            reasoning = parts[0].replace("REASONING:", "").strip()
            insights = parts[1].strip()
        else:
            # If format not followed, use entire response as insights
            insights = response_text
            reasoning = "AI provided direct recommendations without detailed reasoning."
        
        # Store analysis in database
        analysis_doc = {
            "user_id": user["id"],
            "insights": insights,
            "raw_reasoning": reasoning,
            "transaction_count": len(transactions),
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.ai_analyses.insert_one(analysis_doc)
        
        return {
            "insights": insights,
            "raw_reasoning": reasoning,
            "created_at": analysis_doc["created_at"]
        }
        
    except Exception as e:
        logging.error(f"AI analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze finances: {str(e)}")


@api_router.get("/analyze/latest")
async def get_latest_analysis(user: dict = Depends(get_current_user)):
    """Get the most recent AI analysis for the sidebar panel"""
    analysis = await db.ai_analyses.find(
        {"user_id": user["id"]},
        {"_id": 0}
    ).sort("created_at", -1).limit(1).to_list(1)
    
    if not analysis:
        return {"has_analysis": False}
    
    return {
        "has_analysis": True,
        "insights": analysis[0].get("insights", ""),
        "created_at": analysis[0].get("created_at", ""),
    }


# ============== CATEGORIES MANAGEMENT ==============

class CategoryCreate(BaseModel):
    name: str
    type: str  # "income" or "expense"
    icon: Optional[str] = ""

class CategoryResponse(BaseModel):
    id: str
    user_id: str
    name: str
    type: str
    icon: str
    is_default: bool
    created_at: str

@api_router.get("/categories")
async def get_categories(user: dict = Depends(get_current_user)):
    # Get default categories
    default_categories = [
        {"name": "Salary", "type": "income", "icon": "💼", "is_default": True},
        {"name": "Freelance", "type": "income", "icon": "💻", "is_default": True},
        {"name": "Investment", "type": "income", "icon": "📈", "is_default": True},
        {"name": "Gift", "type": "income", "icon": "🎁", "is_default": True},
        {"name": "Other Income", "type": "income", "icon": "💰", "is_default": True},
        {"name": "Food", "type": "expense", "icon": "🍔", "is_default": True},
        {"name": "Transport", "type": "expense", "icon": "🚗", "is_default": True},
        {"name": "Shopping", "type": "expense", "icon": "🛍️", "is_default": True},
        {"name": "Bills", "type": "expense", "icon": "📄", "is_default": True},
        {"name": "Entertainment", "type": "expense", "icon": "🎬", "is_default": True},
        {"name": "Healthcare", "type": "expense", "icon": "🏥", "is_default": True},
        {"name": "Education", "type": "expense", "icon": "📚", "is_default": True},
        {"name": "Other Expense", "type": "expense", "icon": "💸", "is_default": True},
    ]
    
    # Get custom categories
    custom_categories = await db.categories.find({"user_id": user["id"]}, {"_id": 0}).to_list(100)
    for cat in custom_categories:
        cat["is_default"] = False
    
    return default_categories + custom_categories

@api_router.post("/categories")
async def create_category(category: CategoryCreate, user: dict = Depends(get_current_user)):
    if category.type not in ["income", "expense"]:
        raise HTTPException(status_code=400, detail="Type must be 'income' or 'expense'")
    
    cat_doc = {
        "id": str(ObjectId()),
        "user_id": user["id"],
        "name": category.name,
        "type": category.type,
        "icon": category.icon or "📌",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.categories.insert_one(cat_doc)
    cat_doc["is_default"] = False
    cat_doc.pop("_id", None)
    return cat_doc

@api_router.delete("/categories/{category_id}")
async def delete_category(category_id: str, user: dict = Depends(get_current_user)):
    result = await db.categories.delete_one({"id": category_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted"}

# ============== BUDGET MANAGEMENT ==============

class BudgetCreate(BaseModel):
    category: str
    limit: float
    period: str = "monthly"  # monthly, weekly, yearly

class BudgetResponse(BaseModel):
    id: str
    user_id: str
    category: str
    limit: float
    spent: float
    period: str
    percentage: float
    status: str  # "safe", "warning", "exceeded"
    created_at: str

@api_router.get("/budgets")
async def get_budgets(user: dict = Depends(get_current_user)):
    budgets = await db.budgets.find({"user_id": user["id"]}, {"_id": 0}).to_list(100)
    
    # Calculate spent amounts for each budget
    current_month = datetime.now(timezone.utc).strftime("%Y-%m")
    
    for budget in budgets:
        # Get transactions for this category in current period
        transactions = await db.transactions.find({
            "user_id": user["id"],
            "type": "expense",
            "category": budget["category"],
            "date": {"$regex": f"^{current_month}"}
        }).to_list(1000)
        
        spent = sum(t["amount"] for t in transactions)
        budget["spent"] = round(spent, 2)
        budget["percentage"] = round((spent / budget["limit"]) * 100, 1) if budget["limit"] > 0 else 0
        
        if budget["percentage"] >= 100:
            budget["status"] = "exceeded"
        elif budget["percentage"] >= 80:
            budget["status"] = "warning"
        else:
            budget["status"] = "safe"
    
    return budgets

@api_router.post("/budgets")
async def create_budget(budget: BudgetCreate, user: dict = Depends(get_current_user)):
    if budget.limit <= 0:
        raise HTTPException(status_code=400, detail="Budget limit must be greater than 0")
    
    # Check if budget already exists for this category
    existing = await db.budgets.find_one({"user_id": user["id"], "category": budget.category})
    if existing:
        raise HTTPException(status_code=400, detail="Budget already exists for this category")
    
    budget_doc = {
        "id": str(ObjectId()),
        "user_id": user["id"],
        "category": budget.category,
        "limit": budget.limit,
        "period": budget.period,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.budgets.insert_one(budget_doc)
    budget_doc.pop("_id", None)
    budget_doc["spent"] = 0
    budget_doc["percentage"] = 0
    budget_doc["status"] = "safe"
    return budget_doc

@api_router.put("/budgets/{budget_id}")
async def update_budget(budget_id: str, budget: BudgetCreate, user: dict = Depends(get_current_user)):
    result = await db.budgets.update_one(
        {"id": budget_id, "user_id": user["id"]},
        {"$set": {"limit": budget.limit, "period": budget.period}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Budget not found")
    return {"message": "Budget updated"}

@api_router.delete("/budgets/{budget_id}")
async def delete_budget(budget_id: str, user: dict = Depends(get_current_user)):
    result = await db.budgets.delete_one({"id": budget_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Budget not found")
    return {"message": "Budget deleted"}

# ============== RECURRING TRANSACTIONS ==============

class RecurringTransactionCreate(BaseModel):
    type: str  # "income" or "expense"
    amount: float
    category: str
    description: Optional[str] = ""
    frequency: str  # "daily", "weekly", "monthly", "yearly"
    start_date: str
    end_date: Optional[str] = None

class RecurringTransactionResponse(BaseModel):
    id: str
    user_id: str
    type: str
    amount: float
    category: str
    description: str
    frequency: str
    start_date: str
    end_date: Optional[str]
    next_occurrence: str
    is_active: bool
    created_at: str

@api_router.get("/recurring-transactions")
async def get_recurring_transactions(user: dict = Depends(get_current_user)):
    recurring = await db.recurring_transactions.find({"user_id": user["id"]}, {"_id": 0}).to_list(100)
    return recurring

@api_router.post("/recurring-transactions")
async def create_recurring_transaction(recurring: RecurringTransactionCreate, user: dict = Depends(get_current_user)):
    if recurring.type not in ["income", "expense"]:
        raise HTTPException(status_code=400, detail="Type must be 'income' or 'expense'")
    
    if recurring.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be greater than 0")
    
    if recurring.frequency not in ["daily", "weekly", "monthly", "yearly"]:
        raise HTTPException(status_code=400, detail="Invalid frequency")
    
    recurring_doc = {
        "id": str(ObjectId()),
        "user_id": user["id"],
        "type": recurring.type,
        "amount": recurring.amount,
        "category": recurring.category,
        "description": recurring.description or "",
        "frequency": recurring.frequency,
        "start_date": recurring.start_date,
        "end_date": recurring.end_date,
        "next_occurrence": recurring.start_date,
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.recurring_transactions.insert_one(recurring_doc)
    recurring_doc.pop("_id", None)
    return recurring_doc

@api_router.delete("/recurring-transactions/{recurring_id}")
async def delete_recurring_transaction(recurring_id: str, user: dict = Depends(get_current_user)):
    result = await db.recurring_transactions.delete_one({"id": recurring_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Recurring transaction not found")
    return {"message": "Recurring transaction deleted"}

@api_router.post("/recurring-transactions/process")
async def process_recurring_transactions(user: dict = Depends(get_current_user)):
    """Manually trigger processing of recurring transactions"""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    recurring_list = await db.recurring_transactions.find({
        "user_id": user["id"],
        "is_active": True,
        "next_occurrence": {"$lte": today}
    }).to_list(100)
    
    created_count = 0
    for recurring in recurring_list:
        # Create transaction
        trans_doc = {
            "user_id": user["id"],
            "type": recurring["type"],
            "amount": recurring["amount"],
            "category": recurring["category"],
            "description": f"{recurring['description']} (Recurring)",
            "date": recurring["next_occurrence"],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "id": str(ObjectId())
        }
        await db.transactions.insert_one(trans_doc)
        created_count += 1
        
        # Calculate next occurrence
        next_date = datetime.fromisoformat(recurring["next_occurrence"])
        if recurring["frequency"] == "daily":
            next_date += timedelta(days=1)
        elif recurring["frequency"] == "weekly":
            next_date += timedelta(weeks=1)
        elif recurring["frequency"] == "monthly":
            # Add one month
            if next_date.month == 12:
                next_date = next_date.replace(year=next_date.year + 1, month=1)
            else:
                next_date = next_date.replace(month=next_date.month + 1)
        elif recurring["frequency"] == "yearly":
            next_date = next_date.replace(year=next_date.year + 1)
        
        # Update next occurrence
        await db.recurring_transactions.update_one(
            {"id": recurring["id"]},
            {"$set": {"next_occurrence": next_date.strftime("%Y-%m-%d")}}
        )
    
    return {"message": f"Processed {created_count} recurring transactions"}

# ============== EXPORT FUNCTIONALITY ==============

@api_router.get("/export/csv")
async def export_csv(user: dict = Depends(get_current_user)):
    transactions = await db.transactions.find({"user_id": user["id"]}).sort("date", -1).to_list(10000)
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(["Date", "Type", "Category", "Amount", "Description"])
    
    # Write data
    for trans in transactions:
        writer.writerow([
            trans["date"],
            trans["type"].title(),
            trans["category"],
            f"${trans['amount']:.2f}",
            trans.get("description", "")
        ])
    
    # Create response
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=transactions_{datetime.now().strftime('%Y%m%d')}.csv"}
    )

@api_router.get("/export/pdf")
async def export_pdf(user: dict = Depends(get_current_user)):
    transactions = await db.transactions.find({"user_id": user["id"]}).sort("date", -1).to_list(10000)
    summary = await db.transactions.aggregate([
        {"$match": {"user_id": user["id"]}},
        {"$group": {
            "_id": "$type",
            "total": {"$sum": "$amount"}
        }}
    ]).to_list(10)
    
    # Calculate totals
    total_income = sum(s["total"] for s in summary if s["_id"] == "income")
    total_expenses = sum(s["total"] for s in summary if s["_id"] == "expense")
    balance = total_income - total_expenses
    
    # Create PDF in memory
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#09090B'),
        spaceAfter=30,
    )
    
    # Title
    elements.append(Paragraph("Financial Report", title_style))
    elements.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
    elements.append(Spacer(1, 0.3*inch))
    
    # Summary table
    summary_data = [
        ["Summary", "Amount"],
        ["Total Income", f"${total_income:.2f}"],
        ["Total Expenses", f"${total_expenses:.2f}"],
        ["Balance", f"${balance:.2f}"]
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#09090B')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 0.5*inch))
    
    # Transactions table
    elements.append(Paragraph("Transactions", styles['Heading2']))
    elements.append(Spacer(1, 0.2*inch))
    
    trans_data = [["Date", "Type", "Category", "Amount", "Description"]]
    for trans in transactions[:50]:  # Limit to 50 for PDF
        trans_data.append([
            trans["date"],
            trans["type"].title(),
            trans["category"],
            f"${trans['amount']:.2f}",
            (trans.get("description", ""))[:30]
        ])
    
    trans_table = Table(trans_data, colWidths=[1.2*inch, 0.8*inch, 1.2*inch, 1*inch, 2*inch])
    trans_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#09090B')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    
    elements.append(trans_table)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=financial_report_{datetime.now().strftime('%Y%m%d')}.pdf"}
    )

# ============== STARTUP EVENTS ==============

@app.on_event("startup")
async def startup_event():
    # Create indexes
    await db.users.create_index("email", unique=True)
    await db.login_attempts.create_index("identifier")
    await db.transactions.create_index([("user_id", 1), ("date", -1)])
    await db.categories.create_index([("user_id", 1), ("name", 1)])
    await db.budgets.create_index([("user_id", 1), ("category", 1)])
    await db.recurring_transactions.create_index([("user_id", 1), ("next_occurrence", 1)])
    
    # Seed admin user
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@financeapp.com")
    admin_password = os.environ.get("ADMIN_PASSWORD", "Admin@123")
    
    existing_admin = await db.users.find_one({"email": admin_email})
    if existing_admin is None:
        hashed = hash_password(admin_password)
        await db.users.insert_one({
            "email": admin_email,
            "password_hash": hashed,
            "name": "Admin User",
            "role": "admin",
            "created_at": datetime.now(timezone.utc)
        })
        logging.info(f"Admin user created: {admin_email}")
    elif not verify_password(admin_password, existing_admin["password_hash"]):
        await db.users.update_one(
            {"email": admin_email},
            {"$set": {"password_hash": hash_password(admin_password)}}
        )
        logging.info(f"Admin password updated: {admin_email}")
    
    # Write test credentials
    test_creds_path = Path("/app/memory")
    test_creds_path.mkdir(exist_ok=True)
    with open(test_creds_path / "test_credentials.md", "w") as f:
        f.write(f"""# Test Credentials for Finance App

## Admin Account
- Email: {admin_email}
- Password: {admin_password}
- Role: admin

## Test User Account
- Email: testuser@example.com
- Password: Test@123
- Role: user

## Auth Endpoints
- POST /api/auth/register
- POST /api/auth/login
- POST /api/auth/logout
- GET /api/auth/me
- POST /api/auth/refresh

## Finance Endpoints
- POST /api/transactions
- GET /api/transactions
- DELETE /api/transactions/{{id}}
- GET /api/dashboard/summary
- POST /api/analyze
""")

# Include the router in the main app
app.include_router(api_router)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
