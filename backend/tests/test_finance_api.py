"""
Backend API Tests for Finance App - Iteration 2
Tests: Auth, Transactions, Dashboard, Categories, Budgets, Recurring, Export
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@financeapp.com"
ADMIN_PASSWORD = "Admin@123"
TEST_USER_EMAIL = f"TEST_user_{datetime.now().strftime('%H%M%S')}@example.com"
TEST_USER_PASSWORD = "Test@123"
TEST_USER_NAME = "Test User"


class TestHealthAndAuth:
    """Authentication endpoint tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_register_new_user(self):
        """Test user registration"""
        response = self.session.post(f"{BASE_URL}/api/auth/register", json={
            "name": TEST_USER_NAME,
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        assert response.status_code == 200, f"Registration failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["email"] == TEST_USER_EMAIL.lower()
        assert data["name"] == TEST_USER_NAME
        print(f"SUCCESS: User registered - {data['email']}")
    
    def test_login_admin(self):
        """Test admin login"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["email"] == ADMIN_EMAIL
        assert "access_token" in response.cookies or "set-cookie" in response.headers
        print(f"SUCCESS: Admin logged in - {data['email']}")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("SUCCESS: Invalid credentials rejected")
    
    def test_get_me_authenticated(self):
        """Test /auth/me endpoint"""
        # Login first
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_response.status_code == 200
        
        # Get user info
        response = self.session.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == ADMIN_EMAIL
        print(f"SUCCESS: /auth/me returned user info")
    
    def test_logout(self):
        """Test logout endpoint"""
        # Login first
        self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        # Logout
        response = self.session.post(f"{BASE_URL}/api/auth/logout")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print("SUCCESS: Logout successful")


class TestTransactions:
    """Transaction CRUD tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        # Login
        self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
    
    def test_create_income_transaction(self):
        """Test creating income transaction"""
        response = self.session.post(f"{BASE_URL}/api/transactions", json={
            "type": "income",
            "amount": 500.00,
            "category": "Salary",
            "description": "TEST_income_transaction",
            "date": datetime.now().strftime("%Y-%m-%d")
        })
        assert response.status_code == 200, f"Create failed: {response.text}"
        data = response.json()
        assert data["type"] == "income"
        assert data["amount"] == 500.00
        assert data["category"] == "Salary"
        print(f"SUCCESS: Income transaction created - ID: {data.get('id')}")
        return data
    
    def test_create_expense_transaction(self):
        """Test creating expense transaction"""
        response = self.session.post(f"{BASE_URL}/api/transactions", json={
            "type": "expense",
            "amount": 75.50,
            "category": "Food",
            "description": "TEST_expense_transaction",
            "date": datetime.now().strftime("%Y-%m-%d")
        })
        assert response.status_code == 200, f"Create failed: {response.text}"
        data = response.json()
        assert data["type"] == "expense"
        assert data["amount"] == 75.50
        assert data["category"] == "Food"
        print(f"SUCCESS: Expense transaction created - ID: {data.get('id')}")
        return data
    
    def test_get_transactions(self):
        """Test getting all transactions"""
        response = self.session.get(f"{BASE_URL}/api/transactions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: Retrieved {len(data)} transactions")
    
    def test_delete_transaction(self):
        """Test deleting a transaction"""
        # Create a transaction first
        create_response = self.session.post(f"{BASE_URL}/api/transactions", json={
            "type": "expense",
            "amount": 10.00,
            "category": "Other Expense",
            "description": "TEST_to_delete",
            "date": datetime.now().strftime("%Y-%m-%d")
        })
        assert create_response.status_code == 200
        trans_id = create_response.json().get("id")
        
        # Delete it
        delete_response = self.session.delete(f"{BASE_URL}/api/transactions/{trans_id}")
        assert delete_response.status_code == 200
        print(f"SUCCESS: Transaction deleted - ID: {trans_id}")
    
    def test_invalid_transaction_type(self):
        """Test creating transaction with invalid type"""
        response = self.session.post(f"{BASE_URL}/api/transactions", json={
            "type": "invalid",
            "amount": 100.00,
            "category": "Food",
            "date": datetime.now().strftime("%Y-%m-%d")
        })
        assert response.status_code == 400
        print("SUCCESS: Invalid transaction type rejected")


class TestDashboard:
    """Dashboard summary tests - Iteration 3: KPI cards with sparklines and trends"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
    
    def test_get_dashboard_summary(self):
        """Test dashboard summary endpoint"""
        response = self.session.get(f"{BASE_URL}/api/dashboard/summary")
        assert response.status_code == 200
        data = response.json()
        assert "total_income" in data
        assert "total_expenses" in data
        assert "balance" in data
        assert "transaction_count" in data
        print(f"SUCCESS: Dashboard summary - Income: ${data['total_income']}, Expenses: ${data['total_expenses']}, Balance: ${data['balance']}")
    
    def test_dashboard_summary_sparklines(self):
        """Test dashboard summary returns sparkline data for KPI cards"""
        response = self.session.get(f"{BASE_URL}/api/dashboard/summary")
        assert response.status_code == 200
        data = response.json()
        
        # Verify sparkline arrays exist
        assert "sparkline_income" in data, "Missing sparkline_income"
        assert "sparkline_expenses" in data, "Missing sparkline_expenses"
        assert "sparkline_profit" in data, "Missing sparkline_profit"
        assert "sparkline_cashflow" in data, "Missing sparkline_cashflow"
        
        # Verify they are lists
        assert isinstance(data["sparkline_income"], list), "sparkline_income should be a list"
        assert isinstance(data["sparkline_expenses"], list), "sparkline_expenses should be a list"
        assert isinstance(data["sparkline_profit"], list), "sparkline_profit should be a list"
        assert isinstance(data["sparkline_cashflow"], list), "sparkline_cashflow should be a list"
        
        print(f"SUCCESS: Sparkline data present - income: {len(data['sparkline_income'])} points, expenses: {len(data['sparkline_expenses'])} points")
    
    def test_dashboard_summary_trends(self):
        """Test dashboard summary returns trend percentages for KPI cards"""
        response = self.session.get(f"{BASE_URL}/api/dashboard/summary")
        assert response.status_code == 200
        data = response.json()
        
        # Verify trend values exist
        assert "trend_income" in data, "Missing trend_income"
        assert "trend_expenses" in data, "Missing trend_expenses"
        assert "trend_profit" in data, "Missing trend_profit"
        assert "trend_cashflow" in data, "Missing trend_cashflow"
        
        # Verify they are numbers
        assert isinstance(data["trend_income"], (int, float)), "trend_income should be a number"
        assert isinstance(data["trend_expenses"], (int, float)), "trend_expenses should be a number"
        assert isinstance(data["trend_profit"], (int, float)), "trend_profit should be a number"
        assert isinstance(data["trend_cashflow"], (int, float)), "trend_cashflow should be a number"
        
        print(f"SUCCESS: Trend data present - income: {data['trend_income']}%, expenses: {data['trend_expenses']}%, profit: {data['trend_profit']}%, cashflow: {data['trend_cashflow']}%")
    
    def test_dashboard_summary_monthly_series(self):
        """Test dashboard summary returns monthly series for primary line chart"""
        response = self.session.get(f"{BASE_URL}/api/dashboard/summary")
        assert response.status_code == 200
        data = response.json()
        
        # Verify monthly_series exists and is a list
        assert "monthly_series" in data, "Missing monthly_series"
        assert isinstance(data["monthly_series"], list), "monthly_series should be a list"
        
        # If there's data, verify structure
        if len(data["monthly_series"]) > 0:
            first_month = data["monthly_series"][0]
            assert "month" in first_month, "monthly_series item missing 'month'"
            assert "income" in first_month, "monthly_series item missing 'income'"
            assert "expenses" in first_month, "monthly_series item missing 'expenses'"
            assert "profit" in first_month, "monthly_series item missing 'profit'"
            print(f"SUCCESS: Monthly series has {len(data['monthly_series'])} months with income/expenses/profit data")
        else:
            print("INFO: Monthly series is empty (no transactions yet)")
    
    def test_dashboard_summary_cash_flow(self):
        """Test dashboard summary returns cash_flow field"""
        response = self.session.get(f"{BASE_URL}/api/dashboard/summary")
        assert response.status_code == 200
        data = response.json()
        
        assert "cash_flow" in data, "Missing cash_flow"
        assert isinstance(data["cash_flow"], (int, float)), "cash_flow should be a number"
        print(f"SUCCESS: Cash flow present: ${data['cash_flow']}")


class TestCategories:
    """Category management tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
    
    def test_get_categories(self):
        """Test getting all categories"""
        response = self.session.get(f"{BASE_URL}/api/categories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0  # Should have default categories
        print(f"SUCCESS: Retrieved {len(data)} categories")
    
    def test_create_custom_category(self):
        """Test creating custom category"""
        response = self.session.post(f"{BASE_URL}/api/categories", json={
            "name": "TEST_Custom_Category",
            "type": "expense",
            "icon": "🧪"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "TEST_Custom_Category"
        assert data["type"] == "expense"
        print(f"SUCCESS: Custom category created - {data['name']}")
        return data
    
    def test_delete_custom_category(self):
        """Test deleting custom category"""
        # Create first
        create_response = self.session.post(f"{BASE_URL}/api/categories", json={
            "name": "TEST_To_Delete_Category",
            "type": "income"
        })
        assert create_response.status_code == 200
        cat_id = create_response.json().get("id")
        
        # Delete
        delete_response = self.session.delete(f"{BASE_URL}/api/categories/{cat_id}")
        assert delete_response.status_code == 200
        print(f"SUCCESS: Category deleted - ID: {cat_id}")


class TestBudgets:
    """Budget management tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
    
    def test_get_budgets(self):
        """Test getting all budgets"""
        response = self.session.get(f"{BASE_URL}/api/budgets")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: Retrieved {len(data)} budgets")
    
    def test_create_budget(self):
        """Test creating a budget"""
        # Use a unique category name to avoid conflicts
        unique_category = f"TEST_Budget_Cat_{datetime.now().strftime('%H%M%S')}"
        response = self.session.post(f"{BASE_URL}/api/budgets", json={
            "category": unique_category,
            "limit": 500.00,
            "period": "monthly"
        })
        assert response.status_code == 200, f"Create budget failed: {response.text}"
        data = response.json()
        assert data["category"] == unique_category
        assert data["limit"] == 500.00
        assert data["status"] == "safe"
        print(f"SUCCESS: Budget created - {data['category']}: ${data['limit']}")
        return data
    
    def test_delete_budget(self):
        """Test deleting a budget"""
        # Create first
        unique_category = f"TEST_Delete_Budget_{datetime.now().strftime('%H%M%S')}"
        create_response = self.session.post(f"{BASE_URL}/api/budgets", json={
            "category": unique_category,
            "limit": 100.00,
            "period": "monthly"
        })
        assert create_response.status_code == 200
        budget_id = create_response.json().get("id")
        
        # Delete
        delete_response = self.session.delete(f"{BASE_URL}/api/budgets/{budget_id}")
        assert delete_response.status_code == 200
        print(f"SUCCESS: Budget deleted - ID: {budget_id}")


class TestRecurringTransactions:
    """Recurring transaction tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
    
    def test_get_recurring_transactions(self):
        """Test getting recurring transactions"""
        response = self.session.get(f"{BASE_URL}/api/recurring-transactions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"SUCCESS: Retrieved {len(data)} recurring transactions")
    
    def test_create_recurring_transaction(self):
        """Test creating recurring transaction"""
        response = self.session.post(f"{BASE_URL}/api/recurring-transactions", json={
            "type": "expense",
            "amount": 50.00,
            "category": "Bills",
            "description": "TEST_recurring_bill",
            "frequency": "monthly",
            "start_date": datetime.now().strftime("%Y-%m-%d")
        })
        assert response.status_code == 200, f"Create failed: {response.text}"
        data = response.json()
        assert data["type"] == "expense"
        assert data["amount"] == 50.00
        assert data["frequency"] == "monthly"
        assert data["is_active"] == True
        print(f"SUCCESS: Recurring transaction created - ID: {data.get('id')}")
        return data
    
    def test_delete_recurring_transaction(self):
        """Test deleting recurring transaction"""
        # Create first
        create_response = self.session.post(f"{BASE_URL}/api/recurring-transactions", json={
            "type": "income",
            "amount": 100.00,
            "category": "Salary",
            "description": "TEST_to_delete_recurring",
            "frequency": "weekly",
            "start_date": datetime.now().strftime("%Y-%m-%d")
        })
        assert create_response.status_code == 200
        recurring_id = create_response.json().get("id")
        
        # Delete
        delete_response = self.session.delete(f"{BASE_URL}/api/recurring-transactions/{recurring_id}")
        assert delete_response.status_code == 200
        print(f"SUCCESS: Recurring transaction deleted - ID: {recurring_id}")


class TestExport:
    """Export functionality tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
    
    def test_export_csv(self):
        """Test CSV export"""
        response = self.session.get(f"{BASE_URL}/api/export/csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
        assert len(response.content) > 0
        print(f"SUCCESS: CSV export - {len(response.content)} bytes")
    
    def test_export_pdf(self):
        """Test PDF export"""
        response = self.session.get(f"{BASE_URL}/api/export/pdf")
        assert response.status_code == 200
        assert "application/pdf" in response.headers.get("content-type", "")
        assert len(response.content) > 0
        print(f"SUCCESS: PDF export - {len(response.content)} bytes")


class TestAIAnalysis:
    """AI Analysis endpoint tests - Iteration 3: includes /api/analyze/latest for sidebar"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
    
    def test_analyze_finances(self):
        """Test AI analysis endpoint"""
        response = self.session.post(f"{BASE_URL}/api/analyze", timeout=60)
        # May return 400 if no transactions, or 200 with insights
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}"
        if response.status_code == 200:
            data = response.json()
            assert "insights" in data
            assert "raw_reasoning" in data
            assert "created_at" in data
            print(f"SUCCESS: AI analysis completed - insights length: {len(data['insights'])}")
        else:
            print("INFO: AI analysis returned 400 (likely no transactions)")
    
    def test_get_latest_analysis(self):
        """Test /api/analyze/latest endpoint for Quick Insights sidebar"""
        response = self.session.get(f"{BASE_URL}/api/analyze/latest")
        assert response.status_code == 200, f"Latest analysis failed: {response.text}"
        data = response.json()
        
        # Should always have has_analysis field
        assert "has_analysis" in data, "Missing has_analysis field"
        assert isinstance(data["has_analysis"], bool), "has_analysis should be boolean"
        
        if data["has_analysis"]:
            assert "insights" in data, "Missing insights when has_analysis is true"
            assert "created_at" in data, "Missing created_at when has_analysis is true"
            print(f"SUCCESS: Latest analysis found - insights length: {len(data.get('insights', ''))}")
        else:
            print("INFO: No previous analysis found (has_analysis=false)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
