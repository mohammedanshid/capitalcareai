# Capital Care AI — Personal Finance App PRD

## Architecture
- Backend: FastAPI + MongoDB + emergentintegrations (GPT-5.2 + Stripe)
- Frontend: React + Recharts + Phosphor Icons + Tailwind CSS
- Design: Cashly system (cream #F7F5F2, coral #F4845F, white cards, pill buttons)

## Plan Tiers & Feature Gating (Apr 2026)

### Pricing
- **Free** — $0 forever
- **Pro** — $4.99/month (Stripe: `https://buy.stripe.com/14AbJ3akQ9HCgDB8U4bbG02`)
- **Elite** — $9.99/month (Stripe: `https://buy.stripe.com/4gMeVffFa3jecnlfisbbG03`)

### Feature access
| Feature | Free | Pro | Elite |
|---|---|---|---|
| Transactions, Goals, Insights | ✓ | ✓ | ✓ |
| Savings Jars | 1 only | Unlimited | Unlimited |
| Budgets, Zero-Based Budget, Loans, Credit Cards | 🔒 Pro | ✓ | ✓ |
| SIP/RD/FD, Lend & Borrow, Tax 80C | 🔒 Pro | ✓ | ✓ |
| Weekly Digest, Daily Limit, Export PDF/CSV | 🔒 Pro | ✓ | ✓ |
| Health Score full breakdown | 🔒 Pro | ✓ | ✓ |
| Debt Payoff, Investments, Real Estate, Net Worth | 🔒 Elite | 🔒 Elite | ✓ |
| AI Chat, Form 26AS upload | 🔒 Elite | 🔒 Elite | ✓ |

### UX behaviour
- Dashboard tiles show lock icon (grey for Pro, gold for Elite) with slightly reduced opacity
- Click → bottom-sheet `UpgradeModal` with plan price and Stripe CTA (opens in new tab with `?prefilled_email=` pre-filled)
- Direct route access on gated pages → `PlanGate` screen, auto-returns to dashboard on cancel
- Plan badge in header (grey/coral/gold-with-crown), subscription card below digest
- Plan change via webhook: match by email + amount (499¢=pro, 999¢=elite) → updates `users.plan` + audit log

## Implemented

### Phase 0 — Foundation
- Landing page, JWT httpOnly auth, Dashboard with KPIs/charts/forecast/health-score/daily-limit/weekly-digest
- AI Chat Assistant (GPT-5.2), PDF/CSV export, Bank SMS parser

### Phase 1 — Smart Money
- Budgets (caps, rollover), Loans & EMI (amortization, prepayment), Credit Cards (utilization)
- Transactions, Goals with auto-save rules, Subscription detector
- Stripe 3-tier subscription

### Phase 2 — Wealth Tracking
- Investments (stocks/MF/gold/FD/RD/crypto) with allocation donut
- Real Estate tracker, Net Worth page
- Zero-Based Budget Planner, Lend & Borrow log
- Debt Payoff Calculator (Avalanche vs Snowball)

### Phase 3 — Savings & Autopilot
- Savings Jars (deposit/withdraw, color), SIP/RD/FD Tracker

### Phase 4 — Tax & Compliance
- 80C/80D/80CCD(1B)/80E/80G/80TTA/24(b) deduction tracker
- Tax Calendar, ITR auto-categorization, Form 26AS PDF parse, Unusual-spend alerts

### Plan Gating & Stripe Payment Links (this session)
- Central `plan.js` utility, `UpgradeModal` bottom sheet, `PlanGate` route guard
- Dashboard tile gating with lock icons
- Pricing page rewritten with $4.99/$9.99 and direct payment links
- AuthContext refreshes user on window focus (picks up plan updates after Stripe return)
- Webhook handles direct payment links (email + amount matching) + writes to admin_audit_log

## Test Results
- Backend 58/58 (Phase 1: 28, Phase 2-4: 24, Gating: 6) — 100%
- Frontend 100% — all plan tiers verified

## Credentials
- admin@capitalcare.ai / Admin@123 (see /app/memory/test_credentials.md)

## Next / Backlog
- **P0**: Stripe webhook URL configuration (needs to be set in Stripe dashboard for live payments)
- **P1**: "Welcome to Pro/Elite" confetti modal on first post-upgrade dashboard load
- **P1**: Stripe Customer Portal link for subscription management
- **P1**: Payment-failed red banner when `subscription_status=payment_failed`
- **P2**: Split server.py (1668 lines) into /routes + /models
- **P2**: Server-side enforcement (currently gating is client-side — Pro/Elite routes should also block on backend)
- **P3**: Live market prices (Alpha Vantage/CoinGecko), XIRR calculator, tax regime comparator
