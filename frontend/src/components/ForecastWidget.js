import React, { useState, useEffect } from 'react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useTheme } from '../context/ThemeContext';
import { formatINR } from '../utils/inr';
import axios from 'axios';
const API = process.env.REACT_APP_BACKEND_URL;

export const ForecastWidget = ({ persona }) => {
  const { theme } = useTheme();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { fetch_(); }, [persona]);
  const fetch_ = async () => {
    try { const { data: d } = await axios.get(`${API}/api/forecast/${persona}`, { withCredentials: true }); setData(d); }
    catch {} finally { setLoading(false); }
  };

  if (loading || !data) return null;
  const personaColor = persona === 'individual' ? '#1D9E75' : persona === 'shop_owner' ? '#EF9F27' : '#185FA5';

  if (persona === 'individual' && data.forecast?.length > 0) {
    return (
      <div className="bg-[var(--p-surface)] border border-[var(--p-border)] p-4" style={{ borderRadius: 'var(--p-radius)' }} data-testid="forecast-widget">
        <h3 className="text-xs font-semibold text-[var(--p-text)] uppercase tracking-wider mb-3">3-Month Forecast</h3>
        <div className="grid grid-cols-3 gap-3 mb-3">
          {data.forecast.map(f => (
            <div key={f.month} className="text-center">
              <p className="text-[9px] text-[var(--p-text-muted)]">{f.month}</p>
              <p className="text-sm font-bold tabular-nums" style={{ color: personaColor }}>{formatINR(f.projected_savings)}</p>
              <p className="text-[8px] text-[var(--p-text-muted)]">est. savings</p>
            </div>
          ))}
        </div>
        <div className="flex justify-between text-[10px] text-[var(--p-text-muted)]">
          <span>Avg income: {formatINR(data.avg_income)}/mo</span>
          <span>Avg expense: {formatINR(data.avg_expense)}/mo</span>
        </div>
      </div>
    );
  }

  if (persona === 'shop_owner' && data.series?.length > 0) {
    return (
      <div className="bg-[var(--p-surface)] border border-[var(--p-border)] p-4" style={{ borderRadius: 'var(--p-radius)' }} data-testid="forecast-widget">
        <h3 className="text-xs font-semibold text-[var(--p-text)] uppercase tracking-wider mb-1">Cash Flow Forecast</h3>
        <p className="text-[10px] text-[var(--p-text-muted)] mb-3">Daily avg: {formatINR(data.daily_avg_net)}/day</p>
        <div className="grid grid-cols-3 gap-2 mb-3">
          {[{ label: '30 days', val: data.forecast_30 }, { label: '60 days', val: data.forecast_60 }, { label: '90 days', val: data.forecast_90 }].map(f => (
            <div key={f.label} className="bg-[var(--p-bg)] rounded-md p-2 text-center">
              <p className="text-[9px] text-[var(--p-text-muted)]">{f.label}</p>
              <p className="text-sm font-bold tabular-nums" style={{ color: f.val >= 0 ? '#1D9E75' : '#EF4444' }}>{formatINR(f.val)}</p>
            </div>
          ))}
        </div>
        <ResponsiveContainer width="100%" height={100}>
          <AreaChart data={data.series.filter((_, i) => i % 5 === 0)}>
            <defs><linearGradient id="gForecast" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor={personaColor} stopOpacity={0.3} /><stop offset="100%" stopColor={personaColor} stopOpacity={0} /></linearGradient></defs>
            <Area type="monotone" dataKey="projected" stroke={personaColor} strokeWidth={1.5} fill="url(#gForecast)" dot={false} />
            <Tooltip contentStyle={{ background: theme === 'dark' ? '#1E293B' : '#FFF', border: '1px solid #E2E8F0', borderRadius: '6px', fontSize: '10px' }} formatter={v => [formatINR(v), 'Projected']} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    );
  }

  return null;
};
