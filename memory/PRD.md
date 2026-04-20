# Capital Care AI — Personal Finance App PRD

## Architecture
- Backend: FastAPI + MongoDB + emergentintegrations (GPT-5.2 + Stripe)
- Frontend: React + Recharts + Phosphor Icons + Tailwind CSS
- Design: Cashly system (cream #F7F5F2, coral #F4845F, white cards, pill buttons)

## Implemented

### Phase 0 — Foundation
- Landing page, auth (register/login/logout), JWT httpOnly cookies
- Dashboard (Individual): 4 KPIs + sparklines, Income vs Expenses chart, Spending donut, 3-month forecast, Smart Insights, Savings goals preview, Health Score ring, Daily Spend Limit, Weekly Digest
- AI Chat Assistant (GPT-5.2 via Emergent LLM Key)
- PDF/CSV export, Bank SMS parser

### Phase 1 — Smart Money (Apr 2026)
- Budgets (category caps, progress bars, rollover, alerts)
- Loans & EMI (amortization table, prepayment simulator)
- Credit Cards (utilization, thresholds)
- Transactions CRUD, Goals with what-if planner, Auto-save rules
- Stripe subscription (Free / Pro $9.99 / Elite $19.99, monthly+yearly)
- Subscription detector (recurring charges from txn history)

### Phase 2 — Wealth Tracking (Apr 2026)
- Investments portfolio (stocks/MF/gold/FD/RD/crypto) with allocation donut, gain/loss
- Real Estate tracker (property log with appreciation %)
- Net Worth page (assets - liabilities breakdown with donut charts)
- Zero-Based Budget Planner (monthly income allocation, spent/remaining per category)
- Lend & Borrow log (directional entries, interest, settle flow)
- Debt Payoff Calculator (Avalanche vs Snowball comparison with recommendation)

### Phase 3 — Savings & Autopilot (Apr 2026)
- Savings Jars (multiple goals with color picker, deposit/withdraw, progress)
- SIP / RD Tracker (tenure, expected return, current value, projected maturity)
- FD Tracker (compounding monthly/quarterly/yearly, maturity date, days-to-maturity)

### Phase 4 — Tax & Compliance (Apr 2026)
- 80C/80D/80CCD(1B)/80E/80G/80TTA/24(b) deduction tracker with per-section limit, utilization %, estimated tax saved at 30%
- Tax Calendar for FY (advance tax, ITR, TDS, Form 16 — with past/upcoming/due_soon tagging)
- ITR Summary (auto-categorize transactions into salary/business/capital_gains/house_property/other_sources)
- Form 26AS PDF upload + parse (extracts TDS entries)
- Unusual-Spend Alerts (z-score-based anomaly detection per category)

## Test Results
- Backend: 24/24 Phase 2/3/4 (iter 8) + 28/28 Phase 1 (iter 7) = 52/52 (100%)
- Frontend: 100% — all 9 new pages render, dashboard 12-tile quick access

## Test credentials
- admin@capitalcare.ai / Admin@123 (see /app/memory/test_credentials.md)

## Refactor Backlog (P2)
- Split server.py (1621 lines) into /app/backend/routes and /models
- Cache loan amortization helper (reused in /api/loans and /api/net-worth)
- Server-side bounds validation (negative deposits, unrealistic rates)

## Future / Ideas (P3)
- Live market prices for stocks/MF/gold (Alpha Vantage or CoinGecko for crypto)
- Rental income/expense tracking per property
- Push notifications for unusual-spend alerts (web push or email)
- Tax regime comparator (old vs new)
- Mutual fund XIRR calculator
- Goal-based investment recommender (via GPT-5.2)
