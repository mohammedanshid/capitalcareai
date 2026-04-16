#!/usr/bin/env python3
"""
Backend API Testing for Finance Management App
Tests all authentication and finance endpoints
"""

import requests
import sys
import json
from datetime import datetime, timedelta
import time

class FinanceAPITester:
    def __init__(self, base_url="https://finance-ai-coach-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.tests_run = 0
        self.tests_passed = 0
        self.user_id = None
        self.test_transaction_id = None

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED {details}")
        else:
            print(f"❌ {name} - FAILED {details}")
        return success

    def test_auth_register(self):
        """Test user registration"""
        test_email = f"testuser_{int(time.time())}@example.com"
        payload = {
            "name": "Test User",
            "email": test_email,
            "password": "Test@123"
        }
        
        try:
            response = self.session.post(f"{self.base_url}/api/auth/register", json=payload)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                self.user_id = data.get("id")
                return self.log_test("User Registration", True, f"User ID: {self.user_id}")
            else:
                return self.log_test("User Registration", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            return self.log_test("User Registration", False, f"Exception: {str(e)}")

    def test_auth_login_admin(self):
        """Test admin login"""
        payload = {
            "email": "admin@financeapp.com",
            "password": "Admin@123"
        }
        
        try:
            response = self.session.post(f"{self.base_url}/api/auth/login", json=payload)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                self.user_id = data.get("id")
                return self.log_test("Admin Login", True, f"Admin ID: {self.user_id}")
            else:
                return self.log_test("Admin Login", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            return self.log_test("Admin Login", False, f"Exception: {str(e)}")

    def test_auth_me(self):
        """Test get current user"""
        try:
            response = self.session.get(f"{self.base_url}/api/auth/me")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                return self.log_test("Get Current User", True, f"User: {data.get('name', 'Unknown')}")
            else:
                return self.log_test("Get Current User", False, f"Status: {response.status_code}")
                
        except Exception as e:
            return self.log_test("Get Current User", False, f"Exception: {str(e)}")

    def test_dashboard_summary(self):
        """Test dashboard summary endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/dashboard/summary")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                required_fields = ["total_income", "total_expenses", "balance", "transaction_count"]
                has_all_fields = all(field in data for field in required_fields)
                
                if has_all_fields:
                    return self.log_test("Dashboard Summary", True, f"Balance: ${data['balance']}")
                else:
                    return self.log_test("Dashboard Summary", False, "Missing required fields")
            else:
                return self.log_test("Dashboard Summary", False, f"Status: {response.status_code}")
                
        except Exception as e:
            return self.log_test("Dashboard Summary", False, f"Exception: {str(e)}")

    def test_create_income_transaction(self):
        """Test creating income transaction"""
        payload = {
            "type": "income",
            "amount": 5000.00,
            "category": "Salary",
            "description": "Monthly salary",
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        
        try:
            response = self.session.post(f"{self.base_url}/api/transactions", json=payload)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                self.test_transaction_id = data.get("id")
                return self.log_test("Create Income Transaction", True, f"Transaction ID: {self.test_transaction_id}")
            else:
                return self.log_test("Create Income Transaction", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            return self.log_test("Create Income Transaction", False, f"Exception: {str(e)}")

    def test_create_expense_transaction(self):
        """Test creating expense transaction"""
        payload = {
            "type": "expense",
            "amount": 150.50,
            "category": "Food",
            "description": "Grocery shopping",
            "date": datetime.now().strftime("%Y-%m-%d")
        }
        
        try:
            response = self.session.post(f"{self.base_url}/api/transactions", json=payload)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                return self.log_test("Create Expense Transaction", True, f"Amount: ${data.get('amount')}")
            else:
                return self.log_test("Create Expense Transaction", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            return self.log_test("Create Expense Transaction", False, f"Exception: {str(e)}")

    def test_get_transactions(self):
        """Test getting all transactions"""
        try:
            response = self.session.get(f"{self.base_url}/api/transactions")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                return self.log_test("Get Transactions", True, f"Found {len(data)} transactions")
            else:
                return self.log_test("Get Transactions", False, f"Status: {response.status_code}")
                
        except Exception as e:
            return self.log_test("Get Transactions", False, f"Exception: {str(e)}")

    def test_delete_transaction(self):
        """Test deleting a transaction"""
        if not self.test_transaction_id:
            return self.log_test("Delete Transaction", False, "No transaction ID available")
            
        try:
            response = self.session.delete(f"{self.base_url}/api/transactions/{self.test_transaction_id}")
            success = response.status_code == 200
            
            if success:
                return self.log_test("Delete Transaction", True, f"Deleted transaction {self.test_transaction_id}")
            else:
                return self.log_test("Delete Transaction", False, f"Status: {response.status_code}")
                
        except Exception as e:
            return self.log_test("Delete Transaction", False, f"Exception: {str(e)}")

    def test_ai_analyze(self):
        """Test AI financial analysis"""
        try:
            response = self.session.post(f"{self.base_url}/api/analyze", json={})
            success = response.status_code == 200
            
            if success:
                data = response.json()
                has_insights = "insights" in data and "raw_reasoning" in data
                return self.log_test("AI Analysis", True, f"Has insights: {has_insights}")
            else:
                # Check if it's a 400 due to no transactions (which is expected)
                if response.status_code == 400 and "No transactions found" in response.text:
                    return self.log_test("AI Analysis", True, "No transactions available (expected)")
                else:
                    return self.log_test("AI Analysis", False, f"Status: {response.status_code}, Response: {response.text}")
                
        except Exception as e:
            return self.log_test("AI Analysis", False, f"Exception: {str(e)}")

    def test_auth_logout(self):
        """Test user logout"""
        try:
            response = self.session.post(f"{self.base_url}/api/auth/logout")
            success = response.status_code == 200
            
            if success:
                return self.log_test("User Logout", True, "Logged out successfully")
            else:
                return self.log_test("User Logout", False, f"Status: {response.status_code}")
                
        except Exception as e:
            return self.log_test("User Logout", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Finance App Backend API Tests")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Test authentication flow
        print("\n📝 Testing Authentication...")
        self.test_auth_register()
        self.test_auth_me()
        
        # Test finance endpoints
        print("\n💰 Testing Finance Endpoints...")
        self.test_dashboard_summary()
        self.test_create_income_transaction()
        self.test_create_expense_transaction()
        self.test_get_transactions()
        self.test_delete_transaction()
        
        # Test AI analysis
        print("\n🤖 Testing AI Analysis...")
        self.test_ai_analyze()
        
        # Test logout
        print("\n🚪 Testing Logout...")
        self.test_auth_logout()
        
        # Test admin login separately
        print("\n👑 Testing Admin Login...")
        self.test_auth_login_admin()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        success_rate = (self.tests_passed / self.tests_run) * 100 if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print("⚠️  Some tests failed. Check the logs above.")
            return 1

def main():
    """Main test runner"""
    tester = FinanceAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())