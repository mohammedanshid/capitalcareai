"""
Capital Care AI - Cashly Design System - Backend API Tests
Tests all API endpoints for the Individual persona (Shop Owner and CA removed from frontend)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://finance-ai-coach-1.preview.emergentagent.com').rstrip('/')

class TestAuth:
    """Authentication endpoint tests"""
    
    def test_login_success(self):
        """Test login with admin credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@capitalcare.ai",
            "password": "Admin@123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["email"] == "admin@capitalcare.ai"
        print(f"SUCCESS: Login - user id: {data['id']}")
        return response.cookies
    
    def test_login_invalid_credentials(self):
        """Test login with wrong password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@capitalcare.ai",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("SUCCESS: Invalid credentials rejected")
    
    def test_me_endpoint(self):
        """Test /auth/me with valid session"""
        # First login
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@capitalcare.ai",
            "password": "Admin@123"
        })
        cookies = login_resp.cookies
        
        # Then check /me
        response = requests.get(f"{BASE_URL}/api/auth/me", cookies=cookies)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "admin@capitalcare.ai"
        print(f"SUCCESS: /auth/me - user: {data['name']}")


class TestIndividualDashboard:
    """Individual dashboard and transactions tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get session cookies"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@capitalcare.ai",
            "password": "Admin@123"
        })
        self.cookies = login_resp.cookies
    
    def test_dashboard_loads(self):
        """Test individual dashboard endpoint"""
        response = requests.get(f"{BASE_URL}/api/individual/dashboard", cookies=self.cookies)
        assert response.status_code == 200
        data = response.json()
        # Check required fields
        assert "income" in data
        assert "expenses" in data
        assert "net_worth" in data
        assert "savings_rate" in data
        assert "sparkline_income" in data
        assert "sparkline_expenses" in data
        assert "category_breakdown" in data
        assert "monthly_series" in data
        assert "goals" in data
        print(f"SUCCESS: Dashboard - Income: {data['income']}, Expenses: {data['expenses']}, Net Worth: {data['net_worth']}")
    
    def test_transactions_crud(self):
        """Test create, read, delete transactions"""
        # Create income transaction
        create_resp = requests.post(f"{BASE_URL}/api/individual/transactions", json={
            "amount": 50000,
            "category": "Salary",
            "type": "income",
            "description": "TEST_Monthly salary",
            "date": "2026-01-15"
        }, cookies=self.cookies)
        assert create_resp.status_code == 200
        txn = create_resp.json()
        assert txn["amount"] == 50000
        assert txn["category"] == "Salary"
        txn_id = txn["id"]
        print(f"SUCCESS: Created income transaction: {txn_id}")
        
        # Create expense transaction
        create_exp = requests.post(f"{BASE_URL}/api/individual/transactions", json={
            "amount": 5000,
            "category": "Groceries",
            "type": "expense",
            "description": "TEST_Weekly groceries",
            "date": "2026-01-16"
        }, cookies=self.cookies)
        assert create_exp.status_code == 200
        exp_txn = create_exp.json()
        exp_id = exp_txn["id"]
        print(f"SUCCESS: Created expense transaction: {exp_id}")
        
        # Read transactions
        list_resp = requests.get(f"{BASE_URL}/api/individual/transactions", cookies=self.cookies)
        assert list_resp.status_code == 200
        txns = list_resp.json()
        assert isinstance(txns, list)
        print(f"SUCCESS: Listed {len(txns)} transactions")
        
        # Delete transactions
        del_resp = requests.delete(f"{BASE_URL}/api/individual/transactions/{txn_id}", cookies=self.cookies)
        assert del_resp.status_code == 200
        del_resp2 = requests.delete(f"{BASE_URL}/api/individual/transactions/{exp_id}", cookies=self.cookies)
        assert del_resp2.status_code == 200
        print("SUCCESS: Deleted test transactions")


class TestGoals:
    """Goals CRUD tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@capitalcare.ai",
            "password": "Admin@123"
        })
        self.cookies = login_resp.cookies
    
    def test_goals_crud(self):
        """Test create, read, update, delete goals"""
        # Create goal
        create_resp = requests.post(f"{BASE_URL}/api/individual/goals", json={
            "name": "TEST_Emergency Fund",
            "target": 100000,
            "saved": 25000,
            "deadline": "2026-12-31"
        }, cookies=self.cookies)
        assert create_resp.status_code == 200
        goal = create_resp.json()
        assert goal["name"] == "TEST_Emergency Fund"
        assert goal["target"] == 100000
        goal_id = goal["id"]
        print(f"SUCCESS: Created goal: {goal_id}")
        
        # Read goals
        list_resp = requests.get(f"{BASE_URL}/api/individual/goals", cookies=self.cookies)
        assert list_resp.status_code == 200
        goals = list_resp.json()
        assert isinstance(goals, list)
        print(f"SUCCESS: Listed {len(goals)} goals")
        
        # Update goal (add savings)
        update_resp = requests.put(f"{BASE_URL}/api/individual/goals/{goal_id}", json={
            "name": "TEST_Emergency Fund",
            "target": 100000,
            "saved": 35000,
            "deadline": "2026-12-31"
        }, cookies=self.cookies)
        assert update_resp.status_code == 200
        print("SUCCESS: Updated goal savings")
        
        # Delete goal
        del_resp = requests.delete(f"{BASE_URL}/api/individual/goals/{goal_id}", cookies=self.cookies)
        assert del_resp.status_code == 200
        print("SUCCESS: Deleted test goal")


class TestForecastAndAlerts:
    """Forecast and Smart Alerts tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@capitalcare.ai",
            "password": "Admin@123"
        })
        self.cookies = login_resp.cookies
    
    def test_forecast_individual(self):
        """Test 3-month savings forecast"""
        response = requests.get(f"{BASE_URL}/api/forecast/individual", cookies=self.cookies)
        assert response.status_code == 200
        data = response.json()
        assert "forecast" in data
        assert "avg_income" in data
        assert "avg_expense" in data
        print(f"SUCCESS: Forecast - Avg Income: {data['avg_income']}, Avg Expense: {data['avg_expense']}")
        if data["forecast"]:
            print(f"  Forecast months: {[f['month'] for f in data['forecast']]}")
    
    def test_alerts_individual(self):
        """Test proactive smart alerts"""
        response = requests.get(f"{BASE_URL}/api/alerts/individual", cookies=self.cookies)
        assert response.status_code == 200
        alerts = response.json()
        assert isinstance(alerts, list)
        print(f"SUCCESS: Got {len(alerts)} alerts")
        for alert in alerts[:3]:
            print(f"  - [{alert['severity']}] {alert['message'][:60]}...")


class TestExport:
    """Export PDF/CSV tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@capitalcare.ai",
            "password": "Admin@123"
        })
        self.cookies = login_resp.cookies
    
    def test_export_csv(self):
        """Test CSV export"""
        response = requests.get(f"{BASE_URL}/api/export/individual/csv", cookies=self.cookies)
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
        content = response.text
        assert "Date,Type,Category,Amount" in content
        print(f"SUCCESS: CSV export - {len(content)} bytes")
    
    def test_export_pdf(self):
        """Test PDF export"""
        response = requests.get(f"{BASE_URL}/api/export/individual/pdf", cookies=self.cookies)
        assert response.status_code == 200
        assert "application/pdf" in response.headers.get("content-type", "")
        print(f"SUCCESS: PDF export - {len(response.content)} bytes")


class TestSMSParser:
    """SMS Parser tests"""
    
    def test_parse_debit_sms(self):
        """Test parsing debit SMS"""
        response = requests.post(f"{BASE_URL}/api/sms/parse", json={
            "text": "Your A/c XX1234 debited Rs.5,000.00 on 15-Jan-26 at Amazon. Avl Bal Rs.45,000.00"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["parsed"] == True
        assert data["amount"] == 5000.0
        assert data["type"] == "debit"
        print(f"SUCCESS: Parsed debit SMS - Amount: {data['amount']}, Type: {data['type']}")
    
    def test_parse_credit_sms(self):
        """Test parsing credit SMS"""
        response = requests.post(f"{BASE_URL}/api/sms/parse", json={
            "text": "Rs.50,000.00 credited to your A/c XX5678 on 01-Jan-26. Salary from ABC Corp. Avl Bal Rs.95,000.00"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["parsed"] == True
        assert data["amount"] == 50000.0
        assert data["type"] == "credit"
        print(f"SUCCESS: Parsed credit SMS - Amount: {data['amount']}, Type: {data['type']}")


class TestPricing:
    """Pricing page API test"""
    
    def test_pricing_tiers(self):
        """Test pricing endpoint returns 3 tiers"""
        response = requests.get(f"{BASE_URL}/api/pricing")
        assert response.status_code == 200
        tiers = response.json()
        assert len(tiers) == 3
        # Check tier names and prices
        tier_names = [t["name"] for t in tiers]
        assert "Individual" in tier_names
        assert "Shop Owner" in tier_names
        assert "Accountant (CA)" in tier_names
        print(f"SUCCESS: Pricing - {len(tiers)} tiers")
        for t in tiers:
            print(f"  - {t['name']}: ₹{t['price']}/{t['period']}")


class TestAIChat:
    """AI Chat Assistant tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@capitalcare.ai",
            "password": "Admin@123"
        })
        self.cookies = login_resp.cookies
    
    def test_chat_empty_message(self):
        """Test chat rejects empty message"""
        response = requests.post(f"{BASE_URL}/api/ai/chat", json={
            "message": "",
            "persona": "individual"
        }, cookies=self.cookies)
        assert response.status_code == 400
        print("SUCCESS: Empty message rejected")
    
    def test_chat_history(self):
        """Test chat history endpoint"""
        response = requests.get(f"{BASE_URL}/api/ai/chat-history", cookies=self.cookies)
        assert response.status_code == 200
        history = response.json()
        assert isinstance(history, list)
        print(f"SUCCESS: Chat history - {len(history)} messages")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
