import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Check, Star } from '@phosphor-icons/react';

const tiers = [
  { id:'free', name:'Free', price:'₹0', period:'/forever', color:'var(--dark)', features:['Basic expense tracking','5 transactions/month','1 savings goal','Monthly summary'], cta:'Get Started Free' },
  { id:'pro', name:'Pro', price:'₹99', period:'/month', color:'var(--coral)', features:['Unlimited transactions','AI-powered insights','Unlimited goals','What-if planner','Bank SMS parsing','PDF & CSV export','Priority support'], cta:'Start Free Trial', popular:true },
  { id:'premium', name:'Premium', price:'₹299', period:'/month', color:'var(--dark)', features:['Everything in Pro','Cash flow forecast','Proactive smart alerts','AI chat assistant','Advanced analytics','Custom categories','Dedicated support'], cta:'Start Free Trial' },
];

export const PricingPage = () => {
  const nav = useNavigate();
  return (
    <div className="min-h-screen bg-[var(--cream-light)] py-6 px-4" data-testid="pricing-page">
      <div className="max-w-4xl mx-auto">
        <button onClick={()=>nav(-1)} className="flex items-center gap-1.5 text-sm text-[var(--muted)] hover:text-[var(--dark)] mb-8 transition-colors" data-testid="back-button"><ArrowLeft size={16}/> Back</button>
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-1 text-xs text-[var(--coral)] font-semibold mb-3">{[1,2,3,4,5].map(i=><Star key={i} size={12} weight="fill" className="text-amber-400"/>)} Trusted by 200k+ users</div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-[var(--dark)] tracking-tight mb-3">Simple, transparent pricing</h1>
          <p className="text-base text-[var(--text-secondary)]">Choose the plan that fits your financial journey</p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
          {tiers.map(t=>(
            <div key={t.id} className={`relative cashly-card p-6 flex flex-col ${t.popular?'ring-2 ring-[var(--coral)]':''}`} data-testid={`tier-${t.id}`}>
              {t.popular && <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-[var(--coral)] text-white text-[10px] font-bold px-4 py-1 rounded-full">Most Popular</span>}
              <h3 className="text-lg font-bold text-[var(--dark)]">{t.name}</h3>
              <div className="flex items-baseline gap-0.5 my-3"><span className="text-3xl font-extrabold text-[var(--dark)] tabular-nums">{t.price}</span><span className="text-xs text-[var(--muted)]">{t.period}</span></div>
              <ul className="space-y-2.5 flex-1 mb-6">
                {t.features.map(f=><li key={f} className="flex items-center gap-2 text-xs text-[var(--text-secondary)]"><Check size={14} weight="bold" className="text-[var(--green)]"/> {f}</li>)}
              </ul>
              <button className={t.popular ? 'btn-coral w-full' : 'btn-dark w-full'} data-testid={`cta-${t.id}`}>{t.cta}</button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
