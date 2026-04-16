import React from 'react';
import { TrendUp, TrendDown, Wallet } from '@phosphor-icons/react';

export const SummaryCards = ({ summary }) => {
  const cards = [
    {
      title: 'Total Income',
      value: summary.total_income,
      icon: <TrendUp size={24} weight="duotone" className="text-[#059669]" />,
      color: 'text-[#059669]',
      testId: 'total-income-card',
    },
    {
      title: 'Total Expenses',
      value: summary.total_expenses,
      icon: <TrendDown size={24} weight="duotone" className="text-[#E11D48]" />,
      color: 'text-[#E11D48]',
      testId: 'total-expenses-card',
    },
    {
      title: 'Balance',
      value: summary.balance,
      icon: <Wallet size={24} weight="duotone" className="text-[#09090B]" />,
      color: summary.balance >= 0 ? 'text-[#09090B]' : 'text-[#E11D48]',
      testId: 'balance-card',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {cards.map((card) => (
        <div
          key={card.title}
          className="bg-white border border-[#E4E4E7] rounded-xl p-6 lg:p-8 transition-all hover:border-[#A1A1AA]"
          data-testid={card.testId}
        >
          <div className="flex items-start justify-between mb-4">
            <p className="text-sm uppercase tracking-[0.2em] font-semibold text-[#52525B] font-['Manrope']">
              {card.title}
            </p>
            {card.icon}
          </div>
          <p className={`text-4xl lg:text-5xl font-medium tracking-tight font-['JetBrains_Mono'] ${card.color}`}>
            ${card.value.toFixed(2)}
          </p>
        </div>
      ))}
    </div>
  );
};
