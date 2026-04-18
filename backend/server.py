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
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
from bson import ObjectId
from collections import defaultdict
import bcrypt
import jwt
import csv
import io
from emergentintegrations.llm.chat import LlmChat, UserMessage

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

JWT_SECRET = os.environ.get('JWT_SECRET', 'default-secret')
JWT_ALGORITHM = "HS256"

app = FastAPI()
api = APIRouter(prefix="/api")

# ═══════════════════ AUTH UTILS ═══════════════════
def hash_pw(pw): return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
def verify_pw(pw, h): return bcrypt.checkpw(pw.encode(), h.encode())
def make_token(uid, email, ttype="access", mins=15):
    return jwt.encode({"sub": uid, "email": email, "exp": datetime.now(timezone.utc) + timedelta(minutes=mins), "type": ttype}, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        ah = request.headers.get("Authorization", "")
        if ah.startswith("Bearer "): token = ah[7:]
    if not token: raise HTTPException(401, "Not authenticated")
    try:
        p = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if p.get("type") != "access": raise HTTPException(401, "Bad token")
        u = await db.users.find_one({"_id": ObjectId(p["sub"])})
        if not u: raise HTTPException(401, "User not found")
        u["_id"] = str(u["_id"]); u.pop("password_hash", None)
        return u
    except jwt.ExpiredSignatureError: raise HTTPException(401, "Token expired")
    except jwt.InvalidTokenError: raise HTTPException(401, "Invalid token")

def set_cookies(response, uid, email):
    at = make_token(uid, email, "access", 60)
    rt = make_token(uid, email, "refresh", 10080)
    for k, v, m in [("access_token", at, 3600), ("refresh_token", rt, 604800)]:
        response.set_cookie(key=k, value=v, httponly=True, secure=False, samesite="lax", max_age=m, path="/")

# ═══════════════════ AUTH ENDPOINTS ═══════════════════
class RegBody(BaseModel):
    name: str; email: EmailStr; password: str
class LoginBody(BaseModel):
    email: EmailStr; password: str

@api.post("/auth/register")
async def register(body: RegBody, response: Response):
    em = body.email.lower()
    if await db.users.find_one({"email": em}): raise HTTPException(400, "Email taken")
    doc = {"name": body.name, "email": em, "password_hash": hash_pw(body.password), "persona": None, "created_at": datetime.now(timezone.utc)}
    r = await db.users.insert_one(doc)
    uid = str(r.inserted_id)
    set_cookies(response, uid, em)
    return {"id": uid, "name": body.name, "email": em, "persona": None}

@api.post("/auth/login")
async def login(body: LoginBody, response: Response):
    em = body.email.lower()
    u = await db.users.find_one({"email": em})
    if not u or not verify_pw(body.password, u["password_hash"]): raise HTTPException(401, "Invalid credentials")
    uid = str(u["_id"])
    set_cookies(response, uid, em)
    return {"id": uid, "name": u["name"], "email": em, "persona": u.get("persona")}

@api.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/"); response.delete_cookie("refresh_token", path="/")
    return {"ok": True}

@api.get("/auth/me")
async def me(u: dict = Depends(current_user)):
    return u

# ═══════════════════ PERSONA ═══════════════════
@api.post("/persona/select")
async def select_persona(request: Request, u: dict = Depends(current_user)):
    body = await request.json()
    persona = body.get("persona")
    if persona not in ["individual", "shop_owner", "ca"]: raise HTTPException(400, "Invalid persona")
    await db.users.update_one({"_id": ObjectId(u["_id"])}, {"$set": {"persona": persona}})
    return {"persona": persona}

# ═══════════════════ INDIVIDUAL ENDPOINTS ═══════════════════
class TransBody(BaseModel):
    amount: float; category: str; type: str; description: Optional[str] = ""; date: str

@api.get("/individual/dashboard")
async def ind_dashboard(u: dict = Depends(current_user)):
    txns = await db.ind_transactions.find({"user_id": u["_id"]}, {"_id": 0}).to_list(10000)
    goals = await db.ind_goals.find({"user_id": u["_id"]}, {"_id": 0}).to_list(100)
    inc = sum(t["amount"] for t in txns if t["type"] == "income")
    exp = sum(t["amount"] for t in txns if t["type"] == "expense")
    savings_rate = round((inc - exp) / inc * 100, 1) if inc > 0 else 0
    # Monthly sparklines
    monthly = defaultdict(lambda: {"income": 0, "expense": 0})
    for t in txns:
        monthly[t["date"][:7]][t["type"]] += t["amount"]
    months = sorted(monthly.keys())[-6:]
    spark_inc = [monthly[m]["income"] for m in months]
    spark_exp = [monthly[m]["expense"] for m in months]
    # Category breakdown
    cats = defaultdict(float)
    for t in txns:
        if t["type"] == "expense": cats[t["category"]] += t["amount"]
    cat_breakdown = [{"name": k, "value": round(v, 2)} for k, v in sorted(cats.items(), key=lambda x: -x[1])]
    # Monthly series
    series = [{"month": m, "income": round(monthly[m]["income"], 2), "expenses": round(monthly[m]["expense"], 2)} for m in months]
    return {
        "income": round(inc, 2), "expenses": round(exp, 2), "savings_rate": savings_rate,
        "net_worth": round(inc - exp, 2),
        "sparkline_income": spark_inc, "sparkline_expenses": spark_exp,
        "category_breakdown": cat_breakdown, "monthly_series": series,
        "goals": goals, "transaction_count": len(txns)
    }

@api.get("/individual/transactions")
async def ind_get_txns(u: dict = Depends(current_user)):
    return await db.ind_transactions.find({"user_id": u["_id"]}, {"_id": 0}).sort("date", -1).to_list(1000)

@api.post("/individual/transactions")
async def ind_add_txn(body: TransBody, u: dict = Depends(current_user)):
    doc = {"id": str(ObjectId()), "user_id": u["_id"], "amount": body.amount, "category": body.category, "type": body.type, "description": body.description or "", "date": body.date, "created_at": datetime.now(timezone.utc).isoformat()}
    await db.ind_transactions.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api.delete("/individual/transactions/{tid}")
async def ind_del_txn(tid: str, u: dict = Depends(current_user)):
    r = await db.ind_transactions.delete_one({"id": tid, "user_id": u["_id"]})
    if r.deleted_count == 0: raise HTTPException(404, "Not found")
    return {"ok": True}

# Goals
class GoalBody(BaseModel):
    name: str; target: float; saved: Optional[float] = 0; deadline: Optional[str] = ""

@api.get("/individual/goals")
async def ind_get_goals(u: dict = Depends(current_user)):
    return await db.ind_goals.find({"user_id": u["_id"]}, {"_id": 0}).to_list(100)

@api.post("/individual/goals")
async def ind_add_goal(body: GoalBody, u: dict = Depends(current_user)):
    doc = {"id": str(ObjectId()), "user_id": u["_id"], "name": body.name, "target": body.target, "saved": body.saved or 0, "deadline": body.deadline or "", "created_at": datetime.now(timezone.utc).isoformat()}
    await db.ind_goals.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api.put("/individual/goals/{gid}")
async def ind_update_goal(gid: str, body: GoalBody, u: dict = Depends(current_user)):
    await db.ind_goals.update_one({"id": gid, "user_id": u["_id"]}, {"$set": {"name": body.name, "target": body.target, "saved": body.saved, "deadline": body.deadline}})
    return {"ok": True}

@api.delete("/individual/goals/{gid}")
async def ind_del_goal(gid: str, u: dict = Depends(current_user)):
    await db.ind_goals.delete_one({"id": gid, "user_id": u["_id"]})
    return {"ok": True}

# ═══════════════════ SHOP OWNER ENDPOINTS ═══════════════════
class LedgerBody(BaseModel):
    amount: float; category: str; note: Optional[str] = ""; entry_type: str  # "credit" or "debit"

@api.get("/shop/dashboard")
async def shop_dashboard(u: dict = Depends(current_user)):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    entries = await db.shop_ledger.find({"user_id": u["_id"]}, {"_id": 0}).sort("created_at", -1).to_list(10000)
    today_entries = [e for e in entries if e.get("date") == today]
    # Opening balance: sum of all entries before today
    past_entries = [e for e in entries if e.get("date", "") < today]
    opening = sum(e["amount"] if e["entry_type"] == "credit" else -e["amount"] for e in past_entries)
    today_credit = sum(e["amount"] for e in today_entries if e["entry_type"] == "credit")
    today_debit = sum(e["amount"] for e in today_entries if e["entry_type"] == "debit")
    closing = opening + today_credit - today_debit
    # Pending payments
    pending = await db.shop_pending.find({"user_id": u["_id"]}, {"_id": 0}).to_list(100)
    # Weekly data
    weekly = defaultdict(lambda: {"credit": 0, "debit": 0})
    for e in entries:
        d = e.get("date", "")
        weekly[d]["credit" if e["entry_type"] == "credit" else "debit"] += e["amount"]
    last7 = sorted(weekly.keys())[-7:]
    weekly_series = [{"date": d, "credit": round(weekly[d]["credit"], 2), "debit": round(weekly[d]["debit"], 2), "net": round(weekly[d]["credit"] - weekly[d]["debit"], 2)} for d in last7]
    # Category breakdown
    cats = defaultdict(float)
    for e in today_entries:
        if e["entry_type"] == "credit": cats[e["category"]] += e["amount"]
    top5 = sorted(cats.items(), key=lambda x: -x[1])[:5]
    return {
        "today": today, "opening_balance": round(opening, 2),
        "today_credit": round(today_credit, 2), "today_debit": round(today_debit, 2),
        "closing_balance": round(closing, 2),
        "today_entries": today_entries, "pending_payments": pending,
        "weekly_series": weekly_series,
        "top_categories": [{"name": k, "value": round(v, 2)} for k, v in top5],
        "total_revenue": round(sum(e["amount"] for e in entries if e["entry_type"] == "credit"), 2),
    }

@api.post("/shop/entry")
async def shop_add_entry(body: LedgerBody, u: dict = Depends(current_user)):
    if body.entry_type not in ["credit", "debit"]: raise HTTPException(400, "Must be credit or debit")
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    now = datetime.now(timezone.utc).strftime("%H:%M")
    doc = {"id": str(ObjectId()), "user_id": u["_id"], "amount": body.amount, "category": body.category, "note": body.note or "", "entry_type": body.entry_type, "date": today, "time": now, "created_at": datetime.now(timezone.utc).isoformat()}
    await db.shop_ledger.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api.delete("/shop/entry/{eid}")
async def shop_del_entry(eid: str, u: dict = Depends(current_user)):
    r = await db.shop_ledger.delete_one({"id": eid, "user_id": u["_id"]})
    if r.deleted_count == 0: raise HTTPException(404, "Not found")
    return {"ok": True}

@api.get("/shop/ledger")
async def shop_get_ledger(u: dict = Depends(current_user)):
    return await db.shop_ledger.find({"user_id": u["_id"]}, {"_id": 0}).sort("created_at", -1).to_list(5000)

# Pending payments
class PendingBody(BaseModel):
    name: str; amount: float; days_overdue: Optional[int] = 0

@api.get("/shop/pending")
async def shop_get_pending(u: dict = Depends(current_user)):
    return await db.shop_pending.find({"user_id": u["_id"]}, {"_id": 0}).to_list(100)

@api.post("/shop/pending")
async def shop_add_pending(body: PendingBody, u: dict = Depends(current_user)):
    doc = {"id": str(ObjectId()), "user_id": u["_id"], "name": body.name, "amount": body.amount, "days_overdue": body.days_overdue, "created_at": datetime.now(timezone.utc).isoformat()}
    await db.shop_pending.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api.delete("/shop/pending/{pid}")
async def shop_del_pending(pid: str, u: dict = Depends(current_user)):
    await db.shop_pending.delete_one({"id": pid, "user_id": u["_id"]})
    return {"ok": True}

# ═══════════════════ CA ENDPOINTS ═══════════════════
class ClientBody(BaseModel):
    name: str; business_type: str; status: Optional[str] = "on_track"; next_deadline: Optional[str] = ""

@api.get("/ca/dashboard")
async def ca_dashboard(u: dict = Depends(current_user)):
    clients = await db.ca_clients.find({"user_id": u["_id"]}, {"_id": 0}).to_list(500)
    tasks = await db.ca_tasks.find({"user_id": u["_id"]}, {"_id": 0}).to_list(1000)
    overdue = len([t for t in tasks if t.get("status") == "overdue"])
    pending = len([t for t in tasks if t.get("status") == "pending"])
    return {"clients": clients, "tasks": tasks, "active_clients": len(clients), "overdue_tasks": overdue, "pending_tasks": pending, "reports_due": overdue}

@api.get("/ca/clients")
async def ca_get_clients(u: dict = Depends(current_user)):
    return await db.ca_clients.find({"user_id": u["_id"]}, {"_id": 0}).to_list(500)

@api.post("/ca/clients")
async def ca_add_client(body: ClientBody, u: dict = Depends(current_user)):
    doc = {"id": str(ObjectId()), "user_id": u["_id"], "name": body.name, "business_type": body.business_type, "status": body.status, "next_deadline": body.next_deadline, "revenue_trend": [0, 0, 0], "last_activity": datetime.now(timezone.utc).isoformat(), "created_at": datetime.now(timezone.utc).isoformat()}
    await db.ca_clients.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api.delete("/ca/clients/{cid}")
async def ca_del_client(cid: str, u: dict = Depends(current_user)):
    await db.ca_clients.delete_one({"id": cid, "user_id": u["_id"]})
    return {"ok": True}

class TaskBody(BaseModel):
    title: str; client_name: Optional[str] = ""; deadline: Optional[str] = ""; status: Optional[str] = "pending"

@api.get("/ca/tasks")
async def ca_get_tasks(u: dict = Depends(current_user)):
    return await db.ca_tasks.find({"user_id": u["_id"]}, {"_id": 0}).to_list(1000)

@api.post("/ca/tasks")
async def ca_add_task(body: TaskBody, u: dict = Depends(current_user)):
    doc = {"id": str(ObjectId()), "user_id": u["_id"], "title": body.title, "client_name": body.client_name, "deadline": body.deadline, "status": body.status or "pending", "created_at": datetime.now(timezone.utc).isoformat()}
    await db.ca_tasks.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api.put("/ca/tasks/{tid}")
async def ca_update_task(tid: str, body: TaskBody, u: dict = Depends(current_user)):
    await db.ca_tasks.update_one({"id": tid, "user_id": u["_id"]}, {"$set": {"title": body.title, "client_name": body.client_name, "deadline": body.deadline, "status": body.status}})
    return {"ok": True}

@api.delete("/ca/tasks/{tid}")
async def ca_del_task(tid: str, u: dict = Depends(current_user)):
    await db.ca_tasks.delete_one({"id": tid, "user_id": u["_id"]})
    return {"ok": True}

# ═══════════════════ AI ENDPOINTS ═══════════════════
@api.post("/ai/insights")
async def ai_insights(request: Request, u: dict = Depends(current_user)):
    body = await request.json()
    persona = body.get("persona", "individual")
    context = body.get("context", "")
    prompts = {
        "individual": f"You are a friendly personal finance advisor for an Indian user. Analyze:\n{context}\nProvide 5 actionable tips in bullet points. Be encouraging. Use INR amounts.",
        "shop_owner": f"You are a sharp business advisor for an Indian shop owner. Analyze:\n{context}\nProvide 5 tactical recommendations to increase revenue and reduce costs. Use INR amounts.",
        "ca": f"You are an expert Indian Chartered Accountant advisor. Analyze:\n{context}\nProvide 5 professional recommendations on compliance, tax optimization, and client management."
    }
    try:
        chat = LlmChat(api_key=os.environ.get('EMERGENT_LLM_KEY'), session_id=f"capitalcare_{u['_id']}_{datetime.now(timezone.utc).timestamp()}", system_message="You are a professional Indian financial advisor.")
        chat.with_model("openai", "gpt-5.2")
        resp = await chat.send_message(UserMessage(text=prompts.get(persona, prompts["individual"])))
        # Store
        await db.ai_insights.insert_one({"user_id": u["_id"], "persona": persona, "insights": resp.strip(), "created_at": datetime.now(timezone.utc).isoformat()})
        return {"insights": resp.strip()}
    except Exception as e:
        raise HTTPException(500, f"AI error: {str(e)}")

@api.get("/ai/latest")
async def ai_latest(u: dict = Depends(current_user)):
    doc = await db.ai_insights.find({"user_id": u["_id"]}, {"_id": 0}).sort("created_at", -1).limit(1).to_list(1)
    if not doc: return {"has_insights": False}
    return {"has_insights": True, "insights": doc[0]["insights"], "created_at": doc[0]["created_at"]}

# ═══════════════════ AI CHAT ASSISTANT ═══════════════════
@api.post("/ai/chat")
async def ai_chat(request: Request, u: dict = Depends(current_user)):
    body = await request.json()
    message = body.get("message", "")
    persona = body.get("persona", "individual")
    if not message: raise HTTPException(400, "Message required")
    
    system_msgs = {
        "individual": "You are Capital Care AI, a warm and encouraging personal finance coach for Indian users. Help with budgeting, savings goals, investment basics, and tax deductions (80C, 80D, HRA). Use INR amounts. Keep responses concise (3-5 sentences).",
        "shop_owner": "You are Capital Care AI, a sharp business advisor for Indian shop owners. Help with inventory management, pricing strategies, cash flow optimization, GST compliance, and revenue growth tactics. Use INR amounts. Keep responses concise and actionable.",
        "ca": "You are Capital Care AI, an expert Indian CA assistant. Help with tax law interpretation (Income Tax Act, GST Act), compliance deadlines, TDS calculations, ITR filing strategy, and client advisory. Be precise and professional. Cite sections when relevant."
    }
    try:
        chat = LlmChat(api_key=os.environ.get('EMERGENT_LLM_KEY'), session_id=f"chat_{u['_id']}_{datetime.now(timezone.utc).timestamp()}", system_message=system_msgs.get(persona, system_msgs["individual"]))
        chat.with_model("openai", "gpt-5.2")
        resp = await chat.send_message(UserMessage(text=message))
        # Store chat history
        await db.ai_chat_history.insert_one({"user_id": u["_id"], "persona": persona, "message": message, "response": resp.strip(), "created_at": datetime.now(timezone.utc).isoformat()})
        return {"response": resp.strip()}
    except Exception as e:
        raise HTTPException(500, f"Chat error: {str(e)}")

@api.get("/ai/chat-history")
async def ai_chat_history(u: dict = Depends(current_user)):
    history = await db.ai_chat_history.find({"user_id": u["_id"]}, {"_id": 0}).sort("created_at", -1).limit(20).to_list(20)
    return list(reversed(history))

# ═══════════════════ CASH FLOW FORECAST ═══════════════════
@api.get("/forecast/{persona}")
async def cash_flow_forecast(persona: str, u: dict = Depends(current_user)):
    if persona == "individual":
        txns = await db.ind_transactions.find({"user_id": u["_id"]}, {"_id": 0}).to_list(10000)
        monthly = defaultdict(lambda: {"income": 0, "expense": 0})
        for t in txns:
            monthly[t["date"][:7]][t["type"]] += t["amount"]
        months = sorted(monthly.keys())
        if len(months) < 1:
            return {"forecast": [], "avg_income": 0, "avg_expense": 0}
        avg_inc = sum(monthly[m]["income"] for m in months) / max(len(months), 1)
        avg_exp = sum(monthly[m]["expense"] for m in months) / max(len(months), 1)
        # Project next 3 months
        forecast = []
        today = datetime.now(timezone.utc)
        for i in range(1, 4):
            d = today + timedelta(days=30*i)
            forecast.append({"month": d.strftime("%Y-%m"), "projected_income": round(avg_inc, 2), "projected_expenses": round(avg_exp, 2), "projected_savings": round(avg_inc - avg_exp, 2)})
        return {"forecast": forecast, "avg_income": round(avg_inc, 2), "avg_expense": round(avg_exp, 2)}
    
    elif persona == "shop_owner":
        entries = await db.shop_ledger.find({"user_id": u["_id"]}, {"_id": 0}).to_list(10000)
        daily = defaultdict(lambda: {"credit": 0, "debit": 0})
        for e in entries:
            daily[e.get("date", "")]["credit" if e["entry_type"] == "credit" else "debit"] += e["amount"]
        days = sorted(daily.keys())
        if len(days) < 1:
            return {"forecast_30": 0, "forecast_60": 0, "forecast_90": 0, "daily_avg_net": 0, "series": []}
        daily_nets = [daily[d]["credit"] - daily[d]["debit"] for d in days]
        avg_net = sum(daily_nets) / max(len(daily_nets), 1)
        return {
            "forecast_30": round(avg_net * 30, 2), "forecast_60": round(avg_net * 60, 2), "forecast_90": round(avg_net * 90, 2),
            "daily_avg_net": round(avg_net, 2),
            "series": [{"day": i+1, "projected": round(avg_net * (i+1), 2)} for i in range(90)]
        }
    return {"forecast": []}

# ═══════════════════ PROACTIVE ALERTS ═══════════════════
@api.get("/alerts/{persona}")
async def get_alerts(persona: str, u: dict = Depends(current_user)):
    alerts = []
    if persona == "individual":
        txns = await db.ind_transactions.find({"user_id": u["_id"]}, {"_id": 0}).to_list(10000)
        # Category spending analysis
        cats = defaultdict(list)
        for t in txns:
            if t["type"] == "expense":
                cats[t["category"]].append(t["amount"])
        for cat, amounts in cats.items():
            if len(amounts) >= 3:
                avg = sum(amounts[:-1]) / (len(amounts) - 1)
                if amounts[-1] > avg * 1.5 and avg > 0:
                    alerts.append({"type": "spending_spike", "severity": "warning", "message": f"Your last {cat} expense (₹{amounts[-1]:,.0f}) is {((amounts[-1]/avg - 1)*100):.0f}% above your average"})
        # Savings rate
        inc = sum(t["amount"] for t in txns if t["type"] == "income")
        exp = sum(t["amount"] for t in txns if t["type"] == "expense")
        if inc > 0 and (inc - exp) / inc < 0.2:
            alerts.append({"type": "low_savings", "severity": "info", "message": f"Your savings rate is {((inc-exp)/inc*100):.0f}%. Aim for at least 20% to build an emergency fund."})
        # Goals behind schedule
        goals = await db.ind_goals.find({"user_id": u["_id"]}, {"_id": 0}).to_list(100)
        for g in goals:
            if g.get("deadline") and g["target"] > 0:
                pct = g["saved"] / g["target"] * 100
                if pct < 50:
                    alerts.append({"type": "goal_behind", "severity": "info", "message": f"'{g['name']}' is only {pct:.0f}% funded. Consider increasing your monthly savings."})
    
    elif persona == "shop_owner":
        pending = await db.shop_pending.find({"user_id": u["_id"]}, {"_id": 0}).to_list(100)
        overdue_count = len([p for p in pending if p.get("days_overdue", 0) > 7])
        if overdue_count > 0:
            total_overdue = sum(p["amount"] for p in pending if p.get("days_overdue", 0) > 7)
            alerts.append({"type": "overdue_payments", "severity": "warning", "message": f"{overdue_count} payments overdue totaling ₹{total_overdue:,.0f}. Send reminders today."})
        entries = await db.shop_ledger.find({"user_id": u["_id"]}, {"_id": 0}).to_list(10000)
        # Weekday analysis
        from collections import Counter
        weekday_rev = Counter()
        for e in entries:
            if e["entry_type"] == "credit":
                try:
                    dt = datetime.strptime(e["date"], "%Y-%m-%d")
                    weekday_rev[dt.strftime("%A")] += e["amount"]
                except: pass
        if weekday_rev:
            avg_rev = sum(weekday_rev.values()) / max(len(weekday_rev), 1)
            for day, rev in weekday_rev.items():
                if rev < avg_rev * 0.6:
                    alerts.append({"type": "low_day", "severity": "info", "message": f"{day} sales are {((1 - rev/avg_rev)*100):.0f}% below average. Consider a special offer."})
    
    elif persona == "ca":
        tasks = await db.ca_tasks.find({"user_id": u["_id"], "status": {"$in": ["pending", "overdue"]}}, {"_id": 0}).to_list(1000)
        if len(tasks) > 5:
            alerts.append({"type": "task_overload", "severity": "warning", "message": f"You have {len(tasks)} pending tasks. Prioritize by deadline."})
        clients = await db.ca_clients.find({"user_id": u["_id"], "status": "overdue"}, {"_id": 0}).to_list(100)
        if clients:
            names = ", ".join([c["name"] for c in clients[:3]])
            alerts.append({"type": "client_overdue", "severity": "warning", "message": f"Clients overdue: {names}. Follow up immediately."})
    
    if not alerts:
        alerts.append({"type": "all_good", "severity": "success", "message": "Everything looks great! Keep up the good work."})
    return alerts

# ═══════════════════ EXPORT PDF ═══════════════════
@api.get("/export/individual/pdf")
async def export_ind_pdf(u: dict = Depends(current_user)):
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    txns = await db.ind_transactions.find({"user_id": u["_id"]}, {"_id": 0}).sort("date", -1).to_list(1000)
    inc = sum(t["amount"] for t in txns if t["type"] == "income")
    exp = sum(t["amount"] for t in txns if t["type"] == "expense")
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter)
    styles = getSampleStyleSheet()
    elems = []
    elems.append(Paragraph("Capital Care AI — Financial Report", styles['Title']))
    elems.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
    elems.append(Spacer(1, 0.3*inch))
    summary = [["Metric","Amount"],["Total Income",f"₹{inc:,.2f}"],["Total Expenses",f"₹{exp:,.2f}"],["Net Savings",f"₹{inc-exp:,.2f}"]]
    t = Table(summary, colWidths=[3*inch, 2*inch])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#0F172A')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),0.5,colors.grey),('FONTNAME',(0,0),(-1,0),'Helvetica-Bold')]))
    elems.append(t)
    elems.append(Spacer(1, 0.3*inch))
    elems.append(Paragraph("Transactions", styles['Heading2']))
    rows = [["Date","Type","Category","Amount","Note"]]
    for tx in txns[:50]:
        rows.append([tx["date"],tx["type"].title(),tx["category"],f"₹{tx['amount']:,.2f}",tx.get("description","")[:25]])
    t2 = Table(rows, colWidths=[1.1*inch,0.7*inch,1.1*inch,1*inch,2*inch])
    t2.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#0F172A')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),0.5,colors.grey),('FONTSIZE',(0,0),(-1,-1),8)]))
    elems.append(t2)
    doc.build(elems)
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=capital_care_report_{datetime.now().strftime('%Y%m%d')}.pdf"})

@api.get("/export/individual/csv")
async def export_ind_csv(u: dict = Depends(current_user)):
    txns = await db.ind_transactions.find({"user_id": u["_id"]}, {"_id": 0}).sort("date", -1).to_list(10000)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Date","Type","Category","Amount","Description"])
    for t in txns:
        writer.writerow([t["date"],t["type"].title(),t["category"],f"{t['amount']:.2f}",t.get("description","")])
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=transactions_{datetime.now().strftime('%Y%m%d')}.csv"})


# ═══════════════════ SMS PARSER ═══════════════════
@api.post("/sms/parse")
async def parse_sms(request: Request):
    body = await request.json()
    sms_text = body.get("text", "")
    if not sms_text: raise HTTPException(400, "No SMS text")
    # Simple regex-based parser for Indian bank SMS
    import re
    result = {"amount": None, "type": None, "merchant": None, "parsed": False}
    # Patterns: "debited" / "credited" / "spent" / "received"
    amt_match = re.search(r'(?:Rs\.?|INR|₹)\s*([\d,]+\.?\d*)', sms_text, re.IGNORECASE)
    if amt_match:
        result["amount"] = float(amt_match.group(1).replace(",", ""))
        result["parsed"] = True
    if re.search(r'debit|spent|paid|purchase|withdrawn', sms_text, re.IGNORECASE):
        result["type"] = "debit"
    elif re.search(r'credit|received|refund|deposit', sms_text, re.IGNORECASE):
        result["type"] = "credit"
    # Merchant
    merchant_match = re.search(r'(?:at|to|from|by)\s+([A-Za-z0-9\s]+?)(?:\s+on|\s+ref|\s+UPI|\.|$)', sms_text, re.IGNORECASE)
    if merchant_match: result["merchant"] = merchant_match.group(1).strip()
    return result

# ═══════════════════ PRICING ═══════════════════
@api.get("/pricing")
async def get_pricing():
    return [
        {"tier": "individual", "name": "Individual", "price": 99, "period": "month", "features": ["Expense tracking", "Savings goals", "AI insights", "Monthly reports", "Bank SMS parsing"]},
        {"tier": "shop_owner", "name": "Shop Owner", "price": 299, "period": "month", "features": ["Cash ledger", "Sales tracking", "P&L reports", "GST summary", "UPI auto-detect", "Inventory basics"]},
        {"tier": "ca", "name": "Accountant (CA)", "price": 999, "period": "month", "features": ["Unlimited clients", "Full financial statements", "GST/TDS/ITR prep", "Client portal", "Bulk export", "Multi-currency"]},
    ]

# ═══════════════════ STARTUP ═══════════════════
@app.on_event("startup")
async def startup():
    await db.users.create_index("email", unique=True)
    await db.ind_transactions.create_index([("user_id", 1), ("date", -1)])
    await db.shop_ledger.create_index([("user_id", 1), ("date", -1)])
    await db.ca_clients.create_index("user_id")
    await db.ca_tasks.create_index("user_id")
    # Seed admin
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@capitalcare.com")
    admin_pw = os.environ.get("ADMIN_PASSWORD", "Admin@123")
    if not await db.users.find_one({"email": admin_email}):
        await db.users.insert_one({"email": admin_email, "password_hash": hash_pw(admin_pw), "name": "Admin", "persona": None, "created_at": datetime.now(timezone.utc)})
    # Write creds
    Path("/app/memory").mkdir(exist_ok=True)
    Path("/app/memory/test_credentials.md").write_text(f"# Capital Care AI Credentials\n- Email: {admin_email}\n- Password: {admin_pw}\n- Endpoints: /api/auth/login, /api/auth/register, /api/persona/select\n")

app.include_router(api)
app.add_middleware(CORSMiddleware, allow_credentials=True, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
logging.basicConfig(level=logging.INFO)

@app.on_event("shutdown")
async def shutdown(): client.close()
