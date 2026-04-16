import React, { useMemo } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';

const PIE_COLORS = ['#09090B', '#52525B', '#A1A1AA', '#E4E4E7', '#F4F4F5'];

export const ChartsSection = ({ transactions }) => {
  const monthlyData = useMemo(() => {
    const monthMap = {};
    transactions.forEach((t) => {
      const month = t.date.substring(0, 7);
      if (!monthMap[month]) {
        monthMap[month] = { month, income: 0, expenses: 0 };
      }
      if (t.type === 'income') {
        monthMap[month].income += t.amount;
      } else {
        monthMap[month].expenses += t.amount;
      }
    });
    return Object.values(monthMap).sort((a, b) => a.month.localeCompare(b.month));
  }, [transactions]);

  const expenseData = useMemo(() => {
    const categoryMap = {};
    transactions.forEach((t) => {
      if (t.type === 'expense') {
        categoryMap[t.category] = (categoryMap[t.category] || 0) + t.amount;
      }
    });
    return Object.entries(categoryMap)
      .map(([name, value]) => ({ name, value }))
      .sort((a, b) => b.value - a.value);
  }, [transactions]);

  if (transactions.length === 0) {
    return null;
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      {/* Bar Chart */}
      <div className="lg:col-span-8 bg-white border border-[#E4E4E7] rounded-xl p-6 lg:p-8" data-testid="bar-chart-container">
        <h3 className="text-xl font-semibold tracking-tight text-[#09090B] font-['Outfit'] mb-6">
          Monthly Trends
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={monthlyData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#F4F4F5" />
            <XAxis dataKey="month" tick={{ fill: '#52525B', fontSize: 12, fontFamily: 'Manrope' }} />
            <YAxis tick={{ fill: '#52525B', fontSize: 12, fontFamily: 'Manrope' }} />
            <Tooltip
              contentStyle={{
                backgroundColor: '#FFFFFF',
                border: '1px solid #E4E4E7',
                borderRadius: '8px',
                fontFamily: 'Manrope',
              }}
            />
            <Legend wrapperStyle={{ fontFamily: 'Manrope', fontSize: '14px' }} />
            <Bar dataKey="income" fill="#09090B" name="Income" radius={[4, 4, 0, 0]} />
            <Bar dataKey="expenses" fill="#E4E4E7" name="Expenses" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Pie Chart */}
      <div className="lg:col-span-4 bg-white border border-[#E4E4E7] rounded-xl p-6 lg:p-8" data-testid="pie-chart-container">
        <h3 className="text-xl font-semibold tracking-tight text-[#09090B] font-['Outfit'] mb-6">
          Expense Breakdown
        </h3>
        {expenseData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={expenseData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {expenseData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: '#FFFFFF',
                  border: '1px solid #E4E4E7',
                  borderRadius: '8px',
                  fontFamily: 'Manrope',
                }}
                formatter={(value) => `$${value.toFixed(2)}`}
              />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-[300px] flex items-center justify-center">
            <p className="text-[#52525B] font-['Manrope']">No expense data yet</p>
          </div>
        )}
      </div>
    </div>
  );
};
