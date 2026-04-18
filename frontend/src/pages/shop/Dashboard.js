import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import { useNavigate } from 'react-router-dom';
import { House, CurrencyInr, BookOpen, ChartBar, Gear, Moon, Sun, SignOut, UserCircle, Plus, Minus, Robot } from '@phosphor-icons/react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { formatINR } from '../../utils/inr';
import { AlertsPanel } from '../../components/AlertsPanel';
import { ForecastWidget } from '../../components/ForecastWidget';
import { AIChatDrawer } from '../../components/AIChatDrawer';
import { toast } from 'sonner';
import axios from 'axios';
const API = process.env.REACT_APP_BACKEND_URL;

const CREDIT_CATS = ['Sales','UPI received','Cash received','Loan','Other'];
const DEBIT_CATS = ['Purchase','Salary','Rent','Utilities','Supplier','Misc'];

export const ShopDashboard = () => {
  const { user, logout, setPersona } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const nav = useNavigate();
  const [d, setD] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sheet, setSheet] = useState(null); // 'credit' | 'debit' | null
  const [form, setForm] = useState({ amount:'', category:'Sales', note:'' });
  const [submitting, setSubmitting] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);

  useEffect(() => { fetch_(); }, []);
  const fetch_ = async () => { try { const { data } = await axios.get(`${API}/api/shop/dashboard`, { withCredentials: true }); setD(data); } catch {} finally { setLoading(false); } };

  const addEntry = async (e) => {
    e.preventDefault(); if (!form.amount) return;
    setSubmitting(true);
    try {
      await axios.post(`${API}/api/shop/entry`, { amount: parseFloat(form.amount), category: form.category, note: form.note, entry_type: sheet }, { withCredentials: true });
      toast.success(`${sheet === 'credit' ? 'Credit' : 'Debit'} added!`);
      setSheet(null); setForm({ amount:'', category:'Sales', note:'' }); fetch_();
    } catch (err) { toast.error(err.response?.data?.detail || 'Failed'); }
    finally { setSubmitting(false); }
  };

  return (
    <div className="min-h-screen pb-24" data-persona="shop_owner" style={{background:'var(--p-bg)'}} data-testid="shop-dashboard">
      <header className="sticky top-0 z-40 backdrop-blur-xl bg-[var(--nav-bg)] border-b border-[var(--p-border)]">
        <div className="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
          <h1 className="text-lg font-extrabold text-[var(--p-text)] font-['Outfit']">Capital Care <span className="text-[#EF9F27]">AI</span></h1>
          <div className="flex items-center gap-1.5">
            <button onClick={()=>setChatOpen(true)} className="p-2 rounded-md text-[var(--p-text-muted)] hover:text-[#EF9F27]" data-testid="open-chat" title="AI Assistant"><Robot size={16}/></button>
            <button onClick={toggleTheme} className="p-2 rounded-md text-[var(--p-text-muted)] hover:bg-[var(--p-border-subtle)]" data-testid="theme-toggle">{theme==='dark'?<Sun size={16}/>:<Moon size={16}/>}</button>
            <button onClick={async()=>{await setPersona(null);nav('/persona?switch=1');}} className="p-2 rounded-md text-[var(--p-text-muted)]" data-testid="switch-persona"><UserCircle size={16}/></button>
            <button onClick={()=>{logout();nav('/login');}} className="p-2 rounded-md text-[var(--p-text-muted)]" data-testid="logout-button"><SignOut size={16}/></button>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-4 space-y-4">
        {loading ? <div className="flex justify-center py-20"><div className="h-10 w-10 animate-spin rounded-full border-[3px] border-[#EF9F27] border-r-transparent"/></div> : d ? (
          <>
            <div className="flex items-center justify-between">
              <div><p className="text-xs text-[var(--p-text-muted)]">Today, {new Date().toLocaleDateString('en-IN',{weekday:'long',day:'numeric',month:'short'})}</p>
              <h2 className="text-lg font-extrabold text-[var(--p-text)] font-['Outfit']">{user?.name || 'Shop'}</h2></div>
            </div>

            {/* 3 KPI cards */}
            <div className="space-y-3">
              {[{label:"Today's Revenue",value:d.today_credit,color:'#1D9E75'},{label:'Cash in Hand',value:d.closing_balance,color:'#EF9F27'},{label:'Pending Payments',value:d.pending_payments.reduce((s,p)=>s+p.amount,0),color:'#EF4444'}].map((k,i)=>(
                <div key={k.label} className={`animate-fade-up stagger-${i+1} bg-[var(--p-surface)] border-2 border-[var(--p-border)] p-4`} style={{borderRadius:'var(--p-radius)'}} data-testid={`kpi-${k.label.toLowerCase().replace(/[^a-z]/g,'-')}`}>
                  <p className="text-[10px] font-bold uppercase tracking-wider text-[var(--p-text-muted)]">{k.label}</p>
                  <p className="text-2xl font-extrabold tabular-nums mt-1" style={{color:k.color}}>{formatINR(k.value)}</p>
                </div>
              ))}
            </div>

            {/* Cash Summary Card */}
            <div className="bg-[var(--p-surface)] border-2 border-[var(--p-border)] p-4" style={{borderRadius:'var(--p-radius)'}} data-testid="cash-summary">
              <h3 className="text-xs font-bold text-[var(--p-text)] uppercase tracking-wider mb-3">Today's Cash Summary</h3>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div><p className="text-[var(--p-text-muted)]">Opening</p><p className="font-bold text-[var(--p-text)] tabular-nums">{formatINR(d.opening_balance)}</p></div>
                <div><p className="text-[var(--p-text-muted)]">Closing</p><p className="font-bold text-[#EF9F27] tabular-nums">{formatINR(d.closing_balance)}</p></div>
                <div><p className="text-[var(--p-text-muted)]">Credited</p><p className="font-bold text-[#1D9E75] tabular-nums">+{formatINR(d.today_credit)}</p></div>
                <div><p className="text-[var(--p-text-muted)]">Debited</p><p className="font-bold text-[#EF4444] tabular-nums">-{formatINR(d.today_debit)}</p></div>
              </div>
              <div className="mt-3 w-full h-2 bg-[var(--p-border-subtle)] rounded-full overflow-hidden">
                <div className="h-full bg-[#1D9E75] rounded-full" style={{width:`${d.today_credit+d.today_debit>0?(d.today_credit/(d.today_credit+d.today_debit))*100:50}%`}}/>
              </div>
              <p className="text-[10px] text-[var(--p-text-muted)] text-center mt-1">Credit vs Debit ratio</p>
            </div>

            {/* Weekly bar chart */}
            {d.weekly_series.length > 0 && (
              <div className="bg-[var(--p-surface)] border-2 border-[var(--p-border)] p-4" style={{borderRadius:'var(--p-radius)'}} data-testid="weekly-chart">
                <h3 className="text-xs font-bold text-[var(--p-text)] uppercase tracking-wider mb-3">Weekly Cash Flow</h3>
                <ResponsiveContainer width="100%" height={180}>
                  <BarChart data={d.weekly_series}>
                    <CartesianGrid strokeDasharray="3 3" stroke={theme==='dark'?'#334155':'#F1F5F9'} vertical={false}/>
                    <XAxis dataKey="date" tick={{fill:theme==='dark'?'#64748B':'#94A3B8',fontSize:9}} axisLine={false} tickLine={false}/>
                    <YAxis tick={{fill:theme==='dark'?'#64748B':'#94A3B8',fontSize:9}} axisLine={false} tickLine={false}/>
                    <Tooltip contentStyle={{background:theme==='dark'?'#29221C':'#FFF',border:'1px solid #E2E8F0',borderRadius:'6px',fontSize:'10px'}} formatter={v=>[formatINR(v)]}/>
                    <Bar dataKey="credit" fill="#1D9E75" radius={[3,3,0,0]} name="Credit"/>
                    <Bar dataKey="debit" fill="#EF4444" radius={[3,3,0,0]} name="Debit"/>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Today's feed */}
            <div className="bg-[var(--p-surface)] border-2 border-[var(--p-border)] p-4" style={{borderRadius:'var(--p-radius)'}} data-testid="today-feed">
              <h3 className="text-xs font-bold text-[var(--p-text)] uppercase tracking-wider mb-3">Today's Entries</h3>
              {d.today_entries.length === 0 ? <p className="text-xs text-[var(--p-text-muted)] text-center py-4">No entries yet. Tap + Credit or - Debit to start.</p> :
                <div className="space-y-2">{d.today_entries.map(e=>(
                  <div key={e.id} className="flex items-center gap-3 py-2 border-b border-[var(--p-border-subtle)] last:border-0">
                    <span className="text-[10px] text-[var(--p-text-muted)] w-10">{e.time}</span>
                    <div className="flex-1"><p className="text-xs font-medium text-[var(--p-text)]">{e.category}{e.note?` — ${e.note}`:''}</p></div>
                    <p className={`text-sm font-bold tabular-nums ${e.entry_type==='credit'?'text-[#1D9E75]':'text-[#EF4444]'}`}>{e.entry_type==='credit'?'+':'-'}{formatINR(e.amount)}</p>
                  </div>
                ))}</div>
              }
            </div>

            {/* Pending Payments */}
            {d.pending_payments.length > 0 && (
              <div className="bg-[var(--p-surface)] border-2 border-[#EF4444]/30 p-4" style={{borderRadius:'var(--p-radius)'}} data-testid="pending-payments">
                <h3 className="text-xs font-bold text-[#EF4444] uppercase tracking-wider mb-3">Pending Payments</h3>
                {d.pending_payments.map(p=>(
                  <div key={p.id} className="flex items-center justify-between py-2 border-b border-[var(--p-border-subtle)] last:border-0">
                    <div><p className="text-xs font-medium text-[var(--p-text)]">{p.name}</p><p className="text-[10px] text-[var(--p-text-muted)]">{p.days_overdue} days overdue</p></div>
                    <p className="text-sm font-bold text-[#EF4444] tabular-nums">{formatINR(p.amount)}</p>
                  </div>
                ))}
              </div>
            )}

            {/* Alerts */}
            <AlertsPanel persona="shop_owner" />

            {/* Forecast */}
            <ForecastWidget persona="shop_owner" />
          </>
        ) : null}
      </main>

      {/* AI Chat Drawer */}
      <AIChatDrawer isOpen={chatOpen} onClose={() => setChatOpen(false)} persona="shop_owner" />

      {/* Quick Entry Bar */}
      <div className="fixed bottom-14 left-0 right-0 z-50 bg-[var(--p-surface)] border-t-2 border-[var(--p-border)] px-4 py-2" data-testid="quick-entry-bar">
        <div className="max-w-4xl mx-auto flex gap-3">
          <button onClick={()=>{setSheet('credit');setForm(f=>({...f,category:'Sales'}));}} className="flex-1 h-12 rounded-md bg-[#1D9E75] text-white font-bold text-sm flex items-center justify-center gap-2 active:scale-[0.97] transition-all" data-testid="credit-button"><Plus size={18} weight="bold"/> Credit</button>
          <button onClick={()=>{setSheet('debit');setForm(f=>({...f,category:'Purchase'}));}} className="flex-1 h-12 rounded-md bg-[#EF4444] text-white font-bold text-sm flex items-center justify-center gap-2 active:scale-[0.97] transition-all" data-testid="debit-button"><Minus size={18} weight="bold"/> Debit</button>
        </div>
      </div>

      {/* Bottom Sheet */}
      {sheet && (
        <div className="fixed inset-0 z-50 bg-black/40" onClick={()=>setSheet(null)}>
          <div className="absolute bottom-0 left-0 right-0 bg-[var(--p-surface)] rounded-t-2xl p-5 max-h-[70vh] overflow-y-auto" onClick={e=>e.stopPropagation()} data-testid="entry-sheet">
            <div className="w-10 h-1 bg-[var(--p-border)] rounded-full mx-auto mb-4"/>
            <h3 className="text-lg font-extrabold text-[var(--p-text)] font-['Outfit'] mb-4">{sheet==='credit'?'+ Credit (Money In)':'- Debit (Money Out)'}</h3>
            <form onSubmit={addEntry} className="space-y-3">
              <input type="number" step="0.01" value={form.amount} onChange={e=>setForm(f=>({...f,amount:e.target.value}))} placeholder="Amount (₹)" required className="w-full h-12 bg-[var(--p-bg)] border-2 border-[var(--p-border)] rounded-md px-4 text-lg font-bold text-[var(--p-text)] placeholder-[var(--p-text-muted)] focus:border-[var(--p-primary)] outline-none" autoFocus data-testid="entry-amount"/>
              <select value={form.category} onChange={e=>setForm(f=>({...f,category:e.target.value}))} className="w-full h-12 bg-[var(--p-bg)] border-2 border-[var(--p-border)] rounded-md px-4 text-sm text-[var(--p-text)] focus:border-[var(--p-primary)] outline-none" data-testid="entry-category">
                {(sheet==='credit'?CREDIT_CATS:DEBIT_CATS).map(c=><option key={c} value={c}>{c}</option>)}
              </select>
              <input type="text" value={form.note} onChange={e=>setForm(f=>({...f,note:e.target.value}))} placeholder="Note (optional)" className="w-full h-12 bg-[var(--p-bg)] border-2 border-[var(--p-border)] rounded-md px-4 text-sm text-[var(--p-text)] placeholder-[var(--p-text-muted)] focus:border-[var(--p-primary)] outline-none" data-testid="entry-note"/>
              <button type="submit" disabled={submitting} className={`w-full h-12 rounded-md text-white font-bold text-sm transition-all ${sheet==='credit'?'bg-[#1D9E75]':'bg-[#EF4444]'} disabled:opacity-50`} data-testid="entry-submit">{submitting?'Adding...':'Add Entry'}</button>
            </form>
          </div>
        </div>
      )}

      {/* Bottom Nav */}
      <nav className="fixed bottom-0 left-0 right-0 z-40 bg-[var(--nav-bg)] backdrop-blur-xl border-t-2 border-[var(--p-border)]" data-testid="bottom-nav">
        <div className="flex items-center justify-around h-14 max-w-4xl mx-auto">
          {[{icon:House,label:'Home',path:'/shop'},{icon:CurrencyInr,label:'Sales',path:'/shop'},{icon:BookOpen,label:'Ledger',path:'/shop/ledger'},{icon:ChartBar,label:'Reports',path:'/shop'},{icon:Gear,label:'Settings',path:'/persona'}].map(i=>(
            <button key={i.label} onClick={()=>nav(i.path)} className={`flex flex-col items-center gap-0.5 w-16 py-1 ${window.location.pathname===i.path?'text-[#EF9F27]':'text-[var(--p-text-muted)]'}`} data-testid={`nav-${i.label.toLowerCase()}`}>
              <i.icon size={20} weight={window.location.pathname===i.path?'fill':'bold'}/><span className="text-[10px] font-bold">{i.label}</span>
            </button>
          ))}
        </div>
      </nav>
    </div>
  );
};
