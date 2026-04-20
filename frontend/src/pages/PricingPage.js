import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Check, Star, ShieldCheck, Crown } from '@phosphor-icons/react';
import { useAuth } from '../context/AuthContext';
import { stripeLinkFor, PLAN_PRICES } from '../utils/plan';

const FREE_FEATURES = ['Basic expense tracking', '50 transactions/month', '1 savings goal', 'Basic monthly report', 'Smart insights preview'];
const PRO_FEATURES = ['Everything in Free', 'Unlimited transactions', '10 savings goals + auto-save', 'Budgets & Zero-Based Budget', 'SIP · RD · FD tracker', 'Loan & EMI tracker', 'Credit card manager', 'Lend & Borrow log', 'Tax deductions (80C/80D) & ITR summary', 'Tax calendar', 'Unlimited savings jars', 'Full AI health score breakdown', 'Weekly digest', 'Daily spend limit', 'Subscription detector', 'PDF + CSV export'];
const ELITE_FEATURES = ['Everything in Pro', 'Investment portfolio tracker', 'Real estate tracker', 'Net worth dashboard', 'Debt payoff calculator (Avalanche vs Snowball)', 'Form 26AS PDF upload & parsing', 'AI chat assistant (unlimited)', 'Priority support', 'Early access to new features'];

const FAQ = [
  { q: 'Can I cancel anytime?', a: 'Yes! Cancel your subscription at any time directly from Stripe. No questions asked.' },
  { q: 'Is my data safe?', a: 'Absolutely. All data is encrypted and we never share your information with third parties.' },
  { q: 'Do you offer refunds?', a: 'We offer a full refund within the first 7 days of any paid plan.' },
  { q: 'Can I switch plans?', a: 'Yes, you can upgrade or downgrade at any time. Changes take effect immediately.' },
  { q: 'How does payment work?', a: 'Payments are processed securely via Stripe. Your plan unlocks automatically after a successful payment.' },
];

export const PricingPage = () => {
  const nav = useNavigate();
  const { user } = useAuth();
  const [openFaq, setOpenFaq] = useState(null);
  const currentPlan = user?.plan || 'free';

  const openStripe = (plan) => {
    const url = stripeLinkFor(plan, user?.email);
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  const tiers = [
    { id: 'free', name: 'Free', price: '$0', period: '/forever', features: FREE_FEATURES },
    { id: 'pro', name: 'Pro', price: `$${PLAN_PRICES.pro}`, period: '/month', features: PRO_FEATURES, popular: true },
    { id: 'elite', name: 'Elite', price: `$${PLAN_PRICES.elite}`, period: '/month', features: ELITE_FEATURES, dark: true, badge: 'Best Value' },
  ];

  return (
    <div className="min-h-screen bg-[var(--cream-light)] py-6 px-4" data-testid="pricing-page">
      <div className="max-w-5xl mx-auto">
        <button onClick={() => nav(-1)} className="flex items-center gap-1.5 text-sm text-[var(--muted)] hover:text-[var(--dark)] mb-8" data-testid="back-button"><ArrowLeft size={16} /> Back</button>

        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-1 text-xs text-[var(--coral)] font-semibold mb-3">{[1, 2, 3, 4, 5].map(i => <Star key={i} size={12} weight="fill" className="text-amber-400" />)} Trusted by 200k+ users</div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-[var(--dark)] tracking-tight mb-3">Simple, honest pricing</h1>
          <p className="text-base text-[var(--text-secondary)]">Start free. Upgrade when you're ready. Cancel anytime.</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 mb-12">
          {tiers.map(t => {
            const isCurrent = currentPlan === t.id;
            return (
              <div key={t.id} className={`relative rounded-[20px] p-6 flex flex-col transition-all ${t.dark ? 'bg-[var(--dark)] text-white' : 'cashly-card'} ${t.popular ? 'ring-2 ring-[var(--coral)]' : ''}`} data-testid={`tier-${t.id}`}>
                {t.popular && <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-[var(--coral)] text-white text-[10px] font-bold px-4 py-1 rounded-full">Most Popular</span>}
                {t.badge && <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-amber-500 text-white text-[10px] font-bold px-4 py-1 rounded-full flex items-center gap-1"><Crown size={10} weight="fill" /> {t.badge}</span>}
                <h3 className={`text-lg font-bold ${t.dark ? 'text-white' : 'text-[var(--dark)]'}`}>{t.name}</h3>
                <div className="flex items-baseline gap-0.5 my-3">
                  <span className={`text-3xl font-extrabold tabular-nums ${t.dark ? 'text-white' : 'text-[var(--dark)]'}`}>{t.price}</span>
                  <span className={`text-xs ${t.dark ? 'text-white/50' : 'text-[var(--muted)]'}`}>{t.period}</span>
                </div>
                <ul className="space-y-2.5 flex-1 mb-6">
                  {t.features.map(f => <li key={f} className={`flex items-start gap-2 text-xs ${t.dark ? 'text-white/80' : 'text-[var(--text-secondary)]'}`}><Check size={14} weight="bold" className="text-[var(--green)] mt-0.5 flex-shrink-0" /> <span>{f}</span></li>)}
                </ul>

                {isCurrent ? (
                  <button disabled className="w-full h-11 rounded-full text-sm font-semibold bg-gray-200 text-gray-500 cursor-not-allowed" data-testid={`cta-${t.id}`}>Current Plan</button>
                ) : t.id === 'free' ? (
                  <button disabled className="w-full h-11 rounded-full text-sm font-semibold bg-gray-100 text-gray-400 cursor-not-allowed" data-testid={`cta-${t.id}`}>Free forever</button>
                ) : (
                  <button onClick={() => openStripe(t.id)}
                    className={`w-full h-11 rounded-full text-sm font-semibold transition-all ${t.dark ? 'bg-white text-[var(--dark)] hover:bg-gray-100' : 'bg-[var(--coral)] text-white hover:bg-[var(--coral-hover)]'}`}
                    data-testid={`cta-${t.id}`}>
                    {t.id === 'elite' ? 'Go Elite' : 'Upgrade to Pro'}
                  </button>
                )}
              </div>
            );
          })}
        </div>

        <div className="max-w-2xl mx-auto mb-12">
          <h2 className="text-xl font-extrabold text-[var(--dark)] text-center mb-6">Frequently Asked Questions</h2>
          <div className="space-y-2">
            {FAQ.map((f, i) => (
              <div key={i} className="cashly-card overflow-hidden">
                <button onClick={() => setOpenFaq(openFaq === i ? null : i)} className="w-full text-left p-4 flex justify-between items-center" data-testid={`faq-${i}`}>
                  <span className="text-sm font-semibold text-[var(--dark)]">{f.q}</span>
                  <span className="text-[var(--muted)]">{openFaq === i ? '−' : '+'}</span>
                </button>
                {openFaq === i && <div className="px-4 pb-4"><p className="text-xs text-[var(--text-secondary)] leading-relaxed">{f.a}</p></div>}
              </div>
            ))}
          </div>
        </div>

        <div className="flex items-center justify-center gap-2 text-xs text-[var(--muted)] pb-8">
          <ShieldCheck size={16} className="text-[var(--green)]" /> Secured by Stripe · Cancel anytime · No hidden fees
        </div>
      </div>
    </div>
  );
};
