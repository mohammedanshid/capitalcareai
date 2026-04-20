import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Plus, Trash, Wallet, Minus, Lock } from '@phosphor-icons/react';
import { formatINR } from '../utils/inr';
import { toast } from 'sonner';
import { useAuth } from '../context/AuthContext';
import { hasAccess } from '../utils/plan';
import { UpgradeModal } from '../components/UpgradeModal';
import { FREE_LIMITS } from '../utils/plan';
import axios from 'axios';
const API = process.env.REACT_APP_BACKEND_URL;
const JAR_COLORS = ['#F4845F', '#4CAF85', '#FFB74D', '#7086FD', '#E0A96D', '#C084FC', '#F87171', '#34D399'];
const input = "w-full h-10 bg-[var(--cream-light)] border border-[var(--border)] rounded-xl px-3 text-sm text-[var(--dark)] placeholder-[var(--muted)] focus:border-[var(--coral)] outline-none";

export const JarsPage = () => {
  const nav = useNavigate();
  const { user } = useAuth();
  const [data, setData] = useState({ jars: [], total_saved: 0 });
  const [showForm, setShowForm] = useState(false);
  const [gateOpen, setGateOpen] = useState(false);
  const [f, setF] = useState({ name: '', target: '', color: JAR_COLORS[0] });
  const [txnFor, setTxnFor] = useState(null); // {jar, mode}
  const [amount, setAmount] = useState('');
  const plan = user?.plan || 'free';
  const unlimitedJars = hasAccess(plan, 'jars_unlimited');
  const atFreeLimit = !unlimitedJars && data.jars.length >= FREE_LIMITS.jars;
  useEffect(() => { load(); }, []);
  const load = async () => { try { const { data } = await axios.get(`${API}/api/jars`, { withCredentials: true }); setData(data); } catch {} };
  const tryNew = () => { if (atFreeLimit) { setGateOpen(true); return; } setShowForm(!showForm); };
  const submit = async (e) => { e.preventDefault(); if (atFreeLimit) { setGateOpen(true); return; } try { await axios.post(`${API}/api/jars`, { ...f, target: parseFloat(f.target) || 0 }, { withCredentials: true }); toast.success('Jar created'); setShowForm(false); setF({ name: '', target: '', color: JAR_COLORS[0] }); load(); } catch (err) { toast.error('Failed'); } };
  const del = async (id) => { await axios.delete(`${API}/api/jars/${id}`, { withCredentials: true }); load(); };
  const txn = async () => { if (!amount || !txnFor) return; try { await axios.post(`${API}/api/jars/${txnFor.jar.id}/${txnFor.mode}`, { amount: parseFloat(amount) }, { withCredentials: true }); toast.success(`${txnFor.mode === 'deposit' ? 'Deposited' : 'Withdrew'} ${formatINR(parseFloat(amount))}`); setTxnFor(null); setAmount(''); load(); } catch { toast.error('Failed'); } };

  return (
    <div className="min-h-screen bg-[var(--cream-light)] pb-6" data-testid="jars-page">
      <header className="sticky top-0 z-40 backdrop-blur-xl bg-[var(--cream-light)]/80 border-b border-[var(--border)]">
        <div className="max-w-5xl mx-auto px-4 h-14 flex items-center gap-3">
          <button onClick={() => nav('/dashboard')} className="p-2 rounded-xl hover:bg-white" data-testid="back-button"><ArrowLeft size={18} /></button>
          <h1 className="text-lg font-bold text-[var(--dark)]">Savings Jars</h1>
          <div className="flex-1" />
          <button onClick={tryNew} className="btn-coral text-xs py-2 px-4" data-testid="add-jar-btn">{atFreeLimit ? <><Lock size={12} /> New Jar</> : <><Plus size={14} /> New Jar</>}</button>
        </div>
      </header>
      <main className="max-w-5xl mx-auto px-4 py-4 space-y-4">
        <div className="cashly-card p-5 bg-gradient-to-br from-[var(--coral)] to-[#e06b47] text-white">
          <p className="text-xs uppercase tracking-wider text-white/80">Total Across All Jars</p>
          <p className="text-3xl font-bold mt-1" data-testid="total-saved">{formatINR(data.total_saved)}</p>
          <p className="text-xs text-white/80 mt-1">{data.jars.length} active jar{data.jars.length !== 1 ? 's' : ''}</p>
        </div>

        {showForm && (
          <form onSubmit={submit} className="cashly-card p-5 space-y-3" data-testid="jar-form">
            <div className="grid grid-cols-2 gap-3">
              <input value={f.name} onChange={e => setF({ ...f, name: e.target.value })} placeholder="Jar name (e.g. Vacation)" required className={input} data-testid="jar-name" />
              <input type="number" step="0.01" value={f.target} onChange={e => setF({ ...f, target: e.target.value })} placeholder="Target (₹) — optional" className={input} data-testid="jar-target" />
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-[var(--muted)]">Color:</span>
              {JAR_COLORS.map(c => <button type="button" key={c} onClick={() => setF({ ...f, color: c })} className={`w-6 h-6 rounded-full border-2 ${f.color === c ? 'border-[var(--dark)]' : 'border-transparent'}`} style={{ background: c }} />)}
            </div>
            <button type="submit" className="w-full btn-coral h-10 text-xs" data-testid="save-jar-btn">Create Jar</button>
          </form>
        )}

        <div className="grid md:grid-cols-2 gap-4">
          {data.jars.length === 0 ? <div className="cashly-card p-8 text-center md:col-span-2"><p className="text-sm text-[var(--muted)]">No jars yet. Create one for each savings goal (vacation, emergency, new phone, etc).</p></div> :
            data.jars.map(j => {
              const pct = j.target > 0 ? Math.min(j.progress, 100) : 0;
              return (
                <div key={j.id} className="cashly-card p-5" data-testid={`jar-${j.name}`}>
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3"><div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: `${j.color}22` }}><Wallet size={20} style={{ color: j.color }} /></div><div><p className="text-sm font-bold text-[var(--dark)]">{j.name}</p>{j.target > 0 && <p className="text-[11px] text-[var(--muted)]">Target: {formatINR(j.target)}</p>}</div></div>
                    <button onClick={() => del(j.id)} className="p-1 text-[var(--muted)] hover:text-[var(--red)]"><Trash size={14} /></button>
                  </div>
                  <p className="text-2xl font-bold text-[var(--dark)]">{formatINR(j.balance)}</p>
                  {j.target > 0 && <><div className="w-full h-2 bg-[var(--cream-light)] rounded-full overflow-hidden mt-2"><div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, background: j.color }} /></div><p className="text-[10px] text-[var(--muted)] mt-1">{j.progress}% of target</p></>}
                  <div className="flex gap-2 mt-3">
                    <button onClick={() => setTxnFor({ jar: j, mode: 'deposit' })} className="flex-1 h-9 rounded-xl text-xs font-semibold bg-[var(--dark)] text-white flex items-center justify-center gap-1" data-testid={`deposit-${j.name}`}><Plus size={12} /> Deposit</button>
                    <button onClick={() => setTxnFor({ jar: j, mode: 'withdraw' })} className="flex-1 h-9 rounded-xl text-xs font-semibold bg-[var(--cream-light)] text-[var(--dark)] border border-[var(--border)] flex items-center justify-center gap-1" data-testid={`withdraw-${j.name}`}><Minus size={12} /> Withdraw</button>
                  </div>
                </div>
              );
            })}
        </div>
      </main>

      {txnFor && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 px-4" onClick={() => setTxnFor(null)}>
          <div className="cashly-card p-5 max-w-sm w-full" onClick={e => e.stopPropagation()} data-testid="txn-modal">
            <p className="text-base font-bold text-[var(--dark)] mb-3">{txnFor.mode === 'deposit' ? 'Deposit to' : 'Withdraw from'} {txnFor.jar.name}</p>
            <input type="number" step="0.01" value={amount} onChange={e => setAmount(e.target.value)} placeholder="Amount (₹)" autoFocus className={`${input} h-12 text-lg`} data-testid="txn-amount" />
            <div className="flex gap-2 mt-3">
              <button onClick={() => { setTxnFor(null); setAmount(''); }} className="flex-1 h-10 rounded-xl text-xs font-semibold bg-[var(--cream-light)] text-[var(--dark)]">Cancel</button>
              <button onClick={txn} className="flex-1 h-10 rounded-xl text-xs font-semibold bg-[var(--coral)] text-white" data-testid="confirm-txn">Confirm</button>
            </div>
          </div>
        </div>
      )}
      <UpgradeModal open={gateOpen} onClose={() => setGateOpen(false)} feature="jars_unlimited" requiredPlan="pro" />
    </div>
  );
};
