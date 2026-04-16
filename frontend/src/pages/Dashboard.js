import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { SummaryCards } from '../components/SummaryCards';
import { TransactionForm } from '../components/TransactionForm';
import { TransactionList } from '../components/TransactionList';
import { ChartsSection } from '../components/ChartsSection';
import { AIInsightsModal } from '../components/AIInsightsModal';
import { SignOut, Sparkle } from '@phosphor-icons/react';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export const Dashboard = () => {
  const { user, logout } = useAuth();
  const [summary, setSummary] = useState({ total_income: 0, total_expenses: 0, balance: 0, transaction_count: 0 });
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAIModal, setShowAIModal] = useState(false);
  const [aiAnalyzing, setAiAnalyzing] = useState(false);
  const [aiInsights, setAiInsights] = useState(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [summaryRes, transactionsRes] = await Promise.all([
        axios.get(`${API_URL}/api/dashboard/summary`, { withCredentials: true }),
        axios.get(`${API_URL}/api/transactions`, { withCredentials: true }),
      ]);
      setSummary(summaryRes.data);
      setTransactions(transactionsRes.data);
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async () => {
    if (transactions.length === 0) {
      alert('Please add some transactions first!');
      return;
    }

    setAiAnalyzing(true);
    setShowAIModal(true);
    try {
      const { data } = await axios.post(
        `${API_URL}/api/analyze`,
        {},
        { withCredentials: true }
      );
      setAiInsights(data);
    } catch (error) {
      console.error('AI analysis failed:', error);
      alert(error.response?.data?.detail || 'Failed to analyze finances');
      setShowAIModal(false);
    } finally {
      setAiAnalyzing(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#FDFDFD]" data-testid="dashboard-page">
      {/* Header */}
      <header className="sticky top-0 z-50 backdrop-blur-xl bg-white/80 border-b border-[#E4E4E7]">
        <div className="max-w-[1600px] mx-auto px-6 lg:px-10 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl lg:text-3xl font-bold tracking-tight text-[#09090B] font-['Outfit']">
              Finance Dashboard
            </h1>
            <p className="text-sm text-[#52525B] font-['Manrope'] mt-1">Welcome back, {user?.name || 'User'}</p>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={handleAnalyze}
              disabled={aiAnalyzing || transactions.length === 0}
              className="bg-[#1D4ED8] text-white rounded-lg px-6 py-3 font-semibold tracking-wide transition-all shadow-[0_0_20px_rgba(29,78,216,0.3)] hover:shadow-[0_0_30px_rgba(29,78,216,0.5)] hover:bg-[#1E3A8A] flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed font-['Manrope']"
              data-testid="analyze-finances-button"
            >
              <Sparkle size={20} weight="fill" />
              {aiAnalyzing ? 'Analyzing...' : 'Analyze My Finances'}
            </button>
            <button
              onClick={logout}
              className="bg-transparent text-[#09090B] border border-[#E4E4E7] rounded-lg px-4 py-3 font-medium transition-all hover:border-[#09090B] flex items-center gap-2 font-['Manrope']"
              data-testid="logout-button"
            >
              <SignOut size={20} />
              Sign Out
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-[1600px] mx-auto p-6 lg:p-10">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="inline-block h-12 w-12 animate-spin rounded-full border-4 border-solid border-[#09090B] border-r-transparent"></div>
              <p className="mt-4 text-[#52525B] font-['Manrope']">Loading your data...</p>
            </div>
          </div>
        ) : (
          <div className="space-y-8">
            {/* Summary Cards */}
            <SummaryCards summary={summary} />

            {/* Transaction Form */}
            <TransactionForm onTransactionAdded={fetchData} />

            {/* Charts Section */}
            <ChartsSection transactions={transactions} />

            {/* Transaction List */}
            <TransactionList transactions={transactions} onTransactionDeleted={fetchData} />
          </div>
        )}
      </main>

      {/* AI Insights Modal */}
      {showAIModal && (
        <AIInsightsModal
          isOpen={showAIModal}
          onClose={() => setShowAIModal(false)}
          insights={aiInsights}
          loading={aiAnalyzing}
        />
      )}
    </div>
  );
};
