import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { House, Receipt, Target, ChartLine, UserCircle, SignOut, Robot, DownloadSimple, Sparkle, Lock, Crown } from '@phosphor-icons/react';
import { PieChart, Pie, Cell, ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, AreaChart, Area } from 'recharts';
import { formatINR } from '../utils/inr';
import { AIChatDrawer } from '../components/AIChatDrawer';
import { UpgradeModal } from '../components/UpgradeModal';
import { hasAccess, requiredPlanFor } from '../utils/plan';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;
const PIE_COLORS = ['#F4845F','#4CAF85','#FFB74D','#90A4AE','#E0E0E0'];

export const Dashboard = () => {
  const { user, logout } = useAuth();
  const nav = useNavigate();
  const [d, setD] = useState(null);
  const [loading, setLoading] = useState(true);
  const [chatOpen, setChatOpen] = useState(false);
  const [alerts, setAlerts] = useState([]);
  const [forecast, setForecast] = useState(null);
  const [healthScore, setHealthScore] = useState(null);
  const [dailyLimit, setDailyLimit] = useState(null);
  const [digest, setDigest] = useState(null);
  const [gateFeature, setGateFeature] = useState(null);
  const plan = user?.plan || 'free';

  useEffect(() => { fetchAll(); }, []);
  const fetchAll = async () => {
    try {
      const [dash, alertsRes, forecastRes, healthRes, dailyRes, digestRes] = await Promise.all([
        axios.get(`${API}/api/individual/dashboard`, { withCredentials: true }),
        axios.get(`${API}/api/alerts/individual`, { withCredentials: true }).catch(() => ({ data: [] })),
        axios.get(`${API}/api/forecast/individual`, { withCredentials: true }).catch(() => ({ data: null })),
        axios.get(`${API}/api/health-score`, { withCredentials: true }).catch(() => ({ data: null })),
        axios.get(`${API}/api/daily-limit`, { withCredentials: true }).catch(() => ({ data: null })),
        axios.get(`${API}/api/weekly-digest`, { withCredentials: true }).catch(() => ({ data: null })),
      ]);
      setD(dash.data); setAlerts(alertsRes.data); setForecast(forecastRes.data);
      setHealthScore(healthRes.data); setDailyLimit(dailyRes.data); setDigest(digestRes.data);
    } catch {} finally { setLoading(false); }
  };

  const handleExport = async (fmt) => {
    try {
      const r = await axios.get(`${API}/api/export/individual/${fmt}`, { withCredentials: true, responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([r.data]));
      const a = document.createElement('a'); a.href = url; a.download = `report.${fmt}`; a.click();
    } catch {}
  };

  const MiniSpark = ({ data: sd, color }) => {
    if (!sd || sd.length < 2) return null;
    return <ResponsiveContainer width="100%" height={32}><AreaChart data={sd.map((v,i)=>({v,i}))} margin={{top:2,right:0,left:0,bottom:0}}><defs><linearGradient id={`gs${color.replace('#','')}`} x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={color} stopOpacity={0.3}/><stop offset="100%" stopColor={color} stopOpacity={0}/></linearGradient></defs><Area type="monotone" dataKey="v" stroke={color} strokeWidth={1.5} fill={`url(#gs${color.replace('#','')})`} dot={false} isAnimationActive={false}/></AreaChart></ResponsiveContainer>;
  };

  const kpis = d ? [
    { label: 'Total Balance', value: d.net_worth, spark: d.sparkline_income, color: 'var(--dark)' },
    { label: 'Monthly Income', value: d.income, spark: d.sparkline_income, color: 'var(--green)' },
    { label: 'Monthly Expenses', value: d.expenses, spark: d.sparkline_expenses, color: 'var(--coral)' },
    { label: 'Savings Growth', value: d.net_worth, spark: [], color: 'var(--green)', suffix: d.savings_rate > 0 ? ` (${d.savings_rate}%)` : '' },
  ] : [];

  return (
    <div className="min-h-screen bg-[var(--cream-light)] pb-20" data-testid="dashboard-page">
      {/* Header */}
      <header className="sticky top-0 z-40 backdrop-blur-xl bg-[var(--cream-light)]/80 border-b border-[var(--border)]">
        <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-full bg-[var(--dark)] flex items-center justify-center"><span className="text-white text-[9px] font-bold">CC</span></div>
            <span className="text-base font-bold text-[var(--dark)]">Capital Care AI</span>
          </div>
          <div className="flex items-center gap-1.5">
            {/* Plan Badge */}
            <button onClick={() => plan === 'free' ? nav('/pricing') : null} className={`hidden sm:flex items-center gap-1 h-7 px-3 rounded-full text-[10px] font-bold uppercase tracking-wider ${plan === 'elite' ? 'text-white' : plan === 'pro' ? 'bg-[var(--coral)] text-white' : 'bg-[var(--cream-light)] text-[var(--muted)] border border-[var(--border)] hover:bg-white'}`} style={plan === 'elite' ? { background: 'linear-gradient(135deg,#FFD700,#FFA500)' } : {}} data-testid="plan-badge">
              {plan === 'elite' && <Crown size={10} weight="fill" />} {plan}
            </button>
            <button onClick={()=>{ if (!hasAccess(plan, 'ai_chat')) { setGateFeature('ai_chat'); return; } setChatOpen(true); }} className="p-2 rounded-xl text-[var(--muted)] hover:text-[var(--coral)] hover:bg-white transition-all relative" data-testid="open-chat" title="AI Assistant">
              <Robot size={18}/>
              {!hasAccess(plan, 'ai_chat') && <span className="absolute top-1 right-1 w-3 h-3 rounded-full flex items-center justify-center" style={{ background: 'linear-gradient(135deg,#FFD700,#FFA500)' }}><Lock size={7} weight="fill" className="text-white" /></span>}
            </button>
            <div className="relative group"><button onClick={() => { if (!hasAccess(plan, 'export_pdf_csv')) setGateFeature('export_pdf_csv'); }} className="p-2 rounded-xl text-[var(--muted)] hover:text-[var(--dark)] hover:bg-white transition-all relative" data-testid="export-button"><DownloadSimple size={18}/>{!hasAccess(plan, 'export_pdf_csv') && <span className="absolute top-1 right-1 w-3 h-3 rounded-full flex items-center justify-center bg-[var(--muted)]"><Lock size={7} weight="fill" className="text-white" /></span>}</button>{hasAccess(plan, 'export_pdf_csv') && <div className="absolute right-0 top-full mt-1 w-36 bg-white rounded-2xl shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50 overflow-hidden border border-[var(--border)]"><button onClick={()=>handleExport('csv')} className="w-full text-left px-4 py-2.5 text-xs text-[var(--text-secondary)] hover:bg-[var(--cream-light)]" data-testid="export-csv">Export CSV</button><button onClick={()=>handleExport('pdf')} className="w-full text-left px-4 py-2.5 text-xs text-[var(--text-secondary)] hover:bg-[var(--cream-light)]" data-testid="export-pdf">Export PDF</button></div>}</div>
            <button onClick={()=>{logout();nav('/login');}} className="p-2 rounded-xl text-[var(--muted)] hover:text-[var(--dark)] hover:bg-white transition-all" data-testid="logout-button"><SignOut size={18}/></button>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-5 space-y-5">
        {loading ? <div className="flex justify-center py-20"><div className="h-10 w-10 animate-spin rounded-full border-[3px] border-[var(--coral)] border-r-transparent"/></div> : d ? (
          <>
            <div><p className="text-xs text-[var(--muted)]">Good morning,</p><h2 className="text-xl font-extrabold text-[var(--dark)]">{user?.name || 'User'}</h2></div>

            {/* KPI Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {kpis.map((k,i)=>(
                <div key={k.label} className={`cashly-card animate-fade-up stagger-${i+1} p-4`} data-testid={`kpi-${k.label.toLowerCase().replace(/\s/g,'-')}`}>
                  <p className="text-[10px] text-[var(--muted)] font-medium mb-1">{k.label}</p>
                  <p className="text-lg sm:text-xl font-bold tabular-nums" style={{color:k.color}}>{k.suffix ? `${formatINR(k.value)}${k.suffix}` : formatINR(k.value)}</p>
                  {k.spark.length > 0 && <div className="mt-2"><MiniSpark data={k.spark} color={k.color === 'var(--dark)' ? '#1A1A1A' : k.color === 'var(--green)' ? '#4CAF85' : '#F4845F'}/></div>}
                </div>
              ))}
            </div>

            {/* Charts row */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
              {/* Income vs Expenses */}
              {d.monthly_series.length > 0 && (
                <div className="lg:col-span-2 cashly-card p-5" data-testid="line-chart">
                  <h3 className="text-sm font-bold text-[var(--dark)] mb-4">Income vs Expenses</h3>
                  <ResponsiveContainer width="100%" height={220}>
                    <LineChart data={d.monthly_series}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#F0F0EE" vertical={false}/>
                      <XAxis dataKey="month" tick={{fill:'#999',fontSize:10}} axisLine={false} tickLine={false}/>
                      <YAxis tick={{fill:'#999',fontSize:10}} axisLine={false} tickLine={false}/>
                      <Tooltip contentStyle={{background:'#FFF',border:'1px solid #EEE',borderRadius:'12px',fontSize:'11px',boxShadow:'0 4px 12px rgba(0,0,0,0.08)'}} formatter={v=>[formatINR(v)]}/>
                      <Line type="monotone" dataKey="income" stroke="#4CAF85" strokeWidth={2.5} dot={{r:4,fill:'#4CAF85'}}/>
                      <Line type="monotone" dataKey="expenses" stroke="#F4845F" strokeWidth={2.5} dot={{r:4,fill:'#F4845F'}}/>
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              )}
              {/* Spending Breakdown */}
              {d.category_breakdown.length > 0 && (
                <div className="cashly-card p-5" data-testid="donut-chart">
                  <h3 className="text-sm font-bold text-[var(--dark)] mb-4">Spending Breakdown</h3>
                  <ResponsiveContainer width="100%" height={140}>
                    <PieChart><Pie data={d.category_breakdown} cx="50%" cy="50%" innerRadius={35} outerRadius={55} paddingAngle={3} dataKey="value">
                      {d.category_breakdown.map((_,i)=><Cell key={i} fill={PIE_COLORS[i%PIE_COLORS.length]}/>)}
                    </Pie></PieChart>
                  </ResponsiveContainer>
                  <div className="space-y-1.5 mt-2">
                    {d.category_breakdown.slice(0,5).map((c,i)=>(
                      <div key={c.name} className="flex items-center justify-between text-[11px]">
                        <div className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-full" style={{background:PIE_COLORS[i%PIE_COLORS.length]}}/><span className="text-[var(--text-secondary)]">{c.name}</span></div>
                        <span className="font-semibold text-[var(--dark)] tabular-nums">{formatINR(c.value)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Forecast */}
            {forecast?.forecast?.length > 0 && (
              <div className="cashly-card p-5" data-testid="forecast-widget">
                <h3 className="text-sm font-bold text-[var(--dark)] mb-3">3-Month Savings Forecast</h3>
                <div className="grid grid-cols-3 gap-3">
                  {forecast.forecast.map(f=>(
                    <div key={f.month} className="bg-[var(--cream-light)] rounded-2xl p-3 text-center">
                      <p className="text-[9px] text-[var(--muted)]">{f.month}</p>
                      <p className="text-sm font-bold text-[var(--green)] tabular-nums">{formatINR(f.projected_savings)}</p>
                      <p className="text-[8px] text-[var(--muted)]">est. savings</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Smart Alerts */}
            {alerts.length > 0 && (
              <div className="cashly-card p-5" data-testid="alerts-panel">
                <h3 className="text-sm font-bold text-[var(--dark)] mb-3 flex items-center gap-2"><Sparkle size={16} weight="fill" className="text-[var(--coral)]"/> Smart Insights</h3>
                <div className="space-y-2">
                  {alerts.map((a,i)=>(
                    <div key={i} className="flex items-start gap-2.5 p-3 rounded-xl bg-[var(--cream-light)]" data-testid={`alert-${a.type}`}>
                      <div className={`w-2 h-2 rounded-full mt-1.5 flex-shrink-0 ${a.severity==='warning'?'bg-[var(--coral)]':a.severity==='success'?'bg-[var(--green)]':'bg-blue-400'}`}/>
                      <p className="text-xs text-[var(--text-secondary)] leading-relaxed">{a.message}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Goals Preview */}
            {d.goals.length > 0 && (
              <div className="cashly-card p-5" data-testid="goals-preview">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-bold text-[var(--dark)]">Savings Goals</h3>
                  <button onClick={()=>nav('/goals')} className="text-xs text-[var(--coral)] font-semibold">View all</button>
                </div>
                {d.goals.slice(0,2).map(g=>{
                  const pct = g.target>0?Math.min((g.saved/g.target)*100,100):0;
                  return (
                    <div key={g.id} className="mb-3 last:mb-0">
                      <div className="flex justify-between text-xs mb-1"><span className="text-[var(--dark)] font-medium">{g.name}</span><span className="text-[var(--muted)] tabular-nums">{formatINR(g.saved)} / {formatINR(g.target)}</span></div>
                      <div className="w-full h-2.5 bg-[var(--cream-light)] rounded-full overflow-hidden"><div className="h-full rounded-full bg-[var(--coral)] transition-all" style={{width:`${pct}%`}}/></div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Health Score + Daily Limit row */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {healthScore && (
                <div className="cashly-card p-5 flex items-center gap-5" data-testid="health-score">
                  <div className="relative w-20 h-20 flex-shrink-0">
                    <svg className="w-20 h-20 -rotate-90" viewBox="0 0 80 80">
                      <circle cx="40" cy="40" r="34" fill="none" stroke="var(--border)" strokeWidth="6"/>
                      <circle cx="40" cy="40" r="34" fill="none" stroke="var(--coral)" strokeWidth="6" strokeLinecap="round"
                        strokeDasharray={`${(healthScore.score / 100) * 213.6} 213.6`} className="transition-all duration-1000"/>
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center"><span className="text-xl font-extrabold text-[var(--dark)]">{healthScore.score}</span></div>
                  </div>
                  <div>
                    <p className="text-xs font-bold text-[var(--dark)] mb-1">Financial Health</p>
                    <p className="text-[10px] text-[var(--muted)] leading-relaxed">{healthScore.tips?.[0] || 'Keep up the good work!'}</p>
                  </div>
                </div>
              )}
              {dailyLimit && dailyLimit.limit > 0 && (
                <div className="cashly-card p-5" data-testid="daily-limit">
                  <p className="text-xs font-bold text-[var(--dark)] mb-2">Daily Spend Limit</p>
                  <div className="flex items-baseline gap-2 mb-2">
                    <span className="text-xl font-extrabold tabular-nums" style={{color: dailyLimit.percentage >= 100 ? 'var(--red)' : dailyLimit.percentage >= 80 ? '#F59E0B' : 'var(--green)'}}>{formatINR(dailyLimit.remaining)}</span>
                    <span className="text-xs text-[var(--muted)]">remaining of {formatINR(dailyLimit.limit)}</span>
                  </div>
                  <div className="w-full h-2 bg-[var(--cream-light)] rounded-full overflow-hidden">
                    <div className="h-full rounded-full transition-all" style={{width:`${Math.min(dailyLimit.percentage,100)}%`, background: dailyLimit.percentage >= 100 ? 'var(--red)' : dailyLimit.percentage >= 80 ? '#F59E0B' : 'var(--green)'}}/>
                  </div>
                  <p className="text-[10px] text-[var(--muted)] mt-1">Today: {formatINR(dailyLimit.spent_today)} spent</p>
                </div>
              )}
            </div>

            {/* Weekly Digest */}
            {digest && digest.total_spent > 0 && (
              <div className="cashly-card p-5" data-testid="weekly-digest">
                <h3 className="text-sm font-bold text-[var(--dark)] mb-3">Weekly Digest</h3>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3">
                  <div className="bg-[var(--cream-light)] rounded-xl p-2.5"><p className="text-[9px] text-[var(--muted)]">Spent</p><p className="text-sm font-bold text-[var(--coral)] tabular-nums">{formatINR(digest.total_spent)}</p></div>
                  <div className="bg-[var(--cream-light)] rounded-xl p-2.5"><p className="text-[9px] text-[var(--muted)]">Saved</p><p className="text-sm font-bold text-[var(--green)] tabular-nums">{formatINR(digest.total_saved)}</p></div>
                  <div className="bg-[var(--cream-light)] rounded-xl p-2.5"><p className="text-[9px] text-[var(--muted)]">Top Category</p><p className="text-sm font-bold text-[var(--dark)]">{digest.top_categories?.[0]?.name || '-'}</p></div>
                  <div className="bg-[var(--cream-light)] rounded-xl p-2.5"><p className="text-[9px] text-[var(--muted)]">vs Last Week</p><p className="text-sm font-bold tabular-nums" style={{color:digest.vs_last_week<=0?'var(--green)':'var(--coral)'}}>{digest.vs_last_week>0?'+':''}{digest.vs_last_week}%</p></div>
                </div>
              </div>
            )}

            {/* Plan / Subscription Card */}
            <div className="cashly-card p-5 flex flex-col sm:flex-row items-start sm:items-center gap-4" data-testid="plan-card">
              <div className="flex items-center gap-3 flex-1">
                <div className="w-12 h-12 rounded-2xl flex items-center justify-center flex-shrink-0" style={{ background: plan === 'elite' ? 'linear-gradient(135deg,#FFD700,#FFA500)' : plan === 'pro' ? 'var(--coral)' : 'var(--cream-light)', border: plan === 'free' ? '1px solid var(--border)' : 'none' }}>
                  {plan === 'elite' ? <Crown size={22} weight="fill" className="text-white" /> : <Sparkle size={22} weight={plan === 'pro' ? 'fill' : 'regular'} className={plan === 'pro' ? 'text-white' : 'text-[var(--muted)]'} />}
                </div>
                <div>
                  <p className="text-[10px] text-[var(--muted)] uppercase tracking-wider">Your Plan</p>
                  <p className="text-lg font-bold text-[var(--dark)] capitalize">{plan}{plan === 'elite' && ' · Priority Support'}</p>
                  <p className="text-[11px] text-[var(--text-secondary)]">{plan === 'free' ? 'Upgrade to unlock Pro and Elite features.' : plan === 'pro' ? 'Upgrade to Elite for Investments, Net Worth and AI Chat.' : 'All features unlocked. Thank you for being Elite!'}</p>
                </div>
              </div>
              {plan !== 'elite' && (
                <button onClick={() => nav('/pricing')} className="btn-coral text-xs py-2.5 px-5 whitespace-nowrap" data-testid="upgrade-cta-card">{plan === 'free' ? 'Upgrade your plan' : 'Upgrade to Elite'}</button>
              )}
            </div>

            {/* Quick Access Grid with plan gating */}
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3" data-testid="quick-access-grid">
              {[
                {label:'Budgets',path:'/budgets',emoji:'📊',feature:'budgets'},
                {label:'Zero Budget',path:'/zero-budget',emoji:'🎯',feature:'zero_budget'},
                {label:'Loans & EMI',path:'/loans',emoji:'🏦',feature:'loans'},
                {label:'Credit Cards',path:'/credit-cards',emoji:'💳',feature:'credit_cards'},
                {label:'Debt Payoff',path:'/debt-payoff',emoji:'⚡',feature:'debt_payoff'},
                {label:'Investments',path:'/investments',emoji:'📈',feature:'investments'},
                {label:'Real Estate',path:'/real-estate',emoji:'🏠',feature:'real_estate'},
                {label:'Net Worth',path:'/net-worth',emoji:'💎',feature:'net_worth'},
                {label:'SIP · RD · FD',path:'/sip-rd',emoji:'🌱',feature:'sip_rd'},
                {label:'Savings Jars',path:'/jars',emoji:'🫙',feature:'jars_unlimited'},
                {label:'Lend & Borrow',path:'/lend-borrow',emoji:'🤝',feature:'lend_borrow'},
                {label:'Tax & 80C',path:'/tax',emoji:'🧾',feature:'tax_basic'},
              ].map(item=>{
                // Savings Jars is a special case: free tier gets limited access (1 jar)
                const unlocked = item.feature === 'jars_unlimited' ? true : hasAccess(plan, item.feature);
                const isLocked = !unlocked;
                const required = requiredPlanFor(item.feature);
                const gold = required === 'elite';
                const handle = () => { if (isLocked) { setGateFeature(item.feature); } else { nav(item.path); } };
                return (
                  <button key={item.label} onClick={handle} className={`cashly-card p-4 text-center relative transition-all border ${isLocked ? 'border-transparent opacity-70 hover:opacity-95' : 'border-transparent hover:border-[var(--coral)]'}`} data-testid={`quick-${item.label.toLowerCase().replace(/\s/g,'-').replace(/·/g,'')}`}>
                    {isLocked && (
                      <span className="absolute top-2 right-2 w-5 h-5 rounded-full flex items-center justify-center" style={{ background: gold ? 'linear-gradient(135deg,#FFD700,#FFA500)' : 'var(--muted)' }} data-testid={`lock-${item.feature}`}>
                        <Lock size={10} weight="fill" className="text-white" />
                      </span>
                    )}
                    <span className="text-2xl block mb-1">{item.emoji}</span>
                    <p className="text-xs font-semibold text-[var(--dark)]">{item.label}</p>
                  </button>
                );
              })}
            </div>
          </>
        ) : <p className="text-center text-[var(--muted)] py-10">Welcome! Add your first transaction to get started.</p>}
      </main>

      <AIChatDrawer isOpen={chatOpen} onClose={()=>setChatOpen(false)} persona="individual" />
      <UpgradeModal open={!!gateFeature} onClose={() => setGateFeature(null)} feature={gateFeature} requiredPlan={gateFeature ? requiredPlanFor(gateFeature) : 'pro'} />

      {/* Bottom Nav */}
      <nav className="fixed bottom-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-xl border-t border-[var(--border)]" data-testid="bottom-nav">
        <div className="flex items-center justify-around h-16 max-w-5xl mx-auto">
          {[{icon:House,label:'Home',path:'/dashboard'},{icon:Receipt,label:'Transactions',path:'/transactions'},{icon:Target,label:'Goals',path:'/goals'},{icon:ChartLine,label:'Reports',path:'/dashboard'},{icon:UserCircle,label:'Profile',path:'/dashboard'}].map(i=>(
            <button key={i.label} onClick={()=>nav(i.path)} className={`flex flex-col items-center gap-0.5 w-16 py-1 transition-all ${window.location.pathname===i.path?'text-[var(--coral)]':'text-[var(--muted)]'}`} data-testid={`nav-${i.label.toLowerCase()}`}>
              <i.icon size={22} weight={window.location.pathname===i.path?'fill':'regular'}/><span className="text-[10px] font-medium">{i.label}</span>
            </button>
          ))}
        </div>
      </nav>
    </div>
  );
};
