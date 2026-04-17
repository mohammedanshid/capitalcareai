import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { useTheme } from '../context/ThemeContext';

export const PrimaryLineChart = ({ monthlySeries }) => {
  const { theme } = useTheme();
  if (!monthlySeries || monthlySeries.length === 0) return null;

  const axisColor = theme === 'dark' ? '#475569' : '#CBD5E1';
  const gridColor = theme === 'dark' ? '#1E293B' : '#F1F5F9';
  const tooltipBg = theme === 'dark' ? '#1E293B' : '#FFFFFF';
  const tooltipBorder = theme === 'dark' ? '#334155' : '#E2E8F0';
  const textColor = theme === 'dark' ? '#F8FAFC' : '#0F172A';

  return (
    <div className="bg-[var(--surface-0)] border border-[var(--border-default)] rounded-xl p-4 sm:p-5" data-testid="primary-line-chart">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-[var(--text-primary)]">Revenue vs Expenses</h3>
        <div className="flex items-center gap-4 text-[11px] text-[var(--text-tertiary)]">
          <span className="flex items-center gap-1.5"><span className="w-2.5 h-[2px] rounded bg-[#10B981]" />Income</span>
          <span className="flex items-center gap-1.5"><span className="w-2.5 h-[2px] rounded bg-[#EF4444]" />Expenses</span>
          <span className="flex items-center gap-1.5"><span className="w-2.5 h-[2px] rounded bg-[#3B82F6]" />Profit</span>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={monthlySeries} margin={{ top: 5, right: 5, left: -10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={gridColor} vertical={false} />
          <XAxis dataKey="month" tick={{ fill: axisColor, fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: axisColor, fontSize: 11 }} axisLine={false} tickLine={false} />
          <Tooltip
            contentStyle={{ backgroundColor: tooltipBg, border: `1px solid ${tooltipBorder}`, borderRadius: '10px', fontSize: '12px', color: textColor, boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
            formatter={(value, name) => [`$${value.toFixed(2)}`, name.charAt(0).toUpperCase() + name.slice(1)]}
          />
          <Line type="monotone" dataKey="income" stroke="#10B981" strokeWidth={2} dot={{ r: 3, fill: '#10B981' }} activeDot={{ r: 5 }} />
          <Line type="monotone" dataKey="expenses" stroke="#EF4444" strokeWidth={2} dot={{ r: 3, fill: '#EF4444' }} activeDot={{ r: 5 }} />
          <Line type="monotone" dataKey="profit" stroke="#3B82F6" strokeWidth={2} dot={{ r: 3, fill: '#3B82F6' }} activeDot={{ r: 5 }} strokeDasharray="5 5" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};
