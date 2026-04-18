import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Plus, Trash } from '@phosphor-icons/react';
import { formatINR } from '../utils/inr';
import { toast } from 'sonner';
import axios from 'axios';
const API = process.env.REACT_APP_BACKEND_URL;

export const GoalsPage = () => {
  const nav = useNavigate();
  const [goals, setGoals] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name:'', target:'', saved:'0', deadline:'' });
  const [planner, setPlanner] = useState({ monthly:'', goal: null });

  useEffect(() => { fetch_(); }, []);
  const fetch_ = async () => { try { const { data } = await axios.get(`${API}/api/individual/goals`, { withCredentials: true }); setGoals(data); } catch {} };
  const submit = async (e) => { e.preventDefault(); try { await axios.post(`${API}/api/individual/goals`, { ...form, target:parseFloat(form.target), saved:parseFloat(form.saved||'0') }, { withCredentials: true }); toast.success('Goal created!'); setShowForm(false); setForm({ name:'',target:'',saved:'0',deadline:'' }); fetch_(); } catch { toast.error('Failed'); } };
  const del = async (id) => { try { await axios.delete(`${API}/api/individual/goals/${id}`, { withCredentials: true }); toast.success('Deleted'); fetch_(); } catch {} };
  const addSavings = async (g, amt) => { try { await axios.put(`${API}/api/individual/goals/${g.id}`, { ...g, saved: g.saved + amt }, { withCredentials: true }); toast.success(`Added ${formatINR(amt)}`); fetch_(); } catch {} };
  const plannerResult = () => { if (!planner.goal||!planner.monthly) return null; const rem=planner.goal.target-planner.goal.saved; const m=Math.ceil(rem/parseFloat(planner.monthly)); const d=new Date(); d.setMonth(d.getMonth()+m); return { months:m, date:d.toLocaleDateString('en-IN',{month:'long',year:'numeric'}) }; };

  const inputClass = "w-full h-10 bg-[var(--cream-light)] border border-[var(--border)] rounded-xl px-3 text-sm text-[var(--dark)] placeholder-[var(--muted)] focus:border-[var(--coral)] outline-none transition-all";

  return (
    <div className="min-h-screen bg-[var(--cream-light)] pb-6" data-testid="goals-page">
      <header className="sticky top-0 z-40 backdrop-blur-xl bg-[var(--cream-light)]/80 border-b border-[var(--border)]">
        <div className="max-w-5xl mx-auto px-4 h-14 flex items-center gap-3">
          <button onClick={()=>nav('/dashboard')} className="p-2 rounded-xl hover:bg-white transition-all" data-testid="back-button"><ArrowLeft size={18}/></button>
          <h1 className="text-lg font-bold text-[var(--dark)]">Savings Goals</h1>
          <div className="flex-1"/>
          <button onClick={()=>setShowForm(!showForm)} className="btn-coral text-xs py-2 px-4" data-testid="add-goal-button"><Plus size={14}/> New Goal</button>
        </div>
      </header>
      <main className="max-w-5xl mx-auto px-4 py-4 space-y-4">
        {showForm && (
          <form onSubmit={submit} className="cashly-card p-5 space-y-3" data-testid="goal-form">
            <input type="text" value={form.name} onChange={e=>setForm(f=>({...f,name:e.target.value}))} placeholder="Goal name (e.g., Emergency Fund)" required className={inputClass} data-testid="goal-name-input"/>
            <div className="grid grid-cols-3 gap-2">
              <input type="number" value={form.target} onChange={e=>setForm(f=>({...f,target:e.target.value}))} placeholder="Target (₹)" required className={inputClass} data-testid="goal-target-input"/>
              <input type="number" value={form.saved} onChange={e=>setForm(f=>({...f,saved:e.target.value}))} placeholder="Already saved" className={inputClass} data-testid="goal-saved-input"/>
              <input type="date" value={form.deadline} onChange={e=>setForm(f=>({...f,deadline:e.target.value}))} className={inputClass} data-testid="goal-deadline-input"/>
            </div>
            <button type="submit" className="w-full btn-coral h-10 text-xs" data-testid="save-goal-button">Create Goal</button>
          </form>
        )}
        {goals.length===0 ? <div className="cashly-card p-8 text-center"><p className="text-sm text-[var(--muted)]">No goals yet. Create your first savings goal!</p></div> :
          goals.map(g=>{
            const pct = g.target>0?Math.min((g.saved/g.target)*100,100):0;
            return (
              <div key={g.id} className="cashly-card p-5" data-testid={`goal-${g.id}`}>
                <div className="flex items-start justify-between mb-3">
                  <div><p className="text-base font-bold text-[var(--dark)]">{g.name}</p>{g.deadline&&<p className="text-[10px] text-[var(--muted)]">Deadline: {g.deadline}</p>}</div>
                  <button onClick={()=>del(g.id)} className="p-1 text-[var(--muted)] hover:text-[var(--red)]"><Trash size={14}/></button>
                </div>
                <div className="flex justify-between text-xs mb-2"><span className="text-[var(--text-secondary)]">{formatINR(g.saved)} saved</span><span className="font-bold text-[var(--dark)]">{formatINR(g.target)} target</span></div>
                <div className="w-full h-3 bg-[var(--cream-light)] rounded-full overflow-hidden mb-3"><div className="h-full rounded-full bg-[var(--coral)] transition-all" style={{width:`${pct}%`}}/></div>
                <div className="flex gap-2 mb-3">
                  {[1000,5000,10000].map(a=><button key={a} onClick={()=>addSavings(g,a)} className="flex-1 h-9 rounded-full border border-[var(--border)] text-xs font-semibold text-[var(--dark)] hover:border-[var(--coral)] hover:text-[var(--coral)] transition-all" data-testid={`add-${a}-to-${g.id}`}>+{formatINR(a)}</button>)}
                </div>
                <div className="pt-3 border-t border-[var(--border)]">
                  <p className="text-[10px] font-bold text-[var(--muted)] mb-1.5">What-if planner</p>
                  <div className="flex gap-2 items-center">
                    <input type="number" placeholder="Monthly savings (₹)" value={planner.goal?.id===g.id?planner.monthly:''} onChange={e=>setPlanner({monthly:e.target.value,goal:g})} className="flex-1 h-9 bg-[var(--cream-light)] border border-[var(--border)] rounded-full px-3 text-xs text-[var(--dark)] focus:border-[var(--coral)] outline-none" data-testid={`planner-input-${g.id}`}/>
                    {planner.goal?.id===g.id && plannerResult() && <p className="text-[10px] text-[var(--coral)] font-bold whitespace-nowrap">~{plannerResult().months}mo ({plannerResult().date})</p>}
                  </div>
                </div>
              </div>
            );
          })
        }
      </main>
    </div>
  );
};
