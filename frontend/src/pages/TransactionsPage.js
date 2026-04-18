import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Plus, Trash, MagnifyingGlass } from '@phosphor-icons/react';
import { formatINR } from '../utils/inr';
import { toast } from 'sonner';
import axios from 'axios';
const API = process.env.REACT_APP_BACKEND_URL;

const CATS_INC = ['Salary','Freelance','Investment','Gift','Other'];
const CATS_EXP = ['Groceries','Dining','Rent','EMI','Subscriptions','Transport','Shopping','Entertainment','Healthcare','Other'];

export const TransactionsPage = () => {
  const nav = useNavigate();
  const [txns, setTxns] = useState([]);
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ type:'expense', amount:'', category:'Groceries', description:'', date: new Date().toISOString().split('T')[0] });
  const [loading, setLoading] = useState(false);
  const [smsText, setSmsText] = useState('');

  useEffect(() => { fetch_(); }, []);
  const fetch_ = async () => { try { const { data } = await axios.get(`${API}/api/individual/transactions`, { withCredentials: true }); setTxns(data); } catch {} };
  const submit = async (e) => {
    e.preventDefault(); if (!form.amount) return; setLoading(true);
    try { await axios.post(`${API}/api/individual/transactions`, { ...form, amount: parseFloat(form.amount) }, { withCredentials: true }); toast.success('Added!'); setShowForm(false); setForm({ type:'expense', amount:'', category:'Groceries', description:'', date: new Date().toISOString().split('T')[0] }); fetch_(); }
    catch (err) { toast.error(err.response?.data?.detail || 'Failed'); } finally { setLoading(false); }
  };
  const del = async (id) => { if (!window.confirm('Delete?')) return; try { await axios.delete(`${API}/api/individual/transactions/${id}`, { withCredentials: true }); toast.success('Deleted'); fetch_(); } catch { toast.error('Failed'); } };
  const parseSMS = async () => {
    if (!smsText.trim()) return;
    try { const { data } = await axios.post(`${API}/api/sms/parse`, { text: smsText }, { withCredentials: true }); if (data.parsed) { setForm(f=>({...f,amount:String(data.amount||''),type:data.type==='credit'?'income':'expense',description:data.merchant||''})); setShowForm(true); toast.success('SMS parsed!'); } else toast.error('Could not parse'); } catch { toast.error('Failed'); }
  };
  const filtered = txns.filter(t => !search || t.category.toLowerCase().includes(search.toLowerCase()) || (t.description||'').toLowerCase().includes(search.toLowerCase()));
  const cats = form.type === 'income' ? CATS_INC : CATS_EXP;
  const inputClass = "w-full h-10 bg-[var(--cream-light)] border border-[var(--border)] rounded-xl px-3 text-sm text-[var(--dark)] placeholder-[var(--muted)] focus:border-[var(--coral)] outline-none transition-all";

  return (
    <div className="min-h-screen bg-[var(--cream-light)] pb-6" data-testid="transactions-page">
      <header className="sticky top-0 z-40 backdrop-blur-xl bg-[var(--cream-light)]/80 border-b border-[var(--border)]">
        <div className="max-w-5xl mx-auto px-4 h-14 flex items-center gap-3">
          <button onClick={()=>nav('/dashboard')} className="p-2 rounded-xl hover:bg-white transition-all" data-testid="back-button"><ArrowLeft size={18}/></button>
          <h1 className="text-lg font-bold text-[var(--dark)]">Transactions</h1>
          <div className="flex-1"/>
          <button onClick={()=>setShowForm(!showForm)} className="btn-coral text-xs py-2 px-4" data-testid="add-txn-button"><Plus size={14} weight="bold"/> Add</button>
        </div>
      </header>
      <main className="max-w-5xl mx-auto px-4 py-4 space-y-4">
        {/* SMS Parser */}
        <div className="cashly-card p-4" data-testid="sms-parser">
          <p className="text-xs font-bold text-[var(--dark)] mb-2">Paste Bank SMS</p>
          <div className="flex gap-2">
            <textarea value={smsText} onChange={e=>setSmsText(e.target.value)} className="flex-1 h-14 bg-[var(--cream-light)] border border-[var(--border)] rounded-xl px-3 py-2 text-xs text-[var(--dark)] placeholder-[var(--muted)] resize-none focus:border-[var(--coral)] outline-none" placeholder="Paste your bank SMS here..." data-testid="sms-input"/>
            <button onClick={parseSMS} className="btn-coral text-xs px-4 h-14" data-testid="parse-sms-button">Parse</button>
          </div>
        </div>
        {/* Search */}
        <div className="relative"><MagnifyingGlass size={16} className="absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--muted)]"/><input value={search} onChange={e=>setSearch(e.target.value)} className="w-full h-10 bg-white border border-[var(--border)] rounded-full pl-10 pr-4 text-sm text-[var(--dark)] placeholder-[var(--muted)] focus:border-[var(--coral)] outline-none" placeholder="Search transactions..." data-testid="search-input"/></div>
        {/* Form */}
        {showForm && (
          <form onSubmit={submit} className="cashly-card p-5 space-y-3" data-testid="txn-form">
            <div className="flex gap-2 p-1 bg-[var(--cream-light)] rounded-full">
              {['income','expense'].map(t=><button key={t} type="button" onClick={()=>setForm(f=>({...f,type:t,category:t==='income'?'Salary':'Groceries'}))} className={`flex-1 py-2.5 rounded-full text-xs font-semibold transition-all ${form.type===t?'bg-white text-[var(--dark)] shadow-sm':'text-[var(--muted)]'}`} data-testid={`type-${t}`}>{t.charAt(0).toUpperCase()+t.slice(1)}</button>)}
            </div>
            <div className="grid grid-cols-2 gap-3">
              <input type="number" step="0.01" value={form.amount} onChange={e=>setForm(f=>({...f,amount:e.target.value}))} placeholder="Amount (₹)" required className={inputClass} data-testid="amount-input"/>
              <select value={form.category} onChange={e=>setForm(f=>({...f,category:e.target.value}))} className={inputClass} data-testid="category-select">{cats.map(c=><option key={c} value={c}>{c}</option>)}</select>
              <input type="date" value={form.date} onChange={e=>setForm(f=>({...f,date:e.target.value}))} className={inputClass} data-testid="date-input"/>
              <input type="text" value={form.description} onChange={e=>setForm(f=>({...f,description:e.target.value}))} placeholder="Note" className={inputClass} data-testid="description-input"/>
            </div>
            <button type="submit" disabled={loading} className="w-full btn-coral h-10 text-xs disabled:opacity-50" data-testid="save-txn-button">{loading?'Saving...':'Save Transaction'}</button>
          </form>
        )}
        {/* List */}
        <div className="space-y-2">
          {filtered.length===0 ? <p className="text-center text-xs text-[var(--muted)] py-8">No transactions found</p> :
          filtered.map(t=>(
            <div key={t.id} className="cashly-card flex items-center gap-3 p-4" data-testid={`txn-${t.id}`}>
              <div className={`w-2.5 h-2.5 rounded-full ${t.type==='income'?'bg-[var(--green)]':'bg-[var(--coral)]'}`}/>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-[var(--dark)] truncate">{t.category}{t.description?` — ${t.description}`:''}</p>
                <p className="text-[10px] text-[var(--muted)]">{t.date}</p>
              </div>
              <p className={`text-sm font-bold tabular-nums ${t.type==='income'?'text-[var(--green)]':'text-[var(--coral)]'}`}>{t.type==='income'?'+':'-'}{formatINR(t.amount)}</p>
              <button onClick={()=>del(t.id)} className="p-1.5 rounded-lg text-[var(--muted)] hover:text-[var(--red)] hover:bg-[var(--red-light)] transition-all" data-testid={`del-txn-${t.id}`}><Trash size={14}/></button>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
};
