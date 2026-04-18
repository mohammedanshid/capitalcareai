import React, { useState, useEffect } from 'react';
import { Bell, Warning, CheckCircle, Info, X } from '@phosphor-icons/react';
import axios from 'axios';
const API = process.env.REACT_APP_BACKEND_URL;

const SEVERITY_MAP = {
  warning: { icon: Warning, color: '#EF9F27', bg: '#FEF3C7', darkBg: 'rgba(239,159,39,0.1)' },
  info: { icon: Info, color: '#3B82F6', bg: '#EFF6FF', darkBg: 'rgba(59,130,246,0.1)' },
  success: { icon: CheckCircle, color: '#1D9E75', bg: '#ECFDF5', darkBg: 'rgba(29,158,117,0.1)' },
};

export const AlertsPanel = ({ persona }) => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dismissed, setDismissed] = useState(new Set());

  useEffect(() => { fetch_(); }, [persona]);
  const fetch_ = async () => {
    try { const { data } = await axios.get(`${API}/api/alerts/${persona}`, { withCredentials: true }); setAlerts(data); }
    catch {} finally { setLoading(false); }
  };

  const visible = alerts.filter((_, i) => !dismissed.has(i));
  if (loading || visible.length === 0) return null;

  return (
    <div className="space-y-2" data-testid="alerts-panel">
      <div className="flex items-center gap-2 mb-1">
        <Bell size={14} weight="fill" className="text-[var(--p-text-muted)]" />
        <p className="text-[10px] font-semibold uppercase tracking-wider text-[var(--p-text-muted)]">Smart Alerts</p>
      </div>
      {visible.map((a, i) => {
        const s = SEVERITY_MAP[a.severity] || SEVERITY_MAP.info;
        const Icon = s.icon;
        return (
          <div key={i} className="flex items-start gap-2.5 p-3 rounded-lg border border-[var(--p-border)]" style={{ background: `${s.color}08` }} data-testid={`alert-${a.type}`}>
            <Icon size={16} weight="fill" style={{ color: s.color }} className="flex-shrink-0 mt-0.5" />
            <p className="flex-1 text-xs text-[var(--p-text-secondary)] leading-relaxed">{a.message}</p>
            <button onClick={() => setDismissed(prev => new Set([...prev, alerts.indexOf(a)]))} className="p-0.5 text-[var(--p-text-muted)] hover:text-[var(--p-text)]"><X size={12} /></button>
          </div>
        );
      })}
    </div>
  );
};
