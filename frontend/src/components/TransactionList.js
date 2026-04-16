import React from 'react';
import { Trash } from '@phosphor-icons/react';
import axios from 'axios';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export const TransactionList = ({ transactions, onTransactionDeleted }) => {
  const handleDelete = async (transactionId) => {
    if (!window.confirm('Are you sure you want to delete this transaction?')) return;

    try {
      await axios.delete(`${API_URL}/api/transactions/${transactionId}`, { withCredentials: true });
      toast.success('Transaction deleted');
      onTransactionDeleted();
    } catch (error) {
      toast.error('Failed to delete transaction');
    }
  };

  if (transactions.length === 0) {
    return (
      <div className="bg-white border border-[#E4E4E7] rounded-xl p-8 text-center" data-testid="transactions-empty-state">
        <p className="text-[#52525B] font-['Manrope']">No transactions yet. Add your first transaction above!</p>
      </div>
    );
  }

  return (
    <div className="bg-white border border-[#E4E4E7] rounded-xl p-6 lg:p-8" data-testid="transactions-list">
      <h2 className="text-xl font-semibold tracking-tight text-[#09090B] font-['Outfit'] mb-6">
        Recent Transactions
      </h2>

      <div className="space-y-3">
        {transactions.map((transaction) => (
          <div
            key={transaction.id}
            className="flex items-center justify-between p-4 border border-[#E4E4E7] rounded-lg hover:border-[#A1A1AA] transition-all"
            data-testid={`transaction-item-${transaction.id}`}
          >
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-1">
                <span
                  className={`inline-block px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wider font-['Manrope'] ${
                    transaction.type === 'income'
                      ? 'bg-[#D1FAE5] text-[#065F46]'
                      : 'bg-[#FEE2E2] text-[#991B1B]'
                  }`}
                >
                  {transaction.type}
                </span>
                <span className="text-sm font-semibold text-[#09090B] font-['Manrope']">{transaction.category}</span>
              </div>
              {transaction.description && (
                <p className="text-sm text-[#52525B] font-['Manrope'] mt-1">{transaction.description}</p>
              )}
              <p className="text-xs text-[#A1A1AA] font-['Manrope'] mt-1">{transaction.date}</p>
            </div>

            <div className="flex items-center gap-4">
              <p
                className={`text-2xl font-medium tracking-tight font-['JetBrains_Mono'] ${
                  transaction.type === 'income' ? 'text-[#059669]' : 'text-[#E11D48]'
                }`}
              >
                {transaction.type === 'income' ? '+' : '-'}${transaction.amount.toFixed(2)}
              </p>
              <button
                onClick={() => handleDelete(transaction.id)}
                className="text-[#A1A1AA] hover:text-[#E11D48] transition-colors p-2"
                data-testid={`delete-transaction-${transaction.id}`}
              >
                <Trash size={20} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
