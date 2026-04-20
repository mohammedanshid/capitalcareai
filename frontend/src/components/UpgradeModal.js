import React from 'react';
import { Lock, X, Crown } from '@phosphor-icons/react';
import { PLAN_PRICES, stripeLinkFor } from '../utils/plan';
import { useAuth } from '../context/AuthContext';

const DESCRIPTIONS = {
  budgets: ['Smart Budgeting', 'Category budget caps, progress bars and warnings.'],
  zero_budget: ['Zero-Based Budget Planner', 'Allocate every rupee of income to a category each month.'],
  loans: ['Loans & EMI Tracker', 'Amortization schedule and prepayment simulator.'],
  credit_cards: ['Credit Cards Manager', 'Track utilization, due dates and statements across cards.'],
  sip_rd: ['SIP · RD · FD Tracker', 'Monthly SIPs, recurring deposits and fixed deposits with projected maturity.'],
  jars_unlimited: ['Unlimited Savings Jars', 'Create unlimited themed jars for every savings goal.'],
  lend_borrow: ['Lend & Borrow Log', 'Track who owes you and whom you owe.'],
  tax_basic: ['Tax & 80C', 'Deduction tracker, tax calendar and ITR categorization.'],
  weekly_digest: ['Weekly Digest', 'Weekly money recap delivered on your dashboard.'],
  subscription_detector: ['Subscription Detector', 'Auto-detect recurring charges.'],
  daily_limit: ['Daily Spend Limit', 'Set and monitor daily spending caps.'],
  export_pdf_csv: ['PDF & CSV Export', 'Export transactions and reports.'],
  health_score_full: ['Full Health Score', 'Complete breakdown and personalised tips.'],
  debt_payoff: ['Debt Payoff Calculator', 'Avalanche vs Snowball with interest saved comparison.'],
  investments: ['Investment Portfolio', 'Stocks, mutual funds, gold and crypto with allocation donut.'],
  real_estate: ['Real Estate Tracker', 'Log properties with appreciation tracking.'],
  net_worth: ['Net Worth Tracker', 'Your complete asset vs liability picture.'],
  ai_chat: ['AI Chat Assistant', 'Unlimited GPT-5.2 powered finance advisor.'],
  form_26as: ['Form 26AS Upload', 'Upload your 26AS PDF and auto-extract TDS entries.'],
};

export const UpgradeModal = ({ open, onClose, feature, requiredPlan }) => {
  const { user } = useAuth();
  if (!open) return null;
  const [title, desc] = DESCRIPTIONS[feature] || ['Premium Feature', 'Upgrade to unlock.'];
  const price = PLAN_PRICES[requiredPlan] || 4.99;
  const stripeUrl = stripeLinkFor(requiredPlan, user?.email);
  const planLabel = requiredPlan === 'elite' ? 'Elite' : 'Pro';
  const cta = requiredPlan === 'elite' ? 'Go Elite' : 'Upgrade to Pro';
  const gold = requiredPlan === 'elite';

  return (
    <div className="fixed inset-0 z-[100] flex items-end sm:items-center justify-center bg-black/50 backdrop-blur-sm px-0 sm:px-4" onClick={onClose} data-testid="upgrade-modal">
      <div className="w-full sm:max-w-md bg-white rounded-t-3xl sm:rounded-3xl p-6 shadow-2xl animate-in slide-in-from-bottom duration-300" onClick={e => e.stopPropagation()}>
        <button onClick={onClose} className="absolute top-4 right-4 p-1 text-[var(--muted)] hover:text-[var(--dark)]" data-testid="close-modal"><X size={20} /></button>
        <div className="flex flex-col items-center text-center">
          <div className="w-16 h-16 rounded-2xl flex items-center justify-center mb-4" style={{ background: gold ? 'linear-gradient(135deg, #FFD700, #FFA500)' : 'linear-gradient(135deg, #F4845F, #e06b47)' }}>
            {gold ? <Crown size={32} weight="fill" className="text-white" /> : <Lock size={30} weight="fill" className="text-white" />}
          </div>
          <h3 className="text-xl font-bold text-[var(--dark)]" data-testid="upgrade-title">{title}</h3>
          <p className="text-sm text-[var(--text-secondary)] mt-1 px-2">{desc}</p>
          <div className="w-full mt-5 p-4 rounded-2xl bg-[var(--cream-light)] border border-[var(--border)]">
            <p className="text-xs text-[var(--muted)] uppercase tracking-wider">Included in</p>
            <p className="text-lg font-bold text-[var(--dark)] mt-0.5">{planLabel} Plan · ${price}/month</p>
          </div>
          <div className="flex flex-col gap-2 w-full mt-5">
            <a href={stripeUrl} target="_blank" rel="noopener noreferrer" onClick={onClose} data-testid="upgrade-cta" className="w-full h-12 rounded-full flex items-center justify-center text-sm font-semibold text-white transition-all hover:opacity-90" style={{ background: gold ? 'linear-gradient(135deg, #FFD700, #FFA500)' : 'var(--coral)' }}>
              {cta} · ${price}/mo
            </a>
            <button onClick={onClose} className="w-full h-11 rounded-full text-sm font-semibold text-[var(--muted)] border border-[var(--border)] hover:bg-[var(--cream-light)]" data-testid="maybe-later">Maybe later</button>
          </div>
        </div>
      </div>
    </div>
  );
};
