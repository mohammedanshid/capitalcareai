import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Star, Play, Lightning, ChartLine, Drop, ListChecks, Clock, Lightbulb, Prohibit, Target, ArrowRight, LinkedinLogo, TwitterLogo, InstagramLogo } from '@phosphor-icons/react';

const NAV_LINKS = ['Features', 'How it Works', 'Pricing', 'Testimonials'];
const TRUST_LOGOS = ['Slack', 'Dropbox', 'Webflow', 'Spotify', 'Remessa'];

const FEATURES = [
  { icon: '💰', title: 'Spending Breakdown', desc: 'Understand your spending with category-based insights, helping you manage money smarter and track every expense easily.' },
  { icon: '📈', title: 'Income & Expense Analytics', desc: 'Gain a clear view of your finances by visualizing money flow through detailed charts, graphs, and insights.' },
  { icon: '💧', title: 'Cash Flow', desc: 'Monitor your monthly net cash flow to understand where your money goes and identify saving opportunities.' },
  { icon: '📋', title: 'Budget Planner', desc: 'Set monthly budgets per category and track your spending against targets with real-time progress bars.' },
];

const WHY_US = [
  { icon: Clock, title: 'Save Time With Automation', desc: 'Auto-categorize transactions and parse bank SMS in seconds.' },
  { icon: Lightbulb, title: 'Smarter Money Decisions', desc: 'AI-powered insights analyze patterns and suggest improvements.' },
  { icon: Prohibit, title: 'Eliminate Unwanted Spending', desc: 'Proactive alerts flag unusual spending before it becomes a habit.' },
  { icon: Target, title: 'Reach Money Goals', desc: 'Set savings goals with what-if planners and visual progress tracking.' },
];

const STEPS = [
  { num: '01', title: 'Connect Your Accounts', desc: 'Paste bank SMS or manually add your income and expense transactions.' },
  { num: '02', title: 'Track & Organise', desc: 'Auto-categorize spending, set budgets, and create savings goals.' },
  { num: '03', title: 'Analyse & Improve', desc: 'Get AI-powered insights, forecasts, and actionable recommendations.' },
];

const TESTIMONIALS = [
  { name: 'Priya Sharma', role: 'Software Engineer', text: 'Capital Care AI completely changed how I manage my money. The AI insights are incredibly accurate and the savings goals keep me motivated.' },
  { name: 'Rahul Verma', role: 'Small Business Owner', text: 'The spending breakdown is a game changer. I finally understand where every rupee goes. Highly recommend for anyone serious about finances.' },
  { name: 'Ananya Desai', role: 'Freelance Designer', text: 'Love the clean interface and the what-if planner. It helped me plan my emergency fund in just 3 months.' },
  { name: 'Vikram Patel', role: 'Marketing Manager', text: 'The proactive alerts saved me from overspending on subscriptions I forgot about. Such a thoughtful feature.' },
  { name: 'Sneha Iyer', role: 'CA Professional', text: 'Finally a finance app that understands Indian money. The INR formatting and SMS parser work flawlessly.' },
  { name: 'Arjun Nair', role: 'Product Manager', text: 'I have tried many finance apps but this one stands out. Beautiful design, powerful AI, and actually useful insights.' },
];

export const LandingPage = () => {
  const nav = useNavigate();

  return (
    <div className="min-h-screen bg-[var(--cream-light)]" data-testid="landing-page">
      {/* ═══ NAVBAR ═══ */}
      <nav className="sticky top-0 z-50 backdrop-blur-xl bg-[var(--cream-light)]/80 border-b border-[var(--border)]">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2" data-testid="logo">
            <div className="w-8 h-8 rounded-full bg-[var(--dark)] flex items-center justify-center"><span className="text-white text-xs font-bold">CC</span></div>
            <span className="text-lg font-bold text-[var(--dark)]">Capital Care AI</span>
          </div>
          <div className="hidden md:flex items-center gap-8">
            {NAV_LINKS.map(l => <a key={l} href={`#${l.toLowerCase().replace(/\s/g,'-')}`} className="text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--dark)] transition-colors">{l}</a>)}
          </div>
          <div className="flex items-center gap-3">
            <button onClick={() => nav('/login')} className="text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--dark)] hidden sm:block" data-testid="nav-login">Login</button>
            <button onClick={() => nav('/login')} className="btn-coral text-xs sm:text-sm" data-testid="nav-get-started">Get Started Free</button>
          </div>
        </div>
      </nav>

      {/* ═══ HERO ═══ */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 pt-16 sm:pt-24 pb-12 text-center" id="hero">
        <div className="animate-fade-up">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[var(--coral-light)] text-[var(--coral)] text-xs font-semibold mb-6" data-testid="hero-badge">
            <div className="flex">{[1,2,3,4,5].map(i=><Star key={i} size={12} weight="fill" className="text-amber-400"/>)}</div>
            200k+ Members Joined
          </div>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-[var(--dark)] tracking-tight leading-[1.1] mb-6 max-w-3xl mx-auto" data-testid="hero-heading">
            Effortlessly Manage and Control Your Finances
          </h1>
          <p className="text-base sm:text-lg text-[var(--text-secondary)] max-w-2xl mx-auto mb-8 leading-relaxed">
            Manage your income, track expenses, and grow savings on one powerful platform with real-time insights and smart automation features.
          </p>
          <div className="flex items-center justify-center gap-4 flex-wrap">
            <button onClick={() => nav('/login')} className="btn-coral px-8 py-3.5" data-testid="hero-cta-start">Get Started Free <ArrowRight size={16}/></button>
            <button className="btn-outline px-8 py-3.5" data-testid="hero-cta-demo"><Play size={16} weight="fill"/> View Demo</button>
          </div>
        </div>

        {/* Dashboard mockup */}
        <div className="mt-16 animate-fade-up stagger-2 cashly-card p-4 sm:p-6 max-w-4xl mx-auto" data-testid="hero-mockup">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
            {[{l:'Total Balance',v:'₹2,45,000',c:'var(--dark)'},{l:'Monthly Income',v:'₹85,000',c:'var(--green)'},{l:'Monthly Expenses',v:'₹54,000',c:'var(--coral)'},{l:'Savings Growth',v:'₹28,000',c:'var(--green)'}].map(k=>(
              <div key={k.l} className="bg-[var(--cream-light)] rounded-xl p-3 text-left">
                <p className="text-[10px] text-[var(--muted)] mb-1">{k.l}</p>
                <p className="text-lg font-bold tabular-nums" style={{color:k.c}}>{k.v}</p>
              </div>
            ))}
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="sm:col-span-2 bg-[var(--cream-light)] rounded-xl p-4 h-36 flex items-end">
              <div className="w-full flex items-end gap-1 h-20">{[40,55,35,65,50,72,60,80,45,70,55,85].map((h,i)=><div key={i} className="flex-1 rounded-t-sm transition-all" style={{height:`${h}%`,background:i%2===0?'var(--coral)':'var(--green)',opacity:0.7+i*0.02}}/>)}</div>
            </div>
            <div className="bg-[var(--cream-light)] rounded-xl p-4 flex items-center justify-center">
              <div className="w-24 h-24 rounded-full border-8 border-[var(--coral)] border-t-[var(--green)] border-r-[var(--green)]" style={{borderWidth:'10px'}}/>
            </div>
          </div>
        </div>

        {/* Trust logos */}
        <div className="flex items-center justify-center gap-8 sm:gap-12 mt-12 opacity-40 flex-wrap">
          {TRUST_LOGOS.map(l => <span key={l} className="text-sm font-semibold text-[var(--muted)] tracking-wider">{l}</span>)}
        </div>
      </section>

      {/* ═══ SMARTER WAYS ═══ */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 py-20" id="features">
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-extrabold text-[var(--dark)] tracking-tight mb-4">Smarter Ways to Manage Money</h2>
          <p className="text-base text-[var(--text-secondary)] max-w-xl mx-auto">Everything required to track spending, manage income, and gain full financial control through one simple and powerful platform.</p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          {FEATURES.map((f, i) => (
            <div key={f.title} className={`cashly-card animate-fade-up stagger-${i+1}`} data-testid={`feature-${i}`}>
              <div className="text-3xl mb-3">{f.icon}</div>
              <h3 className="text-lg font-bold text-[var(--dark)] mb-2">{f.title}</h3>
              <p className="text-sm text-[var(--text-secondary)] leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ═══ WHY CHOOSE US ═══ */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 py-20 bg-white rounded-3xl my-4 sm:my-8" style={{boxShadow:'var(--shadow-card)'}}>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-start">
          <div>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-[var(--dark)] tracking-tight leading-tight mb-6">Learn Why Thousands Trust Our Platform For Their Finances</h2>
            <button onClick={() => nav('/login')} className="btn-coral" data-testid="why-cta">Get Started <ArrowRight size={16}/></button>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {WHY_US.map((w, i) => (
              <div key={w.title} className="bg-[var(--cream-light)] rounded-2xl p-5" data-testid={`why-${i}`}>
                <div className="w-10 h-10 rounded-xl bg-white flex items-center justify-center mb-3" style={{boxShadow:'var(--shadow-card)'}}>
                  <w.icon size={20} weight="duotone" className="text-[var(--coral)]"/>
                </div>
                <h4 className="text-sm font-bold text-[var(--dark)] mb-1.5">{w.title}</h4>
                <p className="text-xs text-[var(--text-secondary)] leading-relaxed">{w.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ WORKFLOW ═══ */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 py-20" id="how-it-works">
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-extrabold text-[var(--dark)] tracking-tight mb-4">Smart Financial Workflow System</h2>
          <p className="text-base text-[var(--text-secondary)] max-w-xl mx-auto">Track your finances in a simple, streamlined process designed for clarity and control.</p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          {STEPS.map((s, i) => (
            <div key={s.num} className={`cashly-card text-center animate-fade-up stagger-${i+1}`} data-testid={`step-${s.num}`}>
              <div className="w-12 h-12 rounded-full bg-[var(--coral)] text-white font-extrabold text-lg flex items-center justify-center mx-auto mb-4">{s.num}</div>
              <h3 className="text-lg font-bold text-[var(--dark)] mb-2">{s.title}</h3>
              <p className="text-sm text-[var(--text-secondary)] leading-relaxed">{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ═══ TESTIMONIALS ═══ */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 py-20" id="testimonials">
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-extrabold text-[var(--dark)] tracking-tight mb-4">Trusted by Thousands of Users</h2>
          <p className="text-base text-[var(--text-secondary)] max-w-xl mx-auto">Real people sharing how Capital Care AI helped them take control of their finances.</p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {TESTIMONIALS.map((t, i) => (
            <div key={t.name} className={`cashly-card animate-fade-up stagger-${(i%4)+1}`} data-testid={`testimonial-${i}`}>
              <div className="flex mb-3">{[1,2,3,4,5].map(s=><Star key={s} size={14} weight="fill" className="text-amber-400"/>)}</div>
              <p className="text-sm text-[var(--text-secondary)] leading-relaxed mb-4">"{t.text}"</p>
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-full bg-gradient-to-br from-[var(--coral)] to-[var(--green)] flex items-center justify-center text-white text-xs font-bold">{t.name.split(' ').map(n=>n[0]).join('')}</div>
                <div><p className="text-sm font-semibold text-[var(--dark)]">{t.name}</p><p className="text-[10px] text-[var(--muted)]">{t.role}</p></div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ═══ BOTTOM CTA ═══ */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 py-20">
        <div className="cashly-card p-8 sm:p-12 grid grid-cols-1 lg:grid-cols-2 gap-8 items-center" style={{background:'linear-gradient(135deg, #FFF5F2 0%, #FFFFFF 100%)'}}>
          <div>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-[var(--dark)] tracking-tight leading-tight mb-4">Manage your finances smarter starting from today</h2>
            <p className="text-base text-[var(--text-secondary)] mb-6">Join thousands of users who have transformed their financial lives with intelligent tracking and AI-powered insights.</p>
            <button onClick={() => nav('/login')} className="btn-coral px-8 py-3.5" data-testid="bottom-cta">Get Started <ArrowRight size={16}/></button>
          </div>
          <div className="hidden lg:block">
            <div className="bg-white rounded-2xl p-4 shadow-lg">
              <div className="grid grid-cols-2 gap-2 mb-3">
                {[{l:'Balance',v:'₹2,45,000'},{l:'Income',v:'₹85,000'},{l:'Expenses',v:'₹54,000'},{l:'Savings',v:'₹28,000'}].map(k=>(
                  <div key={k.l} className="bg-[var(--cream-light)] rounded-lg p-2"><p className="text-[8px] text-[var(--muted)]">{k.l}</p><p className="text-xs font-bold">{k.v}</p></div>
                ))}
              </div>
              <div className="bg-[var(--cream-light)] rounded-lg h-16 flex items-end gap-0.5 p-2">{[30,50,40,65,55,70,45,80].map((h,i)=><div key={i} className="flex-1 rounded-t-sm" style={{height:`${h}%`,background:i%2?'var(--green)':'var(--coral)',opacity:0.8}}/>)}</div>
            </div>
          </div>
        </div>
      </section>

      {/* ═══ FOOTER ═══ */}
      <footer className="border-t border-[var(--border)] bg-white mt-8">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-12">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-8 mb-8">
            <div className="col-span-2 sm:col-span-1">
              <div className="flex items-center gap-2 mb-3"><div className="w-7 h-7 rounded-full bg-[var(--dark)] flex items-center justify-center"><span className="text-white text-[10px] font-bold">CC</span></div><span className="text-sm font-bold text-[var(--dark)]">Capital Care AI</span></div>
              <p className="text-xs text-[var(--muted)] leading-relaxed">Your money, your way. Smart finance management powered by AI.</p>
            </div>
            {[{t:'Product',l:['Dashboard','Analytics','Goals','Export']},{t:'Company',l:['About','Careers','Blog','Press']},{t:'Support',l:['Help Center','Contact','Privacy','Terms']}].map(g=>(
              <div key={g.t}><p className="text-xs font-bold text-[var(--dark)] mb-3">{g.t}</p>{g.l.map(l=><p key={l} className="text-xs text-[var(--muted)] mb-2 hover:text-[var(--dark)] cursor-pointer transition-colors">{l}</p>)}</div>
            ))}
          </div>
          <div className="flex items-center justify-between pt-6 border-t border-[var(--border)]">
            <p className="text-xs text-[var(--muted)]">© 2026 Capital Care AI. All rights reserved.</p>
            <div className="flex gap-3">
              {[TwitterLogo, LinkedinLogo, InstagramLogo].map((Icon, i) => <Icon key={i} size={18} className="text-[var(--muted)] hover:text-[var(--dark)] cursor-pointer transition-colors"/>)}
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};
