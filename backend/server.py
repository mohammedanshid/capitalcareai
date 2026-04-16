from dotenv import load_dotenv
from pathlib import Path
import os

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends
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
    
    return {
        "total_income": round(total_income, 2),
        "total_expenses": round(total_expenses, 2),
        "balance": round(balance, 2),
        "transaction_count": len(transactions)
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

Please analyze this data and provide:
1. Spending behavior analysis
2. Overspending patterns (if any)
3. Money leaks or wasteful spending
4. Budget optimization suggestions
5. Savings recommendations
6. Action items for better financial health

Format your response in two sections:
1. REASONING: Your detailed internal analysis and thought process
2. INSIGHTS: Clear, concise, actionable recommendations for the user (this will be shown to them)

Use this exact format:
REASONING:
[Your detailed analysis here]

INSIGHTS:
[User-facing recommendations here]
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

# ============== STARTUP EVENTS ==============

@app.on_event("startup")
async def startup_event():
    # Create indexes
    await db.users.create_index("email", unique=True)
    await db.login_attempts.create_index("identifier")
    await db.transactions.create_index([("user_id", 1), ("date", -1)])
    
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
