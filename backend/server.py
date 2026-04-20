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
import re
import math
from emergentintegrations.llm.chat import LlmChat, UserMessage
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest

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
    doc = {"name": body.name, "email": em, "password_hash": hash_pw(body.password), "persona": None, "plan": "free", "subscription_status": "inactive", "created_at": datetime.now(timezone.utc)}
    r = await db.users.insert_one(doc)
    uid = str(r.inserted_id)
    set_cookies(response, uid, em)
    return {"id": uid, "name": body.name, "email": em, "persona": None, "plan": "free", "subscription_status": "inactive"}

@api.post("/auth/login")
async def login(body: LoginBody, response: Response):
    em = body.email.lower()
    u = await db.users.find_one({"email": em})
    if not u or not verify_pw(body.password, u["password_hash"]): raise HTTPException(401, "Invalid credentials")
    uid = str(u["_id"])
    set_cookies(response, uid, em)
    return {"id": uid, "name": u["name"], "email": em, "persona": u.get("persona"), "plan": u.get("plan", "free"), "subscription_status": u.get("subscription_status", "inactive")}

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

# ═══════════════════ BUDGETING ═══════════════════
class BudgetCapBody(BaseModel):
    category: str
    limit: float
    rollover: Optional[bool] = False

@api.get("/budgets")
async def get_budgets(u: dict = Depends(current_user)):
    budgets = await db.budget_caps.find({"user_id": u["_id"]}, {"_id": 0}).to_list(100)
    current_month = datetime.now(timezone.utc).strftime("%Y-%m")
    for b in budgets:
        txns = await db.ind_transactions.find({"user_id": u["_id"], "type": "expense", "category": b["category"], "date": {"$regex": f"^{current_month}"}}).to_list(1000)
        spent = sum(t["amount"] for t in txns)
        b["spent"] = round(spent, 2)
        b["remaining"] = round(b["limit"] - spent, 2)
        b["percentage"] = round((spent / b["limit"]) * 100, 1) if b["limit"] > 0 else 0
        b["status"] = "exceeded" if b["percentage"] >= 100 else "warning" if b["percentage"] >= 80 else "safe"
    return budgets

@api.post("/budgets")
async def create_budget(body: BudgetCapBody, u: dict = Depends(current_user)):
    existing = await db.budget_caps.find_one({"user_id": u["_id"], "category": body.category})
    if existing:
        await db.budget_caps.update_one({"user_id": u["_id"], "category": body.category}, {"$set": {"limit": body.limit, "rollover": body.rollover}})
        return {"ok": True, "updated": True}
    doc = {"id": str(ObjectId()), "user_id": u["_id"], "category": body.category, "limit": body.limit, "rollover": body.rollover or False, "created_at": datetime.now(timezone.utc).isoformat()}
    await db.budget_caps.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api.delete("/budgets/{bid}")
async def delete_budget(bid: str, u: dict = Depends(current_user)):
    await db.budget_caps.delete_one({"id": bid, "user_id": u["_id"]})
    return {"ok": True}

# ═══════════════════ AUTO-SAVE RULES ═══════════════════
class AutoSaveRuleBody(BaseModel):
    rule_type: str  # "roundup", "percentage", "fixed"
    value: float  # roundup to nearest X, X% of income, fixed ₹ amount
    target_goal_id: Optional[str] = ""
    active: Optional[bool] = True

@api.get("/autosave-rules")
async def get_autosave_rules(u: dict = Depends(current_user)):
    return await db.autosave_rules.find({"user_id": u["_id"]}, {"_id": 0}).to_list(50)

@api.post("/autosave-rules")
async def create_autosave_rule(body: AutoSaveRuleBody, u: dict = Depends(current_user)):
    doc = {"id": str(ObjectId()), "user_id": u["_id"], "rule_type": body.rule_type, "value": body.value, "target_goal_id": body.target_goal_id or "", "active": body.active, "created_at": datetime.now(timezone.utc).isoformat()}
    await db.autosave_rules.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api.delete("/autosave-rules/{rid}")
async def delete_autosave_rule(rid: str, u: dict = Depends(current_user)):
    await db.autosave_rules.delete_one({"id": rid, "user_id": u["_id"]})
    return {"ok": True}

# ═══════════════════ LOAN & EMI TRACKER ═══════════════════
class LoanBody(BaseModel):
    loan_type: str  # Home/Car/Personal/Education/Gold
    principal: float
    interest_rate: float
    tenure_months: int
    emi_amount: float
    start_date: str
    bank_name: Optional[str] = ""

@api.get("/loans")
async def get_loans(u: dict = Depends(current_user)):
    loans = await db.loans.find({"user_id": u["_id"]}, {"_id": 0}).to_list(50)
    for loan in loans:
        # Calculate amortization summary
        r = loan["interest_rate"] / 12 / 100
        n = loan["tenure_months"]
        emi = loan["emi_amount"]
        start = datetime.strptime(loan["start_date"], "%Y-%m-%d")
        months_elapsed = max(0, (datetime.now(timezone.utc).year - start.year) * 12 + datetime.now(timezone.utc).month - start.month)
        emis_paid = min(months_elapsed, n)
        total_paid = emi * emis_paid
        # Approximate remaining principal
        if r > 0:
            total_interest = sum([(loan["principal"] * ((1 + r) ** i) - ((((1 + r) ** i) - 1) / r) * emi) * r for i in range(1, emis_paid + 1)]) if emis_paid > 0 else 0
        else:
            total_interest = 0
        principal_paid = total_paid - total_interest
        loan["emis_paid"] = emis_paid
        loan["emis_total"] = n
        loan["principal_remaining"] = round(max(0, loan["principal"] - principal_paid), 2)
        loan["total_interest_paid"] = round(max(0, total_interest), 2)
        loan["next_emi_date"] = (start + timedelta(days=30 * (emis_paid + 1))).strftime("%Y-%m-%d") if emis_paid < n else None
    return loans

@api.post("/loans")
async def add_loan(body: LoanBody, u: dict = Depends(current_user)):
    doc = {"id": str(ObjectId()), "user_id": u["_id"], **body.dict(), "created_at": datetime.now(timezone.utc).isoformat()}
    await db.loans.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api.delete("/loans/{lid}")
async def del_loan(lid: str, u: dict = Depends(current_user)):
    await db.loans.delete_one({"id": lid, "user_id": u["_id"]})
    return {"ok": True}

@api.get("/loans/{lid}/amortization")
async def loan_amortization(lid: str, u: dict = Depends(current_user)):
    loan = await db.loans.find_one({"id": lid, "user_id": u["_id"]}, {"_id": 0})
    if not loan: raise HTTPException(404, "Loan not found")
    r = loan["interest_rate"] / 12 / 100
    n = loan["tenure_months"]
    emi = loan["emi_amount"]
    balance = loan["principal"]
    schedule = []
    for i in range(1, n + 1):
        interest = round(balance * r, 2) if r > 0 else 0
        principal = round(emi - interest, 2)
        balance = round(max(0, balance - principal), 2)
        schedule.append({"month": i, "emi": emi, "principal": principal, "interest": interest, "balance": balance})
    return schedule

@api.post("/loans/{lid}/prepay-simulate")
async def prepay_simulate(lid: str, request: Request, u: dict = Depends(current_user)):
    body = await request.json()
    extra = body.get("amount", 0)
    loan = await db.loans.find_one({"id": lid, "user_id": u["_id"]}, {"_id": 0})
    if not loan: raise HTTPException(404, "Loan not found")
    r = loan["interest_rate"] / 12 / 100
    emi = loan["emi_amount"]
    # Without prepayment
    n_orig = loan["tenure_months"]
    total_orig = emi * n_orig
    # With prepayment (reduce balance)
    balance = loan["principal"] - extra
    months = 0
    total_new = extra
    while balance > 0 and months < 600:
        interest = balance * r if r > 0 else 0
        principal = emi - interest
        if principal <= 0: break
        balance -= principal
        total_new += emi
        months += 1
    return {"months_saved": max(0, n_orig - months), "interest_saved": round(max(0, total_orig - total_new), 2), "new_tenure": months}

# ═══════════════════ CREDIT CARD MANAGER ═══════════════════
class CreditCardBody(BaseModel):
    bank: str
    card_name: str
    credit_limit: float
    statement_date: int  # day of month
    due_date: int
    outstanding: Optional[float] = 0
    reward_points: Optional[int] = 0

@api.get("/credit-cards")
async def get_credit_cards(u: dict = Depends(current_user)):
    cards = await db.credit_cards.find({"user_id": u["_id"]}, {"_id": 0}).to_list(20)
    total_limit = sum(c["credit_limit"] for c in cards)
    total_outstanding = sum(c.get("outstanding", 0) for c in cards)
    utilization = round((total_outstanding / total_limit) * 100, 1) if total_limit > 0 else 0
    for c in cards:
        c["utilization"] = round((c.get("outstanding", 0) / c["credit_limit"]) * 100, 1) if c["credit_limit"] > 0 else 0
        c["available"] = round(c["credit_limit"] - c.get("outstanding", 0), 2)
    return {"cards": cards, "total_utilization": utilization, "total_limit": total_limit, "total_outstanding": total_outstanding}

@api.post("/credit-cards")
async def add_credit_card(body: CreditCardBody, u: dict = Depends(current_user)):
    doc = {"id": str(ObjectId()), "user_id": u["_id"], **body.dict(), "created_at": datetime.now(timezone.utc).isoformat()}
    await db.credit_cards.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api.delete("/credit-cards/{cid}")
async def del_credit_card(cid: str, u: dict = Depends(current_user)):
    await db.credit_cards.delete_one({"id": cid, "user_id": u["_id"]})
    return {"ok": True}

# ═══════════════════ FINANCIAL HEALTH SCORE ═══════════════════
@api.get("/health-score")
async def get_health_score(u: dict = Depends(current_user)):
    txns = await db.ind_transactions.find({"user_id": u["_id"]}, {"_id": 0}).to_list(10000)
    goals = await db.ind_goals.find({"user_id": u["_id"]}, {"_id": 0}).to_list(100)
    loans = await db.loans.find({"user_id": u["_id"]}, {"_id": 0}).to_list(50)
    budgets = await db.budget_caps.find({"user_id": u["_id"]}, {"_id": 0}).to_list(100)
    
    inc = sum(t["amount"] for t in txns if t["type"] == "income")
    exp = sum(t["amount"] for t in txns if t["type"] == "expense")
    
    # Savings rate (25 pts)
    savings_rate = (inc - exp) / inc if inc > 0 else 0
    sr_score = min(25, int(savings_rate * 100))
    
    # Debt-to-income (25 pts)
    monthly_emi = sum(l.get("emi_amount", 0) for l in loans)
    monthly_inc = inc / max(len(set(t["date"][:7] for t in txns if t["type"] == "income")), 1)
    dti = monthly_emi / monthly_inc if monthly_inc > 0 else 0
    dti_score = max(0, 25 - int(dti * 50))
    
    # Emergency fund (20 pts)
    monthly_exp = exp / max(len(set(t["date"][:7] for t in txns if t["type"] == "expense")), 1)
    emergency_goals = [g for g in goals if 'emergency' in g.get("name", "").lower()]
    ef_saved = sum(g.get("saved", 0) for g in emergency_goals)
    ef_months = ef_saved / monthly_exp if monthly_exp > 0 else 0
    ef_score = min(20, int(ef_months * 3.33))
    
    # Budget adherence (15 pts)
    if budgets:
        current_month = datetime.now(timezone.utc).strftime("%Y-%m")
        adherent = 0
        for b in budgets:
            spent = sum(t["amount"] for t in txns if t["type"] == "expense" and t["category"] == b["category"] and t["date"].startswith(current_month))
            if spent <= b["limit"]: adherent += 1
        ba_score = int((adherent / len(budgets)) * 15)
    else:
        ba_score = 8
    
    # Investment consistency (15 pts)
    inv_score = min(15, len(goals) * 3)
    
    total = sr_score + dti_score + ef_score + ba_score + inv_score
    
    tips = []
    if savings_rate < 0.2: tips.append("Aim to save at least 20% of your income each month.")
    if dti > 0.4: tips.append("Your debt-to-income ratio is high. Focus on reducing EMI burden.")
    if ef_months < 3: tips.append("Build your emergency fund to cover at least 3 months of expenses.")
    if not tips: tips.append("Great financial health! Keep up your disciplined approach.")
    
    return {"score": min(100, total), "breakdown": {"savings_rate": sr_score, "debt_to_income": dti_score, "emergency_fund": ef_score, "budget_adherence": ba_score, "investment_consistency": inv_score}, "tips": tips[:3]}

# ═══════════════════ DAILY SPEND LIMIT ═══════════════════
@api.get("/daily-limit")
async def get_daily_limit(u: dict = Depends(current_user)):
    config = await db.daily_limits.find_one({"user_id": u["_id"]}, {"_id": 0})
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    txns = await db.ind_transactions.find({"user_id": u["_id"], "type": "expense", "date": today}).to_list(100)
    spent_today = sum(t["amount"] for t in txns)
    limit = config.get("limit", 0) if config else 0
    return {"limit": limit, "spent_today": round(spent_today, 2), "remaining": round(max(0, limit - spent_today), 2), "percentage": round((spent_today / limit) * 100, 1) if limit > 0 else 0}

@api.post("/daily-limit")
async def set_daily_limit(request: Request, u: dict = Depends(current_user)):
    body = await request.json()
    limit = body.get("limit", 0)
    await db.daily_limits.update_one({"user_id": u["_id"]}, {"$set": {"limit": limit}}, upsert=True)
    return {"ok": True}

# ═══════════════════ WEEKLY DIGEST ═══════════════════
@api.get("/weekly-digest")
async def get_weekly_digest(u: dict = Depends(current_user)):
    today = datetime.now(timezone.utc)
    week_ago = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    two_weeks_ago = (today - timedelta(days=14)).strftime("%Y-%m-%d")
    today_str = today.strftime("%Y-%m-%d")
    
    this_week = await db.ind_transactions.find({"user_id": u["_id"], "date": {"$gte": week_ago, "$lte": today_str}}).to_list(1000)
    last_week = await db.ind_transactions.find({"user_id": u["_id"], "date": {"$gte": two_weeks_ago, "$lt": week_ago}}).to_list(1000)
    
    tw_spent = sum(t["amount"] for t in this_week if t["type"] == "expense")
    lw_spent = sum(t["amount"] for t in last_week if t["type"] == "expense")
    tw_saved = sum(t["amount"] for t in this_week if t["type"] == "income") - tw_spent
    
    cats = defaultdict(float)
    for t in this_week:
        if t["type"] == "expense": cats[t["category"]] += t["amount"]
    top3 = sorted(cats.items(), key=lambda x: -x[1])[:3]
    biggest = max(this_week, key=lambda t: t["amount"]) if this_week else None
    
    change = round(((tw_spent - lw_spent) / lw_spent) * 100, 1) if lw_spent > 0 else 0
    
    return {
        "total_spent": round(tw_spent, 2), "total_saved": round(tw_saved, 2),
        "top_categories": [{"name": c, "amount": round(a, 2)} for c, a in top3],
        "biggest_transaction": {"category": biggest["category"], "amount": biggest["amount"], "date": biggest["date"]} if biggest else None,
        "vs_last_week": change,
        "comparison": "better" if tw_spent < lw_spent else "worse" if tw_spent > lw_spent else "same"
    }

# ═══════════════════ SUBSCRIPTION DETECTOR ═══════════════════
@api.get("/subscriptions")
async def detect_subscriptions(u: dict = Depends(current_user)):
    txns = await db.ind_transactions.find({"user_id": u["_id"], "type": "expense"}, {"_id": 0}).sort("date", -1).to_list(10000)
    # Find recurring charges (same category + similar amount appearing monthly)
    recurring = defaultdict(list)
    for t in txns:
        key = f"{t['category']}_{t.get('description', '')}"
        recurring[key].append(t)
    
    subs = []
    for key, entries in recurring.items():
        if len(entries) >= 2:
            amounts = [e["amount"] for e in entries]
            avg = sum(amounts) / len(amounts)
            if all(abs(a - avg) < avg * 0.15 for a in amounts):  # within 15% variance
                subs.append({
                    "name": entries[0].get("description") or entries[0]["category"],
                    "category": entries[0]["category"],
                    "amount": round(avg, 2),
                    "frequency": "monthly",
                    "annual_cost": round(avg * 12, 2),
                    "last_charged": entries[0]["date"],
                    "occurrences": len(entries)
                })
    
    total_monthly = sum(s["amount"] for s in subs)
    return {"subscriptions": subs, "total_monthly": round(total_monthly, 2), "total_annual": round(total_monthly * 12, 2)}

# ═══════════════════ STRIPE PAYMENTS ═══════════════════
PLANS = {
    "pro_monthly": {"name": "Pro Monthly", "amount": 9.99, "currency": "usd", "interval": "month"},
    "pro_yearly": {"name": "Pro Yearly", "amount": 95.99, "currency": "usd", "interval": "year"},
    "elite_monthly": {"name": "Elite Monthly", "amount": 19.99, "currency": "usd", "interval": "month"},
    "elite_yearly": {"name": "Elite Yearly", "amount": 191.99, "currency": "usd", "interval": "year"},
}

@api.post("/payments/checkout")
async def create_checkout(request: Request, u: dict = Depends(current_user)):
    body = await request.json()
    plan_id = body.get("plan_id")
    origin_url = body.get("origin_url", "")
    
    if plan_id not in PLANS:
        raise HTTPException(400, "Invalid plan")
    
    plan = PLANS[plan_id]
    success_url = f"{origin_url}/payment-success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{origin_url}/pricing"
    
    api_key = os.environ.get("STRIPE_API_KEY")
    host_url = str(request.base_url)
    webhook_url = f"{host_url}api/webhook/stripe"
    
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)
    
    checkout_req = CheckoutSessionRequest(
        amount=float(plan["amount"]),
        currency=plan["currency"],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"user_id": u["_id"], "plan_id": plan_id, "user_email": u.get("email", "")}
    )
    
    session = await stripe_checkout.create_checkout_session(checkout_req)
    
    # Store payment transaction
    await db.payment_transactions.insert_one({
        "session_id": session.session_id,
        "user_id": u["_id"],
        "plan_id": plan_id,
        "amount": plan["amount"],
        "currency": plan["currency"],
        "payment_status": "initiated",
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    return {"url": session.url, "session_id": session.session_id}

@api.get("/payments/status/{session_id}")
async def payment_status(session_id: str, u: dict = Depends(current_user)):
    api_key = os.environ.get("STRIPE_API_KEY")
    host_url = "https://example.com"
    webhook_url = f"{host_url}/api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url=webhook_url)
    
    status = await stripe_checkout.get_checkout_status(session_id)
    
    # Update payment record
    tx = await db.payment_transactions.find_one({"session_id": session_id})
    if tx and tx.get("payment_status") != "paid":
        new_status = "paid" if status.payment_status == "paid" else status.payment_status
        await db.payment_transactions.update_one(
            {"session_id": session_id},
            {"$set": {"payment_status": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        # If paid, upgrade user
        if new_status == "paid":
            plan_id = tx.get("plan_id", "")
            plan_tier = "pro" if "pro" in plan_id else "elite" if "elite" in plan_id else "free"
            await db.users.update_one({"_id": ObjectId(tx["user_id"])}, {"$set": {"plan": plan_tier, "plan_id": plan_id}})
    
    return {"status": status.status, "payment_status": status.payment_status, "amount": status.amount_total, "currency": status.currency}

@api.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    body = await request.body()
    sig = request.headers.get("Stripe-Signature", "")
    api_key = os.environ.get("STRIPE_API_KEY")
    stripe_checkout = StripeCheckout(api_key=api_key, webhook_url="")
    try:
        event = await stripe_checkout.handle_webhook(body, sig)
        if event.payment_status == "paid":
            # 1) Our own checkout session path (has metadata)
            metadata = getattr(event, "metadata", {}) or {}
            plan_id = metadata.get("plan_id", "")
            user_id = metadata.get("user_id", "")
            user_email = metadata.get("user_email", "")
            # 2) Fallback: direct Stripe payment link (no metadata). Match by customer email.
            if not user_email:
                user_email = getattr(event, "customer_email", "") or getattr(event, "email", "") or ""
            # Determine plan tier
            plan_tier = None
            if plan_id:
                plan_tier = "pro" if "pro" in plan_id else "elite" if "elite" in plan_id else None
            if not plan_tier:
                # Use amount_total (cents) to decide: 499 => pro, 999 => elite
                amount_cents = int((getattr(event, "amount_total", 0) or 0))
                if amount_cents == 499: plan_tier = "pro"
                elif amount_cents == 999: plan_tier = "elite"
                # Yearly fallback
                elif amount_cents in (9599, 4790, 5988): plan_tier = "pro"
                elif amount_cents in (19199, 9590, 11988): plan_tier = "elite"
            if not plan_tier:
                logging.warning(f"Stripe webhook: could not determine plan for session {event.session_id}")
                return {"ok": True}
            # Update transaction log if exists
            await db.payment_transactions.update_one({"session_id": event.session_id}, {"$set": {"payment_status": "paid", "plan_tier": plan_tier}}, upsert=True)
            # Update user
            old_plan = None
            if user_id:
                old = await db.users.find_one({"_id": ObjectId(user_id)})
                old_plan = (old or {}).get("plan", "free")
                await db.users.update_one({"_id": ObjectId(user_id)}, {"$set": {"plan": plan_tier, "subscription_status": "active", "plan_updated_at": datetime.now(timezone.utc).isoformat()}})
            elif user_email:
                old = await db.users.find_one({"email": user_email.lower()})
                if old:
                    old_plan = old.get("plan", "free")
                    await db.users.update_one({"_id": old["_id"]}, {"$set": {"plan": plan_tier, "subscription_status": "active", "plan_updated_at": datetime.now(timezone.utc).isoformat()}})
            # Audit log
            await db.admin_audit_log.insert_one({
                "event": "plan_change",
                "user_email": user_email,
                "old_plan": old_plan, "new_plan": plan_tier,
                "stripe_session_id": event.session_id,
                "amount": getattr(event, "amount_total", 0),
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
        return {"ok": True}
    except Exception as e:
        logging.error(f"Webhook error: {e}")
        return {"ok": False}

# Manual sync endpoint — user calls this after returning from Stripe payment link.
# Trusts the logged-in user's email, checks Stripe for any recent paid session,
# or (fallback) allows plan refresh when caller passes a confirmed session_id.
@api.post("/user/refresh-plan")
async def refresh_plan(request: Request, u: dict = Depends(current_user)):
    # Re-read user from DB (in case webhook already updated)
    fresh = await db.users.find_one({"_id": ObjectId(u["_id"])})
    if not fresh: raise HTTPException(404, "User not found")
    return {"plan": fresh.get("plan", "free"), "subscription_status": fresh.get("subscription_status", "inactive")}

@api.get("/user/plan")
async def get_user_plan(u: dict = Depends(current_user)):
    return {"plan": u.get("plan", "free")}


# ═══════════════════ PHASE 2: INVESTMENTS ═══════════════════
class InvestmentBody(BaseModel):
    asset_type: str  # stock, mutual_fund, gold, fd, rd, crypto
    name: str  # ticker/fund name/metal type
    quantity: float
    buy_price: float  # per unit
    current_price: Optional[float] = 0  # per unit
    purchase_date: str
    notes: Optional[str] = ""

@api.get("/investments")
async def get_investments(u: dict = Depends(current_user)):
    items = await db.investments.find({"user_id": u["_id"]}, {"_id": 0}).to_list(500)
    for it in items:
        buy_total = it["quantity"] * it["buy_price"]
        cur_total = it["quantity"] * (it.get("current_price") or it["buy_price"])
        gain = cur_total - buy_total
        it["invested"] = round(buy_total, 2)
        it["current_value"] = round(cur_total, 2)
        it["gain_loss"] = round(gain, 2)
        it["gain_pct"] = round((gain / buy_total) * 100, 2) if buy_total > 0 else 0
    invested = sum(i["invested"] for i in items)
    cur_value = sum(i["current_value"] for i in items)
    # Allocation by asset type
    alloc = defaultdict(float)
    for i in items:
        alloc[i["asset_type"]] += i["current_value"]
    allocation = [{"asset_type": k, "value": round(v, 2), "pct": round((v/cur_value)*100, 1) if cur_value>0 else 0} for k, v in alloc.items()]
    return {
        "items": items,
        "total_invested": round(invested, 2),
        "total_current": round(cur_value, 2),
        "total_gain": round(cur_value - invested, 2),
        "gain_pct": round(((cur_value - invested) / invested) * 100, 2) if invested > 0 else 0,
        "allocation": allocation,
    }

@api.post("/investments")
async def add_investment(body: InvestmentBody, u: dict = Depends(current_user)):
    doc = {"id": str(ObjectId()), "user_id": u["_id"], **body.dict(), "created_at": datetime.now(timezone.utc).isoformat()}
    if not doc.get("current_price"): doc["current_price"] = doc["buy_price"]
    await db.investments.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api.patch("/investments/{iid}")
async def update_investment(iid: str, request: Request, u: dict = Depends(current_user)):
    body = await request.json()
    updatable = {k: v for k, v in body.items() if k in {"quantity", "buy_price", "current_price", "name", "notes"}}
    if not updatable: raise HTTPException(400, "Nothing to update")
    await db.investments.update_one({"id": iid, "user_id": u["_id"]}, {"$set": updatable})
    return {"ok": True}

@api.delete("/investments/{iid}")
async def del_investment(iid: str, u: dict = Depends(current_user)):
    await db.investments.delete_one({"id": iid, "user_id": u["_id"]})
    return {"ok": True}

# ═══════════════════ PHASE 2: REAL ESTATE ═══════════════════
class RealEstateBody(BaseModel):
    name: str
    property_type: str  # apartment, house, plot, commercial
    purchase_price: float
    current_value: float
    purchase_date: str
    location: Optional[str] = ""
    notes: Optional[str] = ""

@api.get("/real-estate")
async def get_real_estate(u: dict = Depends(current_user)):
    items = await db.real_estate.find({"user_id": u["_id"]}, {"_id": 0}).to_list(100)
    for it in items:
        gain = it["current_value"] - it["purchase_price"]
        it["appreciation"] = round(gain, 2)
        it["appreciation_pct"] = round((gain / it["purchase_price"]) * 100, 2) if it["purchase_price"] > 0 else 0
    total_value = sum(i["current_value"] for i in items)
    total_cost = sum(i["purchase_price"] for i in items)
    return {
        "items": items,
        "total_value": round(total_value, 2),
        "total_cost": round(total_cost, 2),
        "total_appreciation": round(total_value - total_cost, 2),
        "appreciation_pct": round(((total_value - total_cost) / total_cost) * 100, 2) if total_cost > 0 else 0,
    }

@api.post("/real-estate")
async def add_real_estate(body: RealEstateBody, u: dict = Depends(current_user)):
    doc = {"id": str(ObjectId()), "user_id": u["_id"], **body.dict(), "created_at": datetime.now(timezone.utc).isoformat()}
    await db.real_estate.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api.delete("/real-estate/{rid}")
async def del_real_estate(rid: str, u: dict = Depends(current_user)):
    await db.real_estate.delete_one({"id": rid, "user_id": u["_id"]})
    return {"ok": True}

# ═══════════════════ PHASE 2: NET WORTH ═══════════════════
@api.get("/net-worth")
async def get_net_worth(u: dict = Depends(current_user)):
    # Assets
    txns = await db.ind_transactions.find({"user_id": u["_id"]}, {"_id": 0}).to_list(20000)
    inc = sum(t["amount"] for t in txns if t["type"] == "income")
    exp = sum(t["amount"] for t in txns if t["type"] == "expense")
    cash_balance = round(inc - exp, 2)

    goals = await db.ind_goals.find({"user_id": u["_id"]}, {"_id": 0}).to_list(100)
    goal_savings = sum(g.get("saved", 0) for g in goals)

    inv_items = await db.investments.find({"user_id": u["_id"]}, {"_id": 0}).to_list(500)
    inv_value = sum((i["quantity"] * (i.get("current_price") or i["buy_price"])) for i in inv_items)

    re_items = await db.real_estate.find({"user_id": u["_id"]}, {"_id": 0}).to_list(100)
    re_value = sum(r["current_value"] for r in re_items)

    # Liabilities
    loans = await db.loans.find({"user_id": u["_id"]}, {"_id": 0}).to_list(50)
    total_loan_outstanding = 0
    for loan in loans:
        r = loan["interest_rate"] / 12 / 100
        n = loan["tenure_months"]
        emi = loan["emi_amount"]
        start = datetime.strptime(loan["start_date"], "%Y-%m-%d")
        months_elapsed = max(0, (datetime.now(timezone.utc).year - start.year) * 12 + datetime.now(timezone.utc).month - start.month)
        emis_paid = min(months_elapsed, n)
        balance = loan["principal"]
        for _ in range(emis_paid):
            interest = balance * r if r > 0 else 0
            principal = emi - interest
            balance = max(0, balance - principal)
        total_loan_outstanding += balance

    cards = await db.credit_cards.find({"user_id": u["_id"]}, {"_id": 0}).to_list(20)
    total_cc_outstanding = sum(c.get("outstanding", 0) for c in cards)

    borrowed = await db.lend_borrow.find({"user_id": u["_id"], "direction": "borrowed", "status": {"$ne": "settled"}}, {"_id": 0}).to_list(200)
    total_borrowed = sum(b["amount"] for b in borrowed)
    lent = await db.lend_borrow.find({"user_id": u["_id"], "direction": "lent", "status": {"$ne": "settled"}}, {"_id": 0}).to_list(200)
    total_lent = sum(l["amount"] for l in lent)

    assets = {
        "cash": max(0, cash_balance),
        "savings_goals": round(goal_savings, 2),
        "investments": round(inv_value, 2),
        "real_estate": round(re_value, 2),
        "money_lent": round(total_lent, 2),
    }
    liabilities = {
        "loans": round(total_loan_outstanding, 2),
        "credit_cards": round(total_cc_outstanding, 2),
        "money_borrowed": round(total_borrowed, 2),
    }
    total_assets = sum(assets.values())
    total_liabilities = sum(liabilities.values())
    net_worth = total_assets - total_liabilities
    return {
        "assets": assets,
        "liabilities": liabilities,
        "total_assets": round(total_assets, 2),
        "total_liabilities": round(total_liabilities, 2),
        "net_worth": round(net_worth, 2),
    }

# ═══════════════════ PHASE 2: ZERO-BASED BUDGET PLANNER ═══════════════════
class ZeroBudgetBody(BaseModel):
    month: str  # YYYY-MM
    monthly_income: float
    allocations: List[Dict[str, Any]]  # [{category, amount}]

@api.get("/zero-budget/{month}")
async def get_zero_budget(month: str, u: dict = Depends(current_user)):
    doc = await db.zero_budgets.find_one({"user_id": u["_id"], "month": month}, {"_id": 0})
    if not doc:
        return {"month": month, "monthly_income": 0, "allocations": [], "total_allocated": 0, "unallocated": 0}
    # Compute actual spend per category this month
    txns = await db.ind_transactions.find({"user_id": u["_id"], "type": "expense", "date": {"$regex": f"^{month}"}}).to_list(5000)
    actual = defaultdict(float)
    for t in txns: actual[t["category"]] += t["amount"]
    for a in doc.get("allocations", []):
        spent = round(actual.get(a["category"], 0), 2)
        a["spent"] = spent
        a["remaining"] = round(a["amount"] - spent, 2)
        a["percentage"] = round((spent / a["amount"]) * 100, 1) if a["amount"] > 0 else 0
    total_alloc = sum(a["amount"] for a in doc.get("allocations", []))
    doc["total_allocated"] = round(total_alloc, 2)
    doc["unallocated"] = round(doc["monthly_income"] - total_alloc, 2)
    return doc

@api.post("/zero-budget")
async def save_zero_budget(body: ZeroBudgetBody, u: dict = Depends(current_user)):
    doc = {"user_id": u["_id"], "month": body.month, "monthly_income": body.monthly_income, "allocations": body.allocations, "updated_at": datetime.now(timezone.utc).isoformat()}
    await db.zero_budgets.update_one({"user_id": u["_id"], "month": body.month}, {"$set": doc}, upsert=True)
    return {"ok": True}

# ═══════════════════ PHASE 2: LEND & BORROW LOG ═══════════════════
class LendBorrowBody(BaseModel):
    direction: str  # "lent" or "borrowed"
    person: str
    amount: float
    date: str
    due_date: Optional[str] = ""
    interest_rate: Optional[float] = 0
    notes: Optional[str] = ""
    status: Optional[str] = "open"  # open, partial, settled

@api.get("/lend-borrow")
async def get_lend_borrow(u: dict = Depends(current_user)):
    items = await db.lend_borrow.find({"user_id": u["_id"]}, {"_id": 0}).sort("date", -1).to_list(500)
    total_lent = sum(i["amount"] for i in items if i["direction"] == "lent" and i.get("status") != "settled")
    total_borrowed = sum(i["amount"] for i in items if i["direction"] == "borrowed" and i.get("status") != "settled")
    return {"items": items, "total_lent": round(total_lent, 2), "total_borrowed": round(total_borrowed, 2), "net": round(total_lent - total_borrowed, 2)}

@api.post("/lend-borrow")
async def add_lend_borrow(body: LendBorrowBody, u: dict = Depends(current_user)):
    if body.direction not in {"lent", "borrowed"}: raise HTTPException(400, "Invalid direction")
    doc = {"id": str(ObjectId()), "user_id": u["_id"], **body.dict(), "created_at": datetime.now(timezone.utc).isoformat()}
    await db.lend_borrow.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api.patch("/lend-borrow/{lid}")
async def update_lend_borrow(lid: str, request: Request, u: dict = Depends(current_user)):
    body = await request.json()
    updatable = {k: v for k, v in body.items() if k in {"status", "amount", "notes", "due_date"}}
    await db.lend_borrow.update_one({"id": lid, "user_id": u["_id"]}, {"$set": updatable})
    return {"ok": True}

@api.delete("/lend-borrow/{lid}")
async def del_lend_borrow(lid: str, u: dict = Depends(current_user)):
    await db.lend_borrow.delete_one({"id": lid, "user_id": u["_id"]})
    return {"ok": True}

# ═══════════════════ PHASE 2: DEBT PAYOFF CALCULATOR ═══════════════════
class DebtPayoffBody(BaseModel):
    debts: List[Dict[str, Any]]  # [{name, balance, interest_rate, min_payment}]
    extra_monthly: float
    strategy: Optional[str] = "avalanche"  # avalanche | snowball | both

def _simulate_payoff(debts: List[Dict[str, Any]], extra: float, strategy: str):
    # Deep copy
    items = [{"name": d["name"], "balance": float(d["balance"]), "rate": float(d["interest_rate"]), "min": float(d["min_payment"])} for d in debts]
    if strategy == "avalanche":
        items.sort(key=lambda x: -x["rate"])
    else:  # snowball
        items.sort(key=lambda x: x["balance"])
    months = 0
    total_interest = 0
    payoff_order = []
    max_months = 600
    while any(i["balance"] > 0 for i in items) and months < max_months:
        months += 1
        # Apply interest
        for it in items:
            if it["balance"] > 0:
                interest = it["balance"] * (it["rate"] / 12 / 100)
                it["balance"] += interest
                total_interest += interest
        # Pay minimums
        extra_pool = extra
        for it in items:
            if it["balance"] > 0:
                pay = min(it["min"], it["balance"])
                it["balance"] -= pay
        # Apply extra to target (first with balance > 0 in sort order)
        for it in items:
            if it["balance"] > 0:
                pay = min(extra_pool, it["balance"])
                it["balance"] -= pay
                extra_pool -= pay
                if extra_pool <= 0: break
        # Track payoff
        for it in items:
            if it["balance"] <= 0.01 and it["name"] not in payoff_order:
                payoff_order.append(it["name"])
                it["balance"] = 0
    total_principal = sum(float(d["balance"]) for d in debts)
    return {
        "strategy": strategy,
        "months_to_payoff": months,
        "total_interest": round(total_interest, 2),
        "total_paid": round(total_principal + total_interest, 2),
        "payoff_order": payoff_order,
    }

@api.post("/debt-payoff/simulate")
async def simulate_debt_payoff(body: DebtPayoffBody, u: dict = Depends(current_user)):
    if not body.debts: raise HTTPException(400, "No debts provided")
    if body.strategy == "both":
        av = _simulate_payoff(body.debts, body.extra_monthly, "avalanche")
        sn = _simulate_payoff(body.debts, body.extra_monthly, "snowball")
        return {
            "avalanche": av,
            "snowball": sn,
            "interest_saved_by_avalanche": round(sn["total_interest"] - av["total_interest"], 2),
            "months_saved_by_avalanche": sn["months_to_payoff"] - av["months_to_payoff"],
        }
    return _simulate_payoff(body.debts, body.extra_monthly, body.strategy)

# ═══════════════════ PHASE 3: SAVINGS JARS ═══════════════════
class JarBody(BaseModel):
    name: str
    target: Optional[float] = 0
    color: Optional[str] = "#F4845F"
    icon: Optional[str] = "piggy-bank"

class JarTxnBody(BaseModel):
    amount: float
    note: Optional[str] = ""

@api.get("/jars")
async def get_jars(u: dict = Depends(current_user)):
    jars = await db.jars.find({"user_id": u["_id"]}, {"_id": 0}).to_list(50)
    for j in jars:
        j["balance"] = round(j.get("balance", 0), 2)
        j["progress"] = round((j["balance"] / j["target"]) * 100, 1) if j.get("target", 0) > 0 else 0
    total = sum(j["balance"] for j in jars)
    return {"jars": jars, "total_saved": round(total, 2)}

@api.post("/jars")
async def create_jar(body: JarBody, u: dict = Depends(current_user)):
    doc = {"id": str(ObjectId()), "user_id": u["_id"], "balance": 0, **body.dict(), "created_at": datetime.now(timezone.utc).isoformat()}
    await db.jars.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api.post("/jars/{jid}/deposit")
async def jar_deposit(jid: str, body: JarTxnBody, u: dict = Depends(current_user)):
    await db.jars.update_one({"id": jid, "user_id": u["_id"]}, {"$inc": {"balance": body.amount}})
    await db.jar_txns.insert_one({"user_id": u["_id"], "jar_id": jid, "amount": body.amount, "type": "deposit", "note": body.note, "date": datetime.now(timezone.utc).isoformat()})
    return {"ok": True}

@api.post("/jars/{jid}/withdraw")
async def jar_withdraw(jid: str, body: JarTxnBody, u: dict = Depends(current_user)):
    await db.jars.update_one({"id": jid, "user_id": u["_id"]}, {"$inc": {"balance": -abs(body.amount)}})
    await db.jar_txns.insert_one({"user_id": u["_id"], "jar_id": jid, "amount": body.amount, "type": "withdraw", "note": body.note, "date": datetime.now(timezone.utc).isoformat()})
    return {"ok": True}

@api.delete("/jars/{jid}")
async def del_jar(jid: str, u: dict = Depends(current_user)):
    await db.jars.delete_one({"id": jid, "user_id": u["_id"]})
    return {"ok": True}

# ═══════════════════ PHASE 3: SIP / RD TRACKER ═══════════════════
class SIPBody(BaseModel):
    plan_type: str  # SIP or RD
    name: str
    monthly_amount: float
    start_date: str
    tenure_months: int
    expected_return: Optional[float] = 12.0  # annual % — for RD use FD rate
    bank_or_amc: Optional[str] = ""

@api.get("/sip-rd")
async def get_sips(u: dict = Depends(current_user)):
    items = await db.sip_rd.find({"user_id": u["_id"]}, {"_id": 0}).to_list(200)
    total_monthly = 0
    total_invested_all = 0
    total_value_all = 0
    for it in items:
        start = datetime.strptime(it["start_date"], "%Y-%m-%d")
        months_elapsed = max(0, (datetime.now(timezone.utc).year - start.year) * 12 + datetime.now(timezone.utc).month - start.month)
        installments = min(months_elapsed, it["tenure_months"])
        invested = installments * it["monthly_amount"]
        r = (it.get("expected_return") or 12) / 12 / 100
        # FV of SIP annuity
        if r > 0 and installments > 0:
            fv = it["monthly_amount"] * (((1 + r) ** installments - 1) / r) * (1 + r)
        else:
            fv = invested
        # Projection at maturity
        n = it["tenure_months"]
        if r > 0:
            fv_mat = it["monthly_amount"] * (((1 + r) ** n - 1) / r) * (1 + r)
        else:
            fv_mat = it["monthly_amount"] * n
        it["installments_paid"] = installments
        it["invested_so_far"] = round(invested, 2)
        it["current_value"] = round(fv, 2)
        it["projected_maturity"] = round(fv_mat, 2)
        it["projected_gain"] = round(fv_mat - (it["monthly_amount"] * n), 2)
        total_monthly += it["monthly_amount"] if installments < n else 0
        total_invested_all += invested
        total_value_all += fv
    return {
        "items": items,
        "total_monthly_commitment": round(total_monthly, 2),
        "total_invested": round(total_invested_all, 2),
        "total_current_value": round(total_value_all, 2),
    }

@api.post("/sip-rd")
async def add_sip(body: SIPBody, u: dict = Depends(current_user)):
    doc = {"id": str(ObjectId()), "user_id": u["_id"], **body.dict(), "created_at": datetime.now(timezone.utc).isoformat()}
    await db.sip_rd.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api.delete("/sip-rd/{sid}")
async def del_sip(sid: str, u: dict = Depends(current_user)):
    await db.sip_rd.delete_one({"id": sid, "user_id": u["_id"]})
    return {"ok": True}

# ═══════════════════ PHASE 3: FD TRACKER ═══════════════════
class FDBody(BaseModel):
    bank: str
    principal: float
    interest_rate: float
    start_date: str
    tenure_months: int
    compounding: Optional[str] = "quarterly"  # monthly, quarterly, yearly

@api.get("/fds")
async def get_fds(u: dict = Depends(current_user)):
    items = await db.fds.find({"user_id": u["_id"]}, {"_id": 0}).to_list(100)
    total_principal = 0
    total_maturity = 0
    for it in items:
        comp_map = {"monthly": 12, "quarterly": 4, "yearly": 1}
        n = comp_map.get(it.get("compounding", "quarterly"), 4)
        t = it["tenure_months"] / 12
        maturity = it["principal"] * ((1 + (it["interest_rate"] / 100) / n) ** (n * t))
        interest = maturity - it["principal"]
        start = datetime.strptime(it["start_date"], "%Y-%m-%d")
        mat_date = start + timedelta(days=int(it["tenure_months"] * 30.42))
        it["maturity_amount"] = round(maturity, 2)
        it["interest_earned"] = round(interest, 2)
        it["maturity_date"] = mat_date.strftime("%Y-%m-%d")
        days_left = (mat_date - datetime.now(timezone.utc).replace(tzinfo=None)).days
        it["days_to_maturity"] = max(0, days_left)
        it["matured"] = days_left <= 0
        total_principal += it["principal"]
        total_maturity += maturity
    return {"items": items, "total_principal": round(total_principal, 2), "total_maturity": round(total_maturity, 2), "total_interest": round(total_maturity - total_principal, 2)}

@api.post("/fds")
async def add_fd(body: FDBody, u: dict = Depends(current_user)):
    doc = {"id": str(ObjectId()), "user_id": u["_id"], **body.dict(), "created_at": datetime.now(timezone.utc).isoformat()}
    await db.fds.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api.delete("/fds/{fid}")
async def del_fd(fid: str, u: dict = Depends(current_user)):
    await db.fds.delete_one({"id": fid, "user_id": u["_id"]})
    return {"ok": True}

# ═══════════════════ PHASE 4: TAX — 80C/80D DEDUCTIONS ═══════════════════
DEDUCTION_LIMITS = {
    "80C": 150000,   # PPF, ELSS, EPF, Life Insurance, etc.
    "80D": 75000,    # Health insurance (self + parents senior)
    "80CCD(1B)": 50000,  # NPS additional
    "80E": 0,        # No limit, education loan interest
    "80G": 0,        # Donations (varies)
    "80TTA": 10000,  # Savings interest
    "24(b)": 200000, # Home loan interest
}

class DeductionBody(BaseModel):
    section: str
    name: str
    amount: float
    financial_year: str  # 2025-26
    notes: Optional[str] = ""

@api.get("/deductions/{fy}")
async def get_deductions(fy: str, u: dict = Depends(current_user)):
    items = await db.deductions.find({"user_id": u["_id"], "financial_year": fy}, {"_id": 0}).to_list(500)
    by_section = defaultdict(lambda: {"total": 0, "items": [], "limit": 0, "remaining": 0, "utilization_pct": 0})
    for it in items:
        by_section[it["section"]]["items"].append(it)
        by_section[it["section"]]["total"] += it["amount"]
    for sec, data in by_section.items():
        lim = DEDUCTION_LIMITS.get(sec, 0)
        data["limit"] = lim
        data["total"] = round(data["total"], 2)
        data["remaining"] = round(max(0, lim - data["total"]), 2) if lim > 0 else 0
        data["utilization_pct"] = round((data["total"] / lim) * 100, 1) if lim > 0 else 0
    total_claimed = sum(d["total"] for d in by_section.values())
    # Estimated tax saved at 30% slab
    tax_saved = total_claimed * 0.30
    return {"financial_year": fy, "sections": dict(by_section), "total_claimed": round(total_claimed, 2), "estimated_tax_saved": round(tax_saved, 2)}

@api.post("/deductions")
async def add_deduction(body: DeductionBody, u: dict = Depends(current_user)):
    doc = {"id": str(ObjectId()), "user_id": u["_id"], **body.dict(), "created_at": datetime.now(timezone.utc).isoformat()}
    await db.deductions.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api.delete("/deductions/{did}")
async def del_deduction(did: str, u: dict = Depends(current_user)):
    await db.deductions.delete_one({"id": did, "user_id": u["_id"]})
    return {"ok": True}

# ═══════════════════ PHASE 4: TAX CALENDAR ═══════════════════
@api.get("/tax-calendar/{fy}")
async def get_tax_calendar(fy: str, u: dict = Depends(current_user)):
    # Indian tax calendar for FY (e.g. 2025-26)
    start_year = int(fy.split("-")[0])
    events = [
        {"date": f"{start_year}-06-15", "title": "Advance Tax — 1st Installment", "description": "15% of estimated tax liability", "type": "advance_tax"},
        {"date": f"{start_year}-07-31", "title": "ITR Filing (Non-Audit)", "description": "Last date to file ITR for individuals", "type": "itr"},
        {"date": f"{start_year}-09-15", "title": "Advance Tax — 2nd Installment", "description": "45% cumulative", "type": "advance_tax"},
        {"date": f"{start_year}-10-31", "title": "ITR Filing (Audit Cases)", "description": "Last date for audit cases", "type": "itr"},
        {"date": f"{start_year}-12-15", "title": "Advance Tax — 3rd Installment", "description": "75% cumulative", "type": "advance_tax"},
        {"date": f"{start_year+1}-01-31", "title": "TDS Certificate (Form 16A)", "description": "Quarterly TDS certificate", "type": "tds"},
        {"date": f"{start_year+1}-03-15", "title": "Advance Tax — 4th Installment", "description": "100% cumulative", "type": "advance_tax"},
        {"date": f"{start_year+1}-03-31", "title": "Tax Saving Investments Deadline", "description": "Last date for 80C/80D investments", "type": "investment"},
        {"date": f"{start_year+1}-05-31", "title": "Form 16 Issuance", "description": "Employers issue Form 16", "type": "form16"},
    ]
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for e in events:
        days_to = (datetime.strptime(e["date"], "%Y-%m-%d") - datetime.now(timezone.utc).replace(tzinfo=None)).days
        e["days_until"] = days_to
        e["status"] = "past" if days_to < 0 else "upcoming" if days_to > 7 else "due_soon"
    return {"financial_year": fy, "events": events}

# ═══════════════════ PHASE 4: ITR CATEGORY AUTO-TAG ═══════════════════
ITR_CATEGORY_MAP = {
    "Salary": "salary", "Income": "salary", "Bonus": "salary",
    "Rent": "house_property", "Rental Income": "house_property",
    "Dividend": "other_sources", "Interest": "other_sources", "FD Interest": "other_sources",
    "Capital Gains": "capital_gains", "Investments": "capital_gains", "Stocks": "capital_gains",
    "Business": "business", "Freelance": "business", "Consulting": "business",
    "Groceries": "not_taxable", "Food": "not_taxable", "Transport": "not_taxable",
    "Entertainment": "not_taxable", "Shopping": "not_taxable", "Utilities": "not_taxable",
    "Rent Paid": "exempt_hra", "Medical": "80D", "Insurance": "80C",
    "Donation": "80G", "PPF": "80C", "ELSS": "80C", "NPS": "80CCD(1B)",
}

@api.get("/itr-summary/{fy}")
async def get_itr_summary(fy: str, u: dict = Depends(current_user)):
    # fy format: 2025-26 (Apr 2025 - Mar 2026)
    start_year = int(fy.split("-")[0])
    start = f"{start_year}-04-01"
    end = f"{start_year + 1}-03-31"
    txns = await db.ind_transactions.find({"user_id": u["_id"], "date": {"$gte": start, "$lte": end}}, {"_id": 0}).to_list(20000)

    itr_buckets = defaultdict(lambda: {"amount": 0, "count": 0, "txns": []})
    for t in txns:
        cat = t["category"]
        itr_tag = ITR_CATEGORY_MAP.get(cat, "other_sources" if t["type"] == "income" else "not_taxable")
        itr_buckets[itr_tag]["amount"] += t["amount"] if t["type"] == "income" else 0
        itr_buckets[itr_tag]["count"] += 1

    for k, v in itr_buckets.items():
        v["amount"] = round(v["amount"], 2)
        v.pop("txns", None)

    total_income = sum(v["amount"] for k, v in itr_buckets.items() if k != "not_taxable")
    return {"financial_year": fy, "buckets": dict(itr_buckets), "total_income": round(total_income, 2)}

# ═══════════════════ PHASE 4: FORM 26AS UPLOAD & PARSE ═══════════════════
@api.post("/tax/form26as/upload")
async def upload_form26as(request: Request, u: dict = Depends(current_user)):
    # Accept PDF as multipart/form-data OR JSON base64
    content_type = request.headers.get("content-type", "")
    pdf_bytes = None
    if "multipart/form-data" in content_type:
        form = await request.form()
        f = form.get("file")
        if f: pdf_bytes = await f.read()
    else:
        body = await request.json()
        import base64
        b64 = body.get("pdf_base64", "")
        if b64: pdf_bytes = base64.b64decode(b64)
    if not pdf_bytes: raise HTTPException(400, "No PDF provided")

    # Parse with pdfplumber
    text = ""
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                text += (page.extract_text() or "") + "\n"
    except Exception as e:
        raise HTTPException(400, f"Failed to parse PDF: {e}")

    # Extract TDS entries: amounts following "TDS" or large ₹ amounts in tables
    tds_entries = []
    amt_pattern = re.compile(r'(?:Rs\.?|INR|₹)?\s*([\d,]+\.\d{2})')
    lines = text.split("\n")
    total_tds = 0
    total_income = 0
    for ln in lines:
        low = ln.lower()
        m = amt_pattern.findall(ln)
        if not m: continue
        if "tds" in low or "tax deducted" in low:
            try:
                amt = float(m[-1].replace(",", ""))
                tds_entries.append({"description": ln[:80].strip(), "amount": amt})
                total_tds += amt
            except: pass

    # Save summary
    doc = {
        "id": str(ObjectId()), "user_id": u["_id"],
        "total_tds": round(total_tds, 2),
        "total_income": round(total_income, 2),
        "entries": tds_entries[:50],
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.form_26as.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api.get("/tax/form26as")
async def get_form26as(u: dict = Depends(current_user)):
    docs = await db.form_26as.find({"user_id": u["_id"]}, {"_id": 0}).sort("uploaded_at", -1).to_list(20)
    return docs

# ═══════════════════ PHASE 4+: UNUSUAL SPEND ALERTS ═══════════════════
@api.get("/unusual-alerts")
async def unusual_spend_alerts(u: dict = Depends(current_user)):
    txns = await db.ind_transactions.find({"user_id": u["_id"], "type": "expense"}, {"_id": 0}).to_list(10000)
    cats = defaultdict(list)
    for t in txns:
        cats[t["category"]].append(t)
    alerts = []
    for cat, entries in cats.items():
        if len(entries) < 4: continue
        amounts = [e["amount"] for e in entries]
        avg = sum(amounts[:-1]) / (len(amounts) - 1)
        std = (sum((a - avg) ** 2 for a in amounts[:-1]) / max(1, len(amounts) - 1)) ** 0.5
        last = entries[-1]
        # Z-score approach: flag if last transaction > avg + 2*std AND > avg*1.5
        if last["amount"] > avg * 1.5 and last["amount"] > avg + 1.5 * std and std > 0:
            alerts.append({
                "category": cat,
                "amount": last["amount"],
                "date": last["date"],
                "average": round(avg, 2),
                "deviation_pct": round(((last["amount"] - avg) / avg) * 100, 1),
                "severity": "high" if last["amount"] > avg * 2 else "medium",
                "description": last.get("description", ""),
            })
    return {"alerts": sorted(alerts, key=lambda x: -x["deviation_pct"])}

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
