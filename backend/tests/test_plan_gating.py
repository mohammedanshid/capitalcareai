"""Plan-gating tests: verify login/me/refresh-plan return plan + subscription_status."""
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://finance-ai-coach-1.preview.emergentagent.com').rstrip('/')

ADMIN_EMAIL = "admin@capitalcare.ai"
ADMIN_PW = "Admin@123"


@pytest.fixture(scope="module")
def client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PW})
    assert r.status_code == 200, f"login failed: {r.text}"
    return s


class TestLoginReturnsPlanFields:
    def test_login_returns_plan_and_subscription_status(self):
        r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PW})
        assert r.status_code == 200
        d = r.json()
        assert "plan" in d, f"login response missing 'plan': {d}"
        assert "subscription_status" in d, f"login response missing 'subscription_status': {d}"
        assert d["plan"] in ["free", "pro", "elite"], f"bad plan value: {d['plan']}"
        assert d["subscription_status"] in ["active", "inactive", "cancelled", "trialing"]
        assert d["email"] == ADMIN_EMAIL

    def test_me_returns_plan(self, client):
        r = client.get(f"{BASE_URL}/api/auth/me")
        assert r.status_code == 200
        d = r.json()
        assert "plan" in d
        assert d["plan"] in ["free", "pro", "elite"]


class TestRefreshPlan:
    def test_refresh_plan_returns_plan_fields(self, client):
        r = client.post(f"{BASE_URL}/api/user/refresh-plan")
        assert r.status_code == 200, r.text
        d = r.json()
        assert "plan" in d
        assert "subscription_status" in d
        assert d["plan"] in ["free", "pro", "elite"]

    def test_refresh_plan_requires_auth(self):
        r = requests.post(f"{BASE_URL}/api/user/refresh-plan")
        assert r.status_code in [401, 403]

    def test_user_plan_endpoint_still_works(self, client):
        r = client.get(f"{BASE_URL}/api/user/plan")
        assert r.status_code == 200
        d = r.json()
        assert d["plan"] in ["free", "pro", "elite"]


class TestPhase1Phase2Regression:
    """Smoke regression across prior phase endpoints."""
    def test_core_endpoints(self, client):
        endpoints = [
            "/api/budgets", "/api/loans", "/api/credit-cards", "/api/health-score",
            "/api/daily-limit", "/api/weekly-digest", "/api/subscriptions",
            "/api/autosave-rules", "/api/investments", "/api/real-estate",
            "/api/net-worth", "/api/lend-borrow", "/api/jars", "/api/sip-rd",
            "/api/fds", "/api/tax-calendar/2025-26", "/api/itr-summary/2025-26",
            "/api/deductions/2025-26", "/api/unusual-alerts",
        ]
        failures = []
        for ep in endpoints:
            r = client.get(f"{BASE_URL}{ep}")
            if r.status_code != 200:
                failures.append(f"{ep}: {r.status_code}")
        assert not failures, f"regressions: {failures}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
