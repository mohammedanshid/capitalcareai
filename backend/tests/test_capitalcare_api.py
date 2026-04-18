"""
Capital Care AI - Backend API Tests (Iteration 5)
Tests for: Auth, Persona, Individual, Shop Owner, CA, AI Chat, Forecast, Alerts, Export, SMS Parser, Pricing
App renamed from FinFlow to Capital Care AI
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials - Updated for Capital Care AI
ADMIN_EMAIL = "admin@capitalcare.ai"
ADMIN_PASSWORD = "Admin@123"
TEST_EMAIL = f"test_{datetime.now().strftime('%Y%m%d%H%M%S')}@capitalcare.ai"
TEST_PASSWORD = "Test@123"


class TestAuth:
    """Authentication endpoint tests"""
    
    def test_login_success(self):
        """Test login with valid admin credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert data["email"] == ADMIN_EMAIL
        print(f"Login success: {data['email']}")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpass"
        })
        assert response.status_code == 401
        print("Invalid credentials correctly rejected")
    
    def test_register_new_user(self):
        """Test user registration"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "name": "Test User",
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Registration failed: {response.text}"
        data = response.json()
        assert data["email"] == TEST_EMAIL.lower()
        print(f"Registration success: {data['email']}")
    
    def test_me_endpoint_with_auth(self):
        """Test /auth/me with valid session"""
        session = requests.Session()
        login_resp = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_resp.status_code == 200
        
        me_resp = session.get(f"{BASE_URL}/api/auth/me")
        assert me_resp.status_code == 200
        data = me_resp.json()
        assert data["email"] == ADMIN_EMAIL
        print(f"Me endpoint returned: {data['email']}")
    
    def test_logout(self):
        """Test logout endpoint"""
        session = requests.Session()
        session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        logout_resp = session.post(f"{BASE_URL}/api/auth/logout")
        assert logout_resp.status_code == 200
        assert logout_resp.json().get("ok") == True
        print("Logout successful")


class TestPersona:
    """Persona selection tests"""
    
    @pytest.fixture
    def auth_session(self):
        session = requests.Session()
        session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return session
    
    def test_select_individual_persona(self, auth_session):
        """Test selecting individual persona"""
        response = auth_session.post(f"{BASE_URL}/api/persona/select", json={
            "persona": "individual"
        })
        assert response.status_code == 200
        assert response.json()["persona"] == "individual"
        print("Individual persona selected")
    
    def test_select_shop_owner_persona(self, auth_session):
        """Test selecting shop_owner persona"""
        response = auth_session.post(f"{BASE_URL}/api/persona/select", json={
            "persona": "shop_owner"
        })
        assert response.status_code == 200
        assert response.json()["persona"] == "shop_owner"
        print("Shop owner persona selected")
    
    def test_select_ca_persona(self, auth_session):
        """Test selecting ca persona"""
        response = auth_session.post(f"{BASE_URL}/api/persona/select", json={
            "persona": "ca"
        })
        assert response.status_code == 200
        assert response.json()["persona"] == "ca"
        print("CA persona selected")
    
    def test_invalid_persona(self, auth_session):
        """Test selecting invalid persona"""
        response = auth_session.post(f"{BASE_URL}/api/persona/select", json={
            "persona": "invalid"
        })
        assert response.status_code == 400
        print("Invalid persona correctly rejected")


class TestIndividual:
    """Individual persona endpoint tests"""
    
    @pytest.fixture
    def auth_session(self):
        session = requests.Session()
        session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        session.post(f"{BASE_URL}/api/persona/select", json={"persona": "individual"})
        return session
    
    def test_individual_dashboard(self, auth_session):
        """Test individual dashboard endpoint"""
        response = auth_session.get(f"{BASE_URL}/api/individual/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "income" in data
        assert "expenses" in data
        assert "savings_rate" in data
        assert "net_worth" in data
        assert "category_breakdown" in data
        assert "monthly_series" in data
        assert "goals" in data
        print(f"Dashboard: income={data['income']}, expenses={data['expenses']}")
    
    def test_add_income_transaction(self, auth_session):
        """Test adding income transaction"""
        response = auth_session.post(f"{BASE_URL}/api/individual/transactions", json={
            "amount": 50000,
            "category": "Salary",
            "type": "income",
            "description": "TEST_Monthly salary",
            "date": datetime.now().strftime("%Y-%m-%d")
        })
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 50000
        assert data["type"] == "income"
        print(f"Income transaction added: {data['id']}")
    
    def test_add_expense_transaction(self, auth_session):
        """Test adding expense transaction"""
        response = auth_session.post(f"{BASE_URL}/api/individual/transactions", json={
            "amount": 3000,
            "category": "Groceries",
            "type": "expense",
            "description": "TEST_Weekly groceries",
            "date": datetime.now().strftime("%Y-%m-%d")
        })
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 3000
        assert data["type"] == "expense"
        print(f"Expense transaction added: {data['id']}")
    
    def test_get_transactions(self, auth_session):
        """Test getting transactions list"""
        response = auth_session.get(f"{BASE_URL}/api/individual/transactions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Got {len(data)} transactions")
    
    def test_create_goal(self, auth_session):
        """Test creating a savings goal"""
        response = auth_session.post(f"{BASE_URL}/api/individual/goals", json={
            "name": "TEST_Emergency Fund",
            "target": 100000,
            "saved": 10000,
            "deadline": "2026-12-31"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "TEST_Emergency Fund"
        assert data["target"] == 100000
        print(f"Goal created: {data['id']}")
    
    def test_get_goals(self, auth_session):
        """Test getting goals list"""
        response = auth_session.get(f"{BASE_URL}/api/individual/goals")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Got {len(data)} goals")


class TestShopOwner:
    """Shop Owner persona endpoint tests"""
    
    @pytest.fixture
    def auth_session(self):
        session = requests.Session()
        session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        session.post(f"{BASE_URL}/api/persona/select", json={"persona": "shop_owner"})
        return session
    
    def test_shop_dashboard(self, auth_session):
        """Test shop owner dashboard endpoint"""
        response = auth_session.get(f"{BASE_URL}/api/shop/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "today" in data
        assert "opening_balance" in data
        assert "today_credit" in data
        assert "today_debit" in data
        assert "closing_balance" in data
        print(f"Shop dashboard: credit={data['today_credit']}, debit={data['today_debit']}")
    
    def test_add_credit_entry(self, auth_session):
        """Test adding credit entry"""
        response = auth_session.post(f"{BASE_URL}/api/shop/entry", json={
            "amount": 5000,
            "category": "Sales",
            "note": "TEST_Cash sale",
            "entry_type": "credit"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 5000
        assert data["entry_type"] == "credit"
        print(f"Credit entry added: {data['id']}")
    
    def test_add_debit_entry(self, auth_session):
        """Test adding debit entry"""
        response = auth_session.post(f"{BASE_URL}/api/shop/entry", json={
            "amount": 2000,
            "category": "Purchase",
            "note": "TEST_Stock purchase",
            "entry_type": "debit"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 2000
        assert data["entry_type"] == "debit"
        print(f"Debit entry added: {data['id']}")
    
    def test_get_ledger(self, auth_session):
        """Test getting ledger entries"""
        response = auth_session.get(f"{BASE_URL}/api/shop/ledger")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Got {len(data)} ledger entries")


class TestCA:
    """CA (Chartered Accountant) persona endpoint tests"""
    
    @pytest.fixture
    def auth_session(self):
        session = requests.Session()
        session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        session.post(f"{BASE_URL}/api/persona/select", json={"persona": "ca"})
        return session
    
    def test_ca_dashboard(self, auth_session):
        """Test CA dashboard endpoint"""
        response = auth_session.get(f"{BASE_URL}/api/ca/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "clients" in data
        assert "tasks" in data
        assert "active_clients" in data
        print(f"CA dashboard: {data['active_clients']} clients")
    
    def test_add_client(self, auth_session):
        """Test adding a client"""
        response = auth_session.post(f"{BASE_URL}/api/ca/clients", json={
            "name": "TEST_ABC Corp",
            "business_type": "Retail",
            "status": "on_track"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "TEST_ABC Corp"
        print(f"Client added: {data['id']}")
    
    def test_get_clients(self, auth_session):
        """Test getting clients list"""
        response = auth_session.get(f"{BASE_URL}/api/ca/clients")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Got {len(data)} clients")
    
    def test_add_task(self, auth_session):
        """Test adding a task"""
        response = auth_session.post(f"{BASE_URL}/api/ca/tasks", json={
            "title": "TEST_File GST returns",
            "client_name": "ABC Corp",
            "deadline": "2026-01-31",
            "status": "pending"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "TEST_File GST returns"
        print(f"Task added: {data['id']}")
    
    def test_get_tasks(self, auth_session):
        """Test getting tasks list"""
        response = auth_session.get(f"{BASE_URL}/api/ca/tasks")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Got {len(data)} tasks")


# ═══════════════════ NEW FEATURES (Iteration 5) ═══════════════════

class TestAIChat:
    """AI Chat Assistant endpoint tests - NEW in Iteration 5"""
    
    @pytest.fixture
    def auth_session(self):
        session = requests.Session()
        session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return session
    
    def test_ai_chat_individual(self, auth_session):
        """Test AI chat for individual persona"""
        response = auth_session.post(f"{BASE_URL}/api/ai/chat", json={
            "message": "What is a good savings rate?",
            "persona": "individual"
        })
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert len(data["response"]) > 10  # Should have meaningful response
        print(f"AI Chat (individual): {data['response'][:100]}...")
    
    def test_ai_chat_shop_owner(self, auth_session):
        """Test AI chat for shop owner persona"""
        response = auth_session.post(f"{BASE_URL}/api/ai/chat", json={
            "message": "How can I improve my cash flow?",
            "persona": "shop_owner"
        })
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert len(data["response"]) > 10
        print(f"AI Chat (shop_owner): {data['response'][:100]}...")
    
    def test_ai_chat_ca(self, auth_session):
        """Test AI chat for CA persona"""
        response = auth_session.post(f"{BASE_URL}/api/ai/chat", json={
            "message": "What are the GST filing deadlines?",
            "persona": "ca"
        })
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert len(data["response"]) > 10
        print(f"AI Chat (ca): {data['response'][:100]}...")
    
    def test_ai_chat_empty_message(self, auth_session):
        """Test AI chat with empty message"""
        response = auth_session.post(f"{BASE_URL}/api/ai/chat", json={
            "message": "",
            "persona": "individual"
        })
        assert response.status_code == 400
        print("Empty message correctly rejected")
    
    def test_ai_chat_history(self, auth_session):
        """Test AI chat history endpoint"""
        response = auth_session.get(f"{BASE_URL}/api/ai/chat-history")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Got {len(data)} chat history entries")


class TestForecast:
    """Cash Flow Forecast endpoint tests - NEW in Iteration 5"""
    
    @pytest.fixture
    def auth_session(self):
        session = requests.Session()
        session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return session
    
    def test_forecast_individual(self, auth_session):
        """Test forecast for individual persona - 3 month projection"""
        response = auth_session.get(f"{BASE_URL}/api/forecast/individual")
        assert response.status_code == 200
        data = response.json()
        assert "forecast" in data
        assert "avg_income" in data
        assert "avg_expense" in data
        # Should have 3 months forecast
        if data["forecast"]:
            assert len(data["forecast"]) == 3
            for f in data["forecast"]:
                assert "month" in f
                assert "projected_income" in f
                assert "projected_expenses" in f
                assert "projected_savings" in f
        print(f"Individual forecast: avg_income={data['avg_income']}, avg_expense={data['avg_expense']}")
    
    def test_forecast_shop_owner(self, auth_session):
        """Test forecast for shop owner persona - 30/60/90 day projection"""
        response = auth_session.get(f"{BASE_URL}/api/forecast/shop_owner")
        assert response.status_code == 200
        data = response.json()
        assert "forecast_30" in data
        assert "forecast_60" in data
        assert "forecast_90" in data
        assert "daily_avg_net" in data
        assert "series" in data
        print(f"Shop forecast: 30d={data['forecast_30']}, 60d={data['forecast_60']}, 90d={data['forecast_90']}")


class TestAlerts:
    """Proactive Smart Alerts endpoint tests - NEW in Iteration 5"""
    
    @pytest.fixture
    def auth_session(self):
        session = requests.Session()
        session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return session
    
    def test_alerts_individual(self, auth_session):
        """Test alerts for individual persona"""
        response = auth_session.get(f"{BASE_URL}/api/alerts/individual")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0  # Should have at least one alert
        for alert in data:
            assert "type" in alert
            assert "severity" in alert
            assert "message" in alert
            assert alert["severity"] in ["warning", "info", "success"]
        print(f"Individual alerts: {len(data)} alerts")
    
    def test_alerts_shop_owner(self, auth_session):
        """Test alerts for shop owner persona"""
        response = auth_session.get(f"{BASE_URL}/api/alerts/shop_owner")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        print(f"Shop owner alerts: {len(data)} alerts")
    
    def test_alerts_ca(self, auth_session):
        """Test alerts for CA persona"""
        response = auth_session.get(f"{BASE_URL}/api/alerts/ca")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        print(f"CA alerts: {len(data)} alerts")


class TestExport:
    """Export PDF/CSV endpoint tests - NEW in Iteration 5"""
    
    @pytest.fixture
    def auth_session(self):
        session = requests.Session()
        session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return session
    
    def test_export_csv(self, auth_session):
        """Test CSV export for individual"""
        response = auth_session.get(f"{BASE_URL}/api/export/individual/csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
        # Check CSV content
        content = response.text
        assert "Date,Type,Category,Amount,Description" in content
        print(f"CSV export: {len(content)} bytes")
    
    def test_export_pdf(self, auth_session):
        """Test PDF export for individual"""
        response = auth_session.get(f"{BASE_URL}/api/export/individual/pdf")
        assert response.status_code == 200
        assert "application/pdf" in response.headers.get("content-type", "")
        # Check PDF magic bytes
        assert response.content[:4] == b'%PDF'
        print(f"PDF export: {len(response.content)} bytes")


class TestSMSParser:
    """SMS Parser endpoint tests"""
    
    def test_parse_debit_sms(self):
        """Test parsing debit SMS"""
        response = requests.post(f"{BASE_URL}/api/sms/parse", json={
            "text": "Your A/c XX1234 debited Rs.5000.00 on 15-Jan-26 at AMAZON."
        })
        assert response.status_code == 200
        data = response.json()
        assert data["parsed"] == True
        assert data["amount"] == 5000.0
        assert data["type"] == "debit"
        print(f"Parsed debit SMS: amount={data['amount']}")
    
    def test_parse_credit_sms(self):
        """Test parsing credit SMS"""
        response = requests.post(f"{BASE_URL}/api/sms/parse", json={
            "text": "INR 50,000.00 credited to your A/c XX5678 on 01-Jan-26."
        })
        assert response.status_code == 200
        data = response.json()
        assert data["parsed"] == True
        assert data["amount"] == 50000.0
        assert data["type"] == "credit"
        print(f"Parsed credit SMS: amount={data['amount']}")


class TestPricing:
    """Pricing endpoint tests"""
    
    def test_get_pricing(self):
        """Test getting pricing tiers"""
        response = requests.get(f"{BASE_URL}/api/pricing")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3
        
        individual = next((t for t in data if t["tier"] == "individual"), None)
        assert individual is not None
        assert individual["price"] == 99
        
        shop = next((t for t in data if t["tier"] == "shop_owner"), None)
        assert shop is not None
        assert shop["price"] == 299
        
        ca = next((t for t in data if t["tier"] == "ca"), None)
        assert ca is not None
        assert ca["price"] == 999
        
        print(f"Pricing: Individual=₹{individual['price']}, Shop=₹{shop['price']}, CA=₹{ca['price']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
