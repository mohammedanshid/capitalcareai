import React, { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { useTheme } from '../../context/ThemeContext';
import { useNavigate } from 'react-router-dom';
import { House, Users, ListChecks, ChartBar, Gear, Moon, Sun, SignOut, UserCircle, Plus, MagnifyingGlass, Warning, CheckCircle, Clock, Robot } from '@phosphor-icons/react';
import { AlertsPanel } from '../../components/AlertsPanel';
import { AIChatDrawer } from '../../components/AIChatDrawer';
import { toast } from 'sonner';
import axios from 'axios';
const API = process.env.REACT_APP_BACKEND_URL;

const STATUS_MAP = { on_track: { label: 'On track', color: '#1D9E75', icon: CheckCircle }, overdue: { label: 'Overdue', color: '#EF4444', icon: Warning }, pending_docs: { label: 'Pending docs', color: '#EF9F27', icon: Clock } };

export const CADashboard = () => {
  const { user, logout, setPersona } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const nav = useNavigate();
  const [d, setD] = useState(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name:'', business_type:'', status:'on_track', next_deadline:'' });
  const [chatOpen, setChatOpen] = useState(false);

  useEffect(() => { fetch_(); }, []);
  const fetch_ = async () => { try { const { data } = await axios.get(`${API}/api/ca/dashboard`, { withCredentials: true }); setD(data); } catch {} finally { setLoading(false); } };

  const addClient = async (e) => {
    e.preventDefault();
    try { await axios.post(`${API}/api/ca/clients`, form, { withCredentials: true }); toast.success('Client added'); setShowForm(false); setForm({ name:'', business_type:'', status:'on_track', next_deadline:'' }); fetch_(); }
    catch { toast.error('Failed'); }
  };

  const delClient = async (id) => { try { await axios.delete(`${API}/api/ca/clients/${id}`, { withCredentials: true }); fetch_(); } catch {} };

  const clients = d?.clients?.filter(c => !search || c.name.toLowerCase().includes(search.toLowerCase()) || c.business_type.toLowerCase().includes(search.toLowerCase())) || [];

  return (
    <div className="min-h-screen bg-[var(--p-bg)] pb-20" data-persona="ca" data-testid="ca-dashboard">
      <header className="sticky top-0 z-40 backdrop-blur-xl bg-[var(--nav-bg)] border-b border-[var(--p-border)]">
        <div className="max-w-5xl mx-auto px-4 h-12 flex items-center justify-between">
          <h1 className="text-base font-bold text-[var(--p-text)] font-['Outfit']">Capital Care <span className="text-[#185FA5]">AI</span> <span className="text-[10px] font-normal text-[var(--p-text-muted)]">CA</span></h1>
          <div className="flex items-center gap-1">
            <button onClick={()=>setChatOpen(true)} className="p-1.5 rounded text-[var(--p-text-muted)] hover:text-[#185FA5]" data-testid="open-chat"><Robot size={14}/></button>
            <button onClick={toggleTheme} className="p-1.5 rounded text-[var(--p-text-muted)] hover:bg-[var(--p-border-subtle)]" data-testid="theme-toggle">{theme==='dark'?<Sun size={14}/>:<Moon size={14}/>}</button>
            <button onClick={async()=>{await setPersona(null);nav('/persona?switch=1');}} className="p-1.5 rounded text-[var(--p-text-muted)]" data-testid="switch-persona"><UserCircle size={14}/></button>
            <button onClick={()=>{logout();nav('/login');}} className="p-1.5 rounded text-[var(--p-text-muted)]" data-testid="logout-button"><SignOut size={14}/></button>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-4 space-y-4">
        {loading ? <div className="flex justify-center py-20"><div className="h-8 w-8 animate-spin rounded-full border-2 border-[#185FA5] border-r-transparent"/></div> : d ? (
          <>
            {/* Summary strip */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2" data-testid="ca-summary">
              {[{l:'Active Clients',v:d.active_clients,c:'#185FA5'},{l:'Reports Due',v:d.reports_due,c:'#EF4444'},{l:'Pending Tasks',v:d.pending_tasks,c:'#EF9F27'},{l:'Overdue',v:d.overdue_tasks,c:'#EF4444'}].map(k=>(
                <div key={k.l} className="bg-[var(--p-surface)] border border-[var(--p-border)] rounded-sm p-3" data-testid={`stat-${k.l.toLowerCase().replace(/\s/g,'-')}`}>
                  <p className="text-[9px] font-semibold uppercase tracking-wider text-[var(--p-text-muted)]">{k.l}</p>
                  <p className="text-xl font-bold tabular-nums mt-0.5" style={{color:k.c}}>{k.v}</p>
                </div>
              ))}
            </div>

            {/* Search + Add */}
            <div className="flex gap-2">
              <div className="relative flex-1"><MagnifyingGlass size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-[var(--p-text-muted)]"/><input value={search} onChange={e=>setSearch(e.target.value)} className="w-full h-8 bg-[var(--p-surface)] border border-[var(--p-border)] rounded-sm pl-8 pr-3 text-xs text-[var(--p-text)] placeholder-[var(--p-text-muted)] focus:border-[#185FA5] outline-none" placeholder="Search clients..." data-testid="search-clients"/></div>
              <button onClick={()=>setShowForm(!showForm)} className="h-8 px-3 rounded-sm bg-[#185FA5] text-white text-xs font-semibold flex items-center gap-1" data-testid="add-client-button"><Plus size={12}/> Client</button>
            </div>

            {/* Add client form */}
            {showForm && (
              <form onSubmit={addClient} className="bg-[var(--p-surface)] border border-[var(--p-border)] rounded-sm p-3 grid grid-cols-2 sm:grid-cols-4 gap-2" data-testid="client-form">
                <input type="text" value={form.name} onChange={e=>setForm(f=>({...f,name:e.target.value}))} placeholder="Client name" required className="h-8 bg-[var(--p-bg)] border border-[var(--p-border)] rounded-sm px-2 text-xs text-[var(--p-text)] focus:border-[#185FA5] outline-none" data-testid="client-name-input"/>
                <input type="text" value={form.business_type} onChange={e=>setForm(f=>({...f,business_type:e.target.value}))} placeholder="Business type" className="h-8 bg-[var(--p-bg)] border border-[var(--p-border)] rounded-sm px-2 text-xs text-[var(--p-text)] focus:border-[#185FA5] outline-none" data-testid="client-type-input"/>
                <select value={form.status} onChange={e=>setForm(f=>({...f,status:e.target.value}))} className="h-8 bg-[var(--p-bg)] border border-[var(--p-border)] rounded-sm px-2 text-xs text-[var(--p-text)] focus:border-[#185FA5] outline-none" data-testid="client-status-select"><option value="on_track">On track</option><option value="overdue">Overdue</option><option value="pending_docs">Pending docs</option></select>
                <button type="submit" className="h-8 rounded-sm bg-[var(--p-text)] text-[var(--p-bg)] text-xs font-semibold" data-testid="save-client-button">Save</button>
              </form>
            )}

            {/* Client list */}
            <div className="space-y-2" data-testid="client-list">
              {clients.length === 0 ? <p className="text-xs text-[var(--p-text-muted)] text-center py-6">No clients. Add your first client.</p> :
                clients.map(c => {
                  const st = STATUS_MAP[c.status] || STATUS_MAP.on_track;
                  return (
                    <div key={c.id} className="bg-[var(--p-surface)] border border-[var(--p-border)] rounded-sm p-3 flex items-center gap-3" data-testid={`client-${c.id}`}>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-0.5">
                          <p className="text-sm font-semibold text-[var(--p-text)] truncate">{c.name}</p>
                          <span className="inline-flex items-center gap-0.5 text-[9px] font-semibold px-1.5 py-0.5 rounded-sm" style={{color:st.color,background:`${st.color}15`}}>
                            <st.icon size={10} weight="fill"/> {st.label}
                          </span>
                        </div>
                        <p className="text-[10px] text-[var(--p-text-muted)]">{c.business_type}{c.next_deadline?` · Deadline: ${c.next_deadline}`:''}</p>
                      </div>
                      <button onClick={()=>delClient(c.id)} className="p-1 text-[var(--p-text-muted)] hover:text-[#EF4444] text-xs">Remove</button>
                    </div>
                  );
                })
              }
            </div>

            {/* Alerts */}
            <AlertsPanel persona="ca" />
          </>
        ) : null}
      </main>

      {/* AI Chat Drawer */}
      <AIChatDrawer isOpen={chatOpen} onClose={() => setChatOpen(false)} persona="ca" />

      <nav className="fixed bottom-0 left-0 right-0 z-40 bg-[var(--nav-bg)] backdrop-blur-xl border-t border-[var(--p-border)]" data-testid="bottom-nav">
        <div className="flex items-center justify-around h-12 max-w-5xl mx-auto">
          {[{icon:House,label:'Home',path:'/ca'},{icon:Users,label:'Clients',path:'/ca'},{icon:ListChecks,label:'Tasks',path:'/ca/tasks'},{icon:ChartBar,label:'Reports',path:'/ca'},{icon:Gear,label:'Settings',path:'/persona'}].map(i=>(
            <button key={i.label} onClick={()=>nav(i.path)} className={`flex flex-col items-center gap-0.5 w-14 py-1 ${window.location.pathname===i.path?'text-[#185FA5]':'text-[var(--p-text-muted)]'}`} data-testid={`nav-${i.label.toLowerCase()}`}>
              <i.icon size={18} weight={window.location.pathname===i.path?'fill':'regular'}/><span className="text-[9px] font-medium">{i.label}</span>
            </button>
          ))}
        </div>
      </nav>
    </div>
  );
};
