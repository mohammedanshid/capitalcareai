# FinFlow — Multi-Persona Fintech App PRD

## Problem Statement
Build a complete multi-persona fintech app for the Indian market with 3 user dashboards: Individual, Shop Owner, Accountant (CA).

## Architecture
- Backend: FastAPI + MongoDB + emergentintegrations (OpenAI GPT-5.2)
- Frontend: React + Recharts + Phosphor Icons + Tailwind CSS
- Auth: JWT with httpOnly cookies, bcrypt
- Design: 3 persona-specific themes (green/amber/blue), dark mode, mobile-first

## What's Been Implemented (April 18, 2026)
- [x] Single login → Persona picker with 3 animated cards
- [x] Individual Dashboard: 4 KPIs, donut chart, line chart, sparklines
- [x] Individual Transactions: CRUD, search, filter, bank SMS parsing
- [x] Individual Goals: Create goals, progress bars, what-if planner, quick-add savings
- [x] Shop Owner Dashboard: 3 KPIs, Cash Summary, Credit/Debit bottom sheets, daily feed
- [x] Shop Owner Ledger: Full ledger grouped by date with net calculations
- [x] CA Dashboard: 4 summary stats, client list with status badges, search
- [x] CA Tasks: Task CRUD, status toggle, grouped by overdue/pending/completed
- [x] AI Insights (persona-aware) for all personas
- [x] SMS Parser (regex-based for Indian bank SMS)
- [x] Pricing Page: 3 tiers (₹99/₹299/₹999) with feature comparison
- [x] INR formatting (₹ symbol, Indian number system: lakhs/crores)
- [x] Dark mode with localStorage persistence
- [x] Mobile-first responsive layout with bottom navigation per persona
- [x] Persona switching from any dashboard

## Test Results: Backend 43/43 (100%) | Frontend 100%

## Prioritized Backlog
### P1
- Full CA client portal (read-only client login)
- GST/TDS/ITR report generation
- Bulk CSV/Excel import for CA
- Recurring transaction detection for Individual
- Monthly summary PDF export

### P2
- Malayalam language support
- Offline mode (view + sync)
- Multi-currency + forex for CA
- UPI auto-detection
- Push notifications for upcoming deadlines
