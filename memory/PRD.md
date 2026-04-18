# Capital Care AI — Multi-Persona Fintech App PRD

## Problem Statement
Multi-persona fintech app for Indian market. 3 personas: Individual, Shop Owner, CA.

## Architecture
- Backend: FastAPI + MongoDB + emergentintegrations (OpenAI GPT-5.2)
- Frontend: React + Recharts + Phosphor Icons + Tailwind CSS
- Auth: JWT httpOnly cookies + bcrypt
- Design: 3 persona themes (green/amber/blue), dark mode, mobile-first

## Implemented Features (April 18, 2026)
### Core
- [x] Single login → Persona picker → 3 distinct dashboards
- [x] INR formatting (₹ symbol, Indian number system)
- [x] Dark mode with persistence
- [x] Mobile-first responsive + bottom navigation per persona

### Individual Persona
- [x] 4 KPI cards (Income, Expenses, Savings Rate, Net Worth) with sparklines
- [x] Donut chart (spending by category), Line chart (6-month trends)
- [x] Transaction CRUD with search + bank SMS paste-and-parse
- [x] Savings Goals with progress bars + what-if planner
- [x] AI Chat Assistant (persona-aware GPT-5.2 coaching)
- [x] Smart Alerts (spending spikes, low savings, goal progress)
- [x] 3-Month Cash Flow Forecast
- [x] Export PDF + CSV reports

### Shop Owner Persona
- [x] 3 KPI cards (Revenue, Cash in Hand, Pending Payments)
- [x] Cash Summary (opening/closing/credited/debited/ratio bar)
- [x] Credit/Debit quick entry via bottom sheets
- [x] Real-time transaction feed, ledger with daily grouping
- [x] Weekly cash flow bar chart
- [x] AI Chat Assistant (business-focused advice)
- [x] Smart Alerts (overdue payments, low-revenue days)
- [x] 30/60/90 Day Cash Flow Forecast

### CA Persona
- [x] Client management with status badges (On Track/Overdue/Pending Docs)
- [x] Task management (create/toggle/delete, grouped by status)
- [x] AI Chat Assistant (tax law, compliance guidance)
- [x] Smart Alerts (task overload, client overdue)

### Global
- [x] Pricing Page (₹99/₹299/₹999)
- [x] Persona switching from any dashboard

## Test Results: Backend 39/39 (100%) | Frontend 100%

## P1 Backlog
- Full CA client portal (read-only login)
- GST/TDS/ITR report generation
- Bulk CSV import, Recurring detection, Malayalam support, Offline mode
