import React from 'react';
import { TrendUp, TrendDown, Wallet, CurrencyDollar } from '@phosphor-icons/react';
import { AreaChart, Area, ResponsiveContainer } from 'recharts';

const CARDS = [
  { key: 'income', label: 'Revenue', icon: TrendUp, sparkKey: 'sparkline_income', trendKey: 'trend_income', valueKey: 'total_income', color: '#10B981', gradientId: 'gradIncome' },
  { key: 'expenses', label: 'Expenses', icon: TrendDown, sparkKey: 'sparkline_expenses', trendKey: 'trend_expenses', valueKey: 'total_expenses', color: '#EF4444', gradientId: 'gradExpenses' },
  { key: 'profit', label: 'Profit', icon: Wallet, sparkKey: 'sparkline_profit', trendKey: 'trend_profit', valueKey: 'balance', color: '#3B82F6', gradientId: 'gradProfit' },
  { key: 'cashflow', label: 'Cash Flow', icon: CurrencyDollar, sparkKey: 'sparkline_cashflow', trendKey: 'trend_cashflow', valueKey: 'cash_flow', color: '#8B5CF6', gradientId: 'gradCashflow' },
];

const MiniSparkline = ({ data, color, gradientId }) => {
  if (!data || data.length < 2) return <div className="h-10" />;
  const chartData = data.map((v, i) => ({ v, i }));
  return (
    <ResponsiveContainer width="100%" height={40}>
      <AreaChart data={chartData} margin={{ top: 2, right: 0, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity={0.3} />
            <stop offset="100%" stopColor={color} stopOpacity={0} />
          </linearGradient>
        </defs>
        <Area type="monotone" dataKey="v" stroke={color} strokeWidth={1.5} fill={`url(#${gradientId})`} dot={false} isAnimationActive={false} />
      </AreaChart>
    </ResponsiveContainer>
  );
};

const TrendBadge = ({ value }) => {
  if (value === 0 || value === undefined) return null;
  const up = value > 0;
  return (
    <span className={`inline-flex items-center gap-0.5 text-[11px] font-semibold tabular-nums px-1.5 py-0.5 rounded-md ${up ? 'text-[#10B981] bg-[var(--income-bg)]' : 'text-[#EF4444] bg-[var(--expense-bg)]'}`}>
      {up ? '+' : ''}{value}%
    </span>
  );
};

export const KPICards = ({ summary }) => {
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
      {CARDS.map((card, i) => {
        const value = summary[card.valueKey] ?? 0;
        const trend = summary[card.trendKey] ?? 0;
        const sparkData = summary[card.sparkKey] ?? [];

        return (
          <div key={card.key}
            className={`animate-fade-up stagger-${i + 1} bg-[var(--surface-0)] border border-[var(--border-default)] rounded-xl p-4 sm:p-5 transition-all hover:shadow-[var(--shadow-md)]`}
            data-testid={`kpi-${card.key}`}>
            {/* Top row: label + trend */}
            <div className="flex items-center justify-between mb-1">
              <p className="text-[11px] sm:text-xs font-semibold uppercase tracking-wider text-[var(--text-tertiary)]">{card.label}</p>
              <TrendBadge value={trend} />
            </div>

            {/* Value */}
            <p className="text-xl sm:text-2xl lg:text-3xl font-bold tracking-tight tabular-nums" style={{ color: card.color }}>
              ${Math.abs(value).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
            </p>

            {/* Sparkline */}
            <div className="mt-2">
              <MiniSparkline data={sparkData} color={card.color} gradientId={card.gradientId} />
            </div>
          </div>
        );
      })}
    </div>
  );
};
