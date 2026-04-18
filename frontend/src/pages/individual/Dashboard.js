import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import { useNavigate } from 'react-router-dom';
import { House, Receipt, Target, ChartLine, UserCircle, Moon, Sun, SignOut, Sparkle, Robot, DownloadSimple } from '@phosphor-icons/react';
import { PieChart, Pie, Cell, ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, AreaChart, Area } from 'recharts';
import { formatINR } from '../../utils/inr';
import { AlertsPanel } from '../../components/AlertsPanel';
import { ForecastWidget } from '../../components/ForecastWidget';
import { AIChatDrawer } from '../../components/AIChatDrawer';
import axios from 'axios';
const API = process.env.REACT_APP_BACKEND_URL;

const PIE_COLORS = ['#1D9E75','#34D399','#6EE7B7','#A7F3D0','#D1FAE5'];

export const IndividualDashboard = () => {
  const { user, logout, setPersona } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const nav = useNavigate();
  const [d, setD] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('home');
  const [chatOpen, setChatOpen] = useState(false);

  useEffect(() => { fetch_(); }, []);
  const fetch_ = async () => { try { const { data } = await axios.get(`${API}/api/individual/dashboard`, { withCredentials: true }); setD(data); } catch {} finally { setLoading(false); } };

  const kpis = d ? [
    { label: 'Income', value: d.income, spark: d.sparkline_income, color: '#1D9E75' },
    { label: 'Expenses', value: d.expenses, spark: d.sparkline_expenses, color: '#EF4444' },
    { label: 'Savings Rate', value: d.savings_rate, spark: [], color: '#3B82F6', suffix: '%' },
    { label: 'Net Worth', value: d.net_worth, spark: [], color: '#8B5CF6' },
  ] : [];

  const MiniSpark = ({ data: sd, color }) => {
    if (!sd || sd.length < 2) return null;
    return <ResponsiveContainer width="100%" height={32}><AreaChart data={sd.map((v,i)=>({v,i}))} margin={{top:2,right:0,left:0,bottom:0}}><defs><linearGradient id={`g${color}`} x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={color} stopOpacity={0.3}/><stop offset="100%" stopColor={color} stopOpacity={0}/></linearGradient></defs><Area type="monotone" dataKey="v" stroke={color} strokeWidth={1.5} fill={`url(#g${color})`} dot={false} isAnimationActive={false}/></AreaChart></ResponsiveContainer>;
  };

  return (
    <div className="min-h-screen bg-[var(--p-bg)] pb-20" data-persona="individual" data-testid="individual-dashboard">
      {/* Header */}
      <header className="sticky top-0 z-40 backdrop-blur-xl bg-[var(--nav-bg)] border-b border-[var(--p-border)]">
        <div className="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
          <h1 className="text-lg font-bold text-[var(--p-text)] font-['Outfit']">Capital Care <span className="text-[#1D9E75]">AI</span></h1>
          <div className="flex items-center gap-1.5">
            <button onClick={()=>setChatOpen(true)} className="p-2 rounded-lg text-[var(--p-text-muted)] hover:bg-[var(--p-border-subtle)] hover:text-[#1D9E75]" data-testid="open-chat" title="AI Assistant"><Robot size={16}/></button>
            <div className="relative group"><button className="p-2 rounded-lg text-[var(--p-text-muted)] hover:bg-[var(--p-border-subtle)]" data-testid="export-button" title="Export"><DownloadSimple size={16}/></button><div className="absolute right-0 top-full mt-1 w-32 bg-[var(--p-surface)] border border-[var(--p-border)] rounded-xl shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50 overflow-hidden"><button onClick={async()=>{const r=await axios.get(`${API}/api/export/individual/csv`,{withCredentials:true,responseType:'blob'});const u=window.URL.createObjectURL(new Blob([r.data]));const l=document.createElement('a');l.href=u;l.download='transactions.csv';l.click();}} className="w-full text-left px-3 py-2 text-xs text-[var(--p-text-secondary)] hover:bg-[var(--p-border-subtle)]" data-testid="export-csv">Export CSV</button><button onClick={async()=>{const r=await axios.get(`${API}/api/export/individual/pdf`,{withCredentials:true,responseType:'blob'});const u=window.URL.createObjectURL(new Blob([r.data]));const l=document.createElement('a');l.href=u;l.download='report.pdf';l.click();}} className="w-full text-left px-3 py-2 text-xs text-[var(--p-text-secondary)] hover:bg-[var(--p-border-subtle)]" data-testid="export-pdf">Export PDF</button></div></div>
            <button onClick={toggleTheme} className="p-2 rounded-lg text-[var(--p-text-muted)] hover:bg-[var(--p-border-subtle)]" data-testid="theme-toggle">{theme==='dark'?<Sun size={16}/>:<Moon size={16}/>}</button>
            <button onClick={async()=>{await setPersona(null);nav('/persona?switch=1');}} className="p-2 rounded-lg text-[var(--p-text-muted)] hover:bg-[var(--p-border-subtle)]" data-testid="switch-persona" title="Switch mode"><UserCircle size={16}/></button>
            <button onClick={()=>{logout();nav('/login');}} className="p-2 rounded-lg text-[var(--p-text-muted)] hover:bg-[var(--p-border-subtle)]" data-testid="logout-button"><SignOut size={16}/></button>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-5 space-y-5">
        {loading ? <div className="flex justify-center py-20"><div className="h-10 w-10 animate-spin rounded-full border-[3px] border-[#1D9E75] border-r-transparent"/></div> : d ? (
          <>
            <div>
              <p className="text-xs text-[var(--p-text-muted)]">Good morning,</p>
              <h2 className="text-xl font-bold text-[var(--p-text)] font-['Outfit']">{user?.name || 'User'}</h2>
            </div>

            {/* KPI Cards 2x2 */}
            <div className="grid grid-cols-2 gap-3">
              {kpis.map((k,i) => (
                <div key={k.label} className={`animate-fade-up stagger-${i+1} bg-[var(--p-surface)] border border-[var(--p-border)] p-4 transition-all hover:shadow-md`} style={{borderRadius:'var(--p-radius)'}} data-testid={`kpi-${k.label.toLowerCase().replace(/\s/g,'-')}`}>
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-[var(--p-text-muted)] mb-1">{k.label}</p>
                  <p className="text-xl sm:text-2xl font-bold tabular-nums" style={{color:k.color}}>
                    {k.suffix ? `${k.value}${k.suffix}` : formatINR(k.value)}
                  </p>
                  {k.spark.length > 0 && <div className="mt-2"><MiniSpark data={k.spark} color={k.color}/></div>}
                </div>
              ))}
            </div>

            {/* Donut: Spending by category */}
            {d.category_breakdown.length > 0 && (
              <div className="bg-[var(--p-surface)] border border-[var(--p-border)] p-4" style={{borderRadius:'var(--p-radius)'}} data-testid="donut-chart">
                <h3 className="text-sm font-semibold text-[var(--p-text)] mb-3">Spending by Category</h3>
                <div className="flex items-center gap-4">
                  <ResponsiveContainer width="50%" height={150}>
                    <PieChart><Pie data={d.category_breakdown} cx="50%" cy="50%" innerRadius={35} outerRadius={55} paddingAngle={3} dataKey="value">
                      {d.category_breakdown.map((_,i)=><Cell key={i} fill={PIE_COLORS[i%PIE_COLORS.length]}/>)}
                    </Pie></PieChart>
                  </ResponsiveContainer>
                  <div className="flex-1 space-y-1.5">
                    {d.category_breakdown.slice(0,5).map((c,i) => (
                      <div key={c.name} className="flex items-center justify-between text-xs">
                        <div className="flex items-center gap-1.5"><span className="w-2 h-2 rounded-sm" style={{background:PIE_COLORS[i%PIE_COLORS.length]}}/><span className="text-[var(--p-text-secondary)]">{c.name}</span></div>
                        <span className="font-medium text-[var(--p-text)] tabular-nums">{formatINR(c.value)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Line chart: 6 months */}
            {d.monthly_series.length > 0 && (
              <div className="bg-[var(--p-surface)] border border-[var(--p-border)] p-4" style={{borderRadius:'var(--p-radius)'}} data-testid="line-chart">
                <h3 className="text-sm font-semibold text-[var(--p-text)] mb-3">Income vs Expenses</h3>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={d.monthly_series}>
                    <CartesianGrid strokeDasharray="3 3" stroke={theme==='dark'?'#334155':'#F1F5F9'} vertical={false}/>
                    <XAxis dataKey="month" tick={{fill:theme==='dark'?'#64748B':'#94A3B8',fontSize:10}} axisLine={false} tickLine={false}/>
                    <YAxis tick={{fill:theme==='dark'?'#64748B':'#94A3B8',fontSize:10}} axisLine={false} tickLine={false}/>
                    <Tooltip contentStyle={{background:theme==='dark'?'#1E293B':'#FFF',border:`1px solid ${theme==='dark'?'#334155':'#E2E8F0'}`,borderRadius:'8px',fontSize:'11px'}} formatter={v=>[formatINR(v)]}/>
                    <Line type="monotone" dataKey="income" stroke="#1D9E75" strokeWidth={2} dot={{r:3}}/>
                    <Line type="monotone" dataKey="expenses" stroke="#EF4444" strokeWidth={2} dot={{r:3}}/>
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Goals preview */}
            {d.goals.length > 0 && (
              <div className="bg-[var(--p-surface)] border border-[var(--p-border)] p-4" style={{borderRadius:'var(--p-radius)'}} data-testid="goals-preview">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="text-sm font-semibold text-[var(--p-text)]">Savings Goals</h3>
                  <button onClick={()=>nav('/individual/goals')} className="text-xs text-[#1D9E75] font-medium">View all</button>
                </div>
                {d.goals.slice(0,2).map(g => {
                  const pct = g.target > 0 ? Math.min((g.saved/g.target)*100,100) : 0;
                  return (
                    <div key={g.id} className="mb-3 last:mb-0">
                      <div className="flex justify-between text-xs mb-1"><span className="text-[var(--p-text)]">{g.name}</span><span className="text-[var(--p-text-muted)]">{formatINR(g.saved)} of {formatINR(g.target)}</span></div>
                      <div className="w-full h-2 bg-[var(--p-border-subtle)] rounded-full overflow-hidden"><div className="h-full rounded-full bg-[#1D9E75] transition-all" style={{width:`${pct}%`}}/></div>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Alerts */}
            <AlertsPanel persona="individual" />

            {/* Forecast */}
            <ForecastWidget persona="individual" />
          </>
        ) : <p className="text-center text-[var(--p-text-muted)] py-10">No data yet. Add your first transaction!</p>}
      </main>

      {/* AI Chat Drawer */}
      <AIChatDrawer isOpen={chatOpen} onClose={() => setChatOpen(false)} persona="individual" />

      {/* Bottom Nav */}
      <nav className="fixed bottom-0 left-0 right-0 z-50 bg-[var(--nav-bg)] backdrop-blur-xl border-t border-[var(--p-border)]" data-testid="bottom-nav">
        <div className="flex items-center justify-around h-14 max-w-4xl mx-auto">
          {[{icon:House,label:'Home',path:'/individual'},{icon:Receipt,label:'Transactions',path:'/individual/transactions'},{icon:Target,label:'Goals',path:'/individual/goals'},{icon:ChartLine,label:'Reports',path:'/individual'},{icon:UserCircle,label:'Profile',path:'/persona'}].map(i=>(
            <button key={i.label} onClick={()=>nav(i.path)} className={`flex flex-col items-center gap-0.5 w-16 py-1 ${window.location.pathname===i.path?'text-[#1D9E75]':'text-[var(--p-text-muted)]'}`} data-testid={`nav-${i.label.toLowerCase()}`}>
              <i.icon size={20} weight={window.location.pathname===i.path?'fill':'regular'}/><span className="text-[10px] font-medium">{i.label}</span>
            </button>
          ))}
        </div>
      </nav>
    </div>
  );
};
